# app.py
import os
import glob
import json
import sqlite3
import numpy as np
import re
import aiohttp
import asyncio
import logging
import base64
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
import traceback
import uvicorn
from functools import lru_cache
import aiosqlite

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants - OPTIMIZED
DB_PATH = "knowledge_base.db"
SIMILARITY_THRESHOLD = 0.4  # ✅ Balanced for recall (lowered from 0.65)
MAX_RESULTS = 8  # ✅ Reduced from 10
MAX_CONTEXT_CHUNKS = 3  # ✅ Reduced from 4
QUERY_LIMIT = 500  # ✅ Limit DB scan to top 500 chunks
API_KEY = os.getenv("API_KEY")

# ✅ Query embedding cache (in-memory)
query_cache = {}

# Models
class QueryRequest(BaseModel):
    question: str
    image: Optional[str] = None  # Base64 encoded image

class LinkInfo(BaseModel):
    url: str
    text: str

class QueryResponse(BaseModel):
    answer: str
    links: List[LinkInfo]

# Initialize FastAPI app
app = FastAPI(title="TDS Virtual TA", description="Virtual Teaching Assistant for TDS course")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="templates")

# Verify API key is set
if not API_KEY:
    logger.error("API_KEY environment variable is not set. The application will not function correctly.")

# Create database tables if they don't exist
async def initialize_database():
    """Initialize database with proper async/await"""
    if not os.path.exists(DB_PATH):
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute('''
            CREATE TABLE IF NOT EXISTS discourse_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                topic_id INTEGER,
                topic_title TEXT,
                post_number INTEGER,
                author TEXT,
                created_at TEXT,
                likes INTEGER,
                chunk_index INTEGER,
                content TEXT,
                url TEXT,
                embedding BLOB
            )
            ''')
            
            await conn.execute('''
            CREATE TABLE IF NOT EXISTS markdown_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_title TEXT,
                original_url TEXT,
                downloaded_at TEXT,
                chunk_index INTEGER,
                content TEXT,
                embedding BLOB
            )
            ''')
            await conn.commit()

# Vector similarity calculation
def cosine_similarity(vec1, vec2):
    try:
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # Check dimension compatibility
        if vec1.shape != vec2.shape:
            logger.warning(f"Dimension mismatch: {vec1.shape} vs {vec2.shape} - skipping")
            return 0.0
        
        if np.all(vec1 == 0) or np.all(vec2 == 0):
            return 0.0
            
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
            
        return float(dot_product / (norm_vec1 * norm_vec2))
    except Exception as e:
        logger.error(f"Error in cosine_similarity: {e}")
        return 0.0

# ✅ Cached query embedding to avoid recomputing identical queries
async def get_query_embedding_cached(text):
    """Get embedding with simple in-memory cache"""
    cache_key = text.strip().lower()[:200]  # Use first 200 chars as key
    
    if cache_key in query_cache:
        logger.info("✅ Cache hit for query embedding")
        return query_cache[cache_key]
    
    embedding = await get_embedding(text)
    query_cache[cache_key] = embedding
    
    # Keep cache size reasonable (max 100 queries)
    if len(query_cache) > 100:
        # Remove oldest entry
        query_cache.pop(next(iter(query_cache)))
    
    return embedding

# Function to get embedding using Gemini
async def get_embedding(text, max_retries=3):
    if not API_KEY:
        error_msg = "API_KEY environment variable not set"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    
    retries = 0
    while retries < max_retries:
        try:
            logger.info(f"Getting embedding for text (length: {len(text)})")
            
            # Use Gemini embedding API
            url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": API_KEY
            }
            payload = {
                "model": "models/text-embedding-004",
                "content": {
                    "parts": [{"text": text}]
                }
            }
            
            logger.info("Sending request to Gemini embedding API")
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("Successfully received embedding")
                        return result["embedding"]["values"]
                    elif response.status == 429:
                        error_text = await response.text()
                        logger.warning(f"Rate limit reached, retrying after delay (retry {retries+1}): {error_text}")
                        await asyncio.sleep(5 * (retries + 1))
                        retries += 1
                    else:
                        error_text = await response.text()
                        error_msg = f"Error getting embedding (status {response.status}): {error_text}"
                        logger.error(error_msg)
                        raise HTTPException(status_code=response.status, detail=error_msg)
        except Exception as e:
            error_msg = f"Exception getting embedding (attempt {retries+1}/{max_retries}): {e}"
            logger.error(error_msg)
            retries += 1
            if retries >= max_retries:
                raise HTTPException(status_code=500, detail=error_msg)
            await asyncio.sleep(3 * retries)

# ✅ OPTIMIZED: Function to find similar content - NO runtime embedding computation
async def find_similar_content(query_embedding, conn):
    """Find similar content using ONLY precomputed embeddings"""
    try:
        logger.info("Finding similar content in database")
        results = []
        
        # ✅ Search discourse chunks - ONLY those WITH embeddings
        logger.info("Querying discourse_chunks table")
        async with conn.execute("""
        SELECT id, post_id, topic_id, topic_title, post_number, author, created_at, 
               likes, chunk_index, content, url, embedding 
        FROM discourse_chunks
        WHERE embedding IS NOT NULL AND embedding != ''
        LIMIT ?
        """, (QUERY_LIMIT,)) as cursor:
            discourse_chunks = await cursor.fetchall()
        
        logger.info(f"Processing {len(discourse_chunks)} discourse chunks")
        
        for chunk in discourse_chunks:
            try:
                raw_emb = chunk[11]
                # Parse embedding (stored as JSON)
                try:
                    embedding = json.loads(raw_emb)
                except Exception:
                    embedding = json.loads(raw_emb.decode() if isinstance(raw_emb, (bytes, bytearray)) else str(raw_emb))

                similarity = cosine_similarity(query_embedding, embedding)
                if similarity >= SIMILARITY_THRESHOLD:
                    url = chunk[10] or ""
                    if url and not url.startswith("http"):
                        url = f"https://discourse.onlinedegree.iitm.ac.in/t/{url}"
                    results.append({
                        "source": "discourse",
                        "id": chunk[0],
                        "content": chunk[9],
                        "url": url,
                        "similarity": float(similarity)
                    })
            except Exception as e:
                logger.error(f"Error processing discourse chunk {chunk[0] if chunk else 'unknown'}: {e}")

        # ✅ Search markdown chunks - ONLY those WITH embeddings
        logger.info("Querying markdown_chunks table")
        async with conn.execute("""
        SELECT id, doc_title, original_url, downloaded_at, chunk_index, content, embedding 
        FROM markdown_chunks
        WHERE embedding IS NOT NULL AND embedding != ''
        LIMIT ?
        """, (QUERY_LIMIT,)) as cursor:
            markdown_chunks = await cursor.fetchall()
        
        logger.info(f"Processing {len(markdown_chunks)} markdown chunks")

        for chunk in markdown_chunks:
            try:
                raw_emb = chunk[6]
                try:
                    embedding = json.loads(raw_emb)
                except Exception:
                    embedding = json.loads(raw_emb.decode() if isinstance(raw_emb, (bytes, bytearray)) else str(raw_emb))

                similarity = cosine_similarity(query_embedding, embedding)
                if similarity >= SIMILARITY_THRESHOLD:
                    url = chunk[2] or "https://tds.s-anand.net/"
                    results.append({
                        "source": "markdown",
                        "id": chunk[0],
                        "content": chunk[5],
                        "url": url,
                        "similarity": float(similarity)
                    })
            except Exception as e:
                logger.error(f"Error processing markdown chunk {chunk[0] if chunk else 'unknown'}: {e}")

        # Sort and return top results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        logger.info(f"Found {len(results)} relevant results above threshold {SIMILARITY_THRESHOLD}")
        
        # Log top results for debugging
        if results:
            logger.info(f"Top result similarity: {results[0]['similarity']:.3f}")
            logger.info(f"Top result preview: {results[0]['content'][:100]}...")
        else:
            logger.warning(f"No results found above threshold {SIMILARITY_THRESHOLD}")
            logger.info(f"Total chunks scanned - Discourse: {len(discourse_chunks)}, Markdown: {len(markdown_chunks)}")
        
        return results[:MAX_RESULTS]

    except Exception as e:
        error_msg = f"Error in find_similar_content: {e}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise

# ✅ NEW: Fallback to LLM when no database results
async def generate_answer_without_context(question, max_retries=2):
    """Generate answer using LLM without RAG context"""
    if not API_KEY:
        error_msg = "API_KEY environment variable not set"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    
    retries = 0
    while retries < max_retries:
        try:
            logger.info(f"Generating LLM-only answer for: '{question[:50]}...'")
            
            prompt = f"""You are a helpful Teaching Assistant for the Tools in Data Science course at IIT Madras.
            Answer the following question based on your general knowledge about data science, Python, and related tools.
            If you're not confident about the answer, say so.
            
            Question: {question}
            
            Please provide a helpful and accurate answer:"""
            
            logger.info("Sending request to Gemini 2.5 Flash API (no context)")
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": API_KEY
            }
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1024
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("Successfully received LLM-only answer")
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                    elif response.status == 429:
                        error_text = await response.text()
                        logger.warning(f"Rate limit reached, retrying (retry {retries+1}): {error_text}")
                        await asyncio.sleep(3 * (retries + 1))
                        retries += 1
                    else:
                        error_text = await response.text()
                        error_msg = f"Error generating answer (status {response.status}): {error_text}"
                        logger.error(error_msg)
                        raise HTTPException(status_code=response.status, detail=error_msg)
        except Exception as e:
            error_msg = f"Exception generating LLM answer: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            retries += 1
            if retries >= max_retries:
                raise HTTPException(status_code=500, detail=error_msg)
            await asyncio.sleep(2)

# Function to generate answer using Gemini 2.5 Flash
async def generate_answer(question, relevant_results, max_retries=2):
    if not API_KEY:
        error_msg = "API_KEY environment variable not set"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    
    retries = 0
    while retries < max_retries:    
        try:
            logger.info(f"Generating answer for question: '{question[:50]}...'")
            context = ""
            for result in relevant_results:
                source_type = "Discourse post" if result["source"] == "discourse" else "Documentation"
                context += f"\n\n{source_type} (URL: {result['url']}):\n{result['content'][:3000]}"
            
            prompt = f"""You are a helpful Teaching Assistant for the Tools in Data Science course at IIT Madras. 
            Answer the following question using the provided context from course materials. Use the context as your primary source, but you can supplement with your general knowledge if needed to provide a complete answer.
            
            Context:
            {context}
            
            Question: {question}
            
            Please provide a clear, comprehensive answer. If the context is incomplete, use your knowledge to fill in gaps while noting what comes from the course materials.
            
            Answer:"""
            
            logger.info("Sending request to Gemini 2.5 Flash API")
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": API_KEY
            }
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.5,
                    "maxOutputTokens": 2048
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("Successfully received answer from Gemini")
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                    elif response.status == 429:
                        error_text = await response.text()
                        logger.warning(f"Rate limit reached, retrying after delay (retry {retries+1}): {error_text}")
                        await asyncio.sleep(3 * (retries + 1))
                        retries += 1
                    else:
                        error_text = await response.text()
                        error_msg = f"Error generating answer (status {response.status}): {error_text}"
                        logger.error(error_msg)
                        raise HTTPException(status_code=response.status, detail=error_msg)
        except Exception as e:
            error_msg = f"Exception generating answer: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            retries += 1
            if retries >= max_retries:
                raise HTTPException(status_code=500, detail=error_msg)
            await asyncio.sleep(2)

# Function to process multimodal queries (with image)
async def process_multimodal_query(question, image_base64):
    if not API_KEY:
        error_msg = "API_KEY environment variable not set"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
        
    try:
        logger.info(f"Processing query: '{question[:50]}...', image provided: {image_base64 is not None}")
        
        if not image_base64:
            logger.info("No image provided, processing as text-only query")
            return await get_embedding(question)
        
        logger.info("Processing multimodal query with image")
        
        # Use Gemini 2.5 Flash for vision analysis
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY
        }
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": f"Analyze this image and describe what you see in relation to this question: {question}"},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "maxOutputTokens": 500
            }
        }
        
        logger.info("Sending request to Gemini Vision API")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    image_description = result["candidates"][0]["content"]["parts"][0]["text"]
                    logger.info(f"Received image description: '{image_description[:50]}...'")
                    
                    # Combine the original question with the image description
                    combined_query = f"{question}\nImage context: {image_description}"
                    
                    # Get embedding for the combined query (cached)
                    return await get_query_embedding_cached(combined_query)
                else:
                    error_text = await response.text()
                    logger.error(f"Error processing image (status {response.status}): {error_text}")
                    # Fall back to text-only query
                    logger.info("Falling back to text-only query")
                    return await get_query_embedding_cached(question)
    except Exception as e:
        logger.error(f"Exception processing multimodal query: {e}")
        logger.error(traceback.format_exc())
        # Fall back to text-only query
        logger.info("Falling back to text-only query due to exception")
        return await get_query_embedding_cached(question)

# Main API endpoint
@app.post("/api")
async def query_knowledge_base(request: QueryRequest):
    logger.info(f"Received query request: question='{request.question[:50]}...', image_provided={bool(request.image)}")
    
    if not API_KEY:
        logger.error("API_KEY environment variable is not set.")
        raise HTTPException(status_code=500, detail="API_KEY environment variable is not set.")
    
    try:
        # Process the query (with or without image) - uses cache
        query_embedding = await process_multimodal_query(request.question, request.image)
        
        # ✅ Search for similar content using async SQLite
        async with aiosqlite.connect(DB_PATH) as conn:
            results = await find_similar_content(query_embedding, conn)
        
        # ✅ Fallback to LLM if no database results
        if not results:
            logger.info("No relevant results found in database - using LLM fallback")
            try:
                answer = await generate_answer_without_context(request.question)
                if answer:
                    return {
                        "answer": answer + "\n\n*Note: This answer is generated without specific course context as no matching information was found in the knowledge base.*",
                        "links": []
                    }
            except HTTPException as e:
                if e.status_code == 429 or "quota" in str(e.detail).lower():
                    logger.warning("Rate limit hit on LLM fallback")
                    return {
                        "answer": "I couldn't find specific information in the knowledge base, and the AI service is temporarily at capacity. Please try again in a few moments or rephrase your question.",
                        "links": []
                    }
                logger.error(f"LLM fallback error: {e}")
            
            return {
                "answer": "I couldn't find any relevant information in my knowledge base. Please try rephrasing your question or ask something more specific about the TDS course.",
                "links": []
            }
        
        # Generate answer using the most relevant chunks
        logger.info(f"Found {len(results)} results, using top {min(len(results), MAX_CONTEXT_CHUNKS)} for context")
        
        # Create links from the results
        links = []
        for chunk in results[:MAX_CONTEXT_CHUNKS]:
            if chunk.get("url"):
                links.append({
                    "url": chunk["url"], 
                    "text": chunk["content"][:100] + "..." if len(chunk["content"]) > 100 else chunk["content"]
                })
        
        # Try to generate answer, fallback to content summary if it fails
        try:
            answer = await generate_answer(request.question, results[:MAX_CONTEXT_CHUNKS])
            if answer:
                logger.info(f"Returning answer with {len(links)} links")
                return {"answer": answer, "links": links}
        except Exception as e:
            logger.warning(f"Answer generation failed: {e}")
        
        # Fallback: Return content summary from most relevant chunks
        logger.info("Using content summary fallback")
        content_summary = "Based on the course materials, here's what I found:\n\n"
        for i, chunk in enumerate(results[:MAX_CONTEXT_CHUNKS], 1):
            content_summary += f"{i}. {chunk['content'][:300]}...\n\n"
        content_summary += "\n*Note: AI answer generation is currently unavailable. The above is direct content from the knowledge base.*"
        
        logger.info(f"Returning content summary with {len(links)} links")
        return {"answer": content_summary, "links": links}
        
    except Exception as e:
        logger.error(f"Exception in query_knowledge_base: {e}")
        logger.error(traceback.format_exc())
        return {
            "answer": "Sorry, I encountered an error while processing your request. Please try again.", 
            "links": []
        }

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.execute("SELECT COUNT(*) FROM discourse_chunks") as cursor:
                discourse_count = (await cursor.fetchone())[0]
            
            async with conn.execute("SELECT COUNT(*) FROM markdown_chunks") as cursor:
                markdown_count = (await cursor.fetchone())[0]
            
            async with conn.execute("SELECT COUNT(*) FROM discourse_chunks WHERE embedding IS NOT NULL AND embedding != ''") as cursor:
                discourse_embeddings = (await cursor.fetchone())[0]
            
            async with conn.execute("SELECT COUNT(*) FROM markdown_chunks WHERE embedding IS NOT NULL AND embedding != ''") as cursor:
                markdown_embeddings = (await cursor.fetchone())[0]
        
        return {
            "status": "healthy", 
            "database": "connected", 
            "api_key_set": bool(API_KEY),
            "discourse_chunks": discourse_count,
            "markdown_chunks": markdown_count,
            "discourse_embeddings": discourse_embeddings,
            "markdown_embeddings": markdown_embeddings
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e), "api_key_set": bool(API_KEY)}
        )

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await initialize_database()
    logger.info("Database initialized")

# Root endpoint to serve the web interface
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)