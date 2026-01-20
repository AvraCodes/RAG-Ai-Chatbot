"""
Precompute Embeddings Script
=============================
Run this ONCE to compute embeddings for all chunks in the database.
This ensures embeddings are NEVER computed at query time.

Usage:
    python precompute_embeddings.py
"""

import os
import sqlite3
import json
import asyncio
import aiohttp
from tqdm import tqdm
from dotenv import load_dotenv
import time

load_dotenv()

DB_PATH = "knowledge_base.db"
API_KEY = os.getenv("API_KEY")
BATCH_SIZE = 10  # Process in batches to avoid rate limits
RATE_LIMIT_DELAY = 1.0  # Delay between batches (seconds)


async def get_embedding(text, session, max_retries=3):
    """Get embedding from Gemini API with retry logic"""
    if not API_KEY:
        raise ValueError("API_KEY environment variable not set")
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": API_KEY
    }
    payload = {
        "model": "models/text-embedding-004",
        "content": {
            "parts": [{"text": text[:10000]}]  # Limit text length
        }
    }
    
    for attempt in range(max_retries):
        try:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["embedding"]["values"]
                elif response.status == 429:
                    wait_time = (attempt + 1) * 5
                    print(f"Rate limit hit, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    error_text = await response.text()
                    print(f"Error {response.status}: {error_text}")
                    return None
        except Exception as e:
            print(f"Exception on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
            else:
                return None
    return None


async def precompute_discourse_embeddings():
    """Precompute embeddings for discourse chunks"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Find chunks without embeddings
    cursor.execute("""
        SELECT id, content 
        FROM discourse_chunks 
        WHERE embedding IS NULL OR embedding = ''
    """)
    chunks_to_process = cursor.fetchall()
    
    if not chunks_to_process:
        print("✅ All discourse chunks already have embeddings!")
        conn.close()
        return
    
    print(f"📊 Found {len(chunks_to_process)} discourse chunks without embeddings")
    
    async with aiohttp.ClientSession() as session:
        for i in tqdm(range(0, len(chunks_to_process), BATCH_SIZE), desc="Processing discourse chunks"):
            batch = chunks_to_process[i:i + BATCH_SIZE]
            
            for chunk_id, content in batch:
                if not content or not content.strip():
                    continue
                
                embedding = await get_embedding(content, session)
                
                if embedding:
                    cursor.execute(
                        "UPDATE discourse_chunks SET embedding = ? WHERE id = ?",
                        (json.dumps(embedding), chunk_id)
                    )
                    conn.commit()
            
            # Rate limiting
            if i + BATCH_SIZE < len(chunks_to_process):
                await asyncio.sleep(RATE_LIMIT_DELAY)
    
    conn.close()
    print("✅ Discourse embeddings precomputed!")


async def precompute_markdown_embeddings():
    """Precompute embeddings for markdown chunks"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Find chunks without embeddings
    cursor.execute("""
        SELECT id, content 
        FROM markdown_chunks 
        WHERE embedding IS NULL OR embedding = ''
    """)
    chunks_to_process = cursor.fetchall()
    
    if not chunks_to_process:
        print("✅ All markdown chunks already have embeddings!")
        conn.close()
        return
    
    print(f"📊 Found {len(chunks_to_process)} markdown chunks without embeddings")
    
    async with aiohttp.ClientSession() as session:
        for i in tqdm(range(0, len(chunks_to_process), BATCH_SIZE), desc="Processing markdown chunks"):
            batch = chunks_to_process[i:i + BATCH_SIZE]
            
            for chunk_id, content in batch:
                if not content or not content.strip():
                    continue
                
                embedding = await get_embedding(content, session)
                
                if embedding:
                    cursor.execute(
                        "UPDATE markdown_chunks SET embedding = ? WHERE id = ?",
                        (json.dumps(embedding), chunk_id)
                    )
                    conn.commit()
            
            # Rate limiting
            if i + BATCH_SIZE < len(chunks_to_process):
                await asyncio.sleep(RATE_LIMIT_DELAY)
    
    conn.close()
    print("✅ Markdown embeddings precomputed!")


async def verify_embeddings():
    """Verify all chunks have embeddings"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM discourse_chunks")
    total_discourse = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM discourse_chunks WHERE embedding IS NOT NULL AND embedding != ''")
    discourse_with_emb = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM markdown_chunks")
    total_markdown = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM markdown_chunks WHERE embedding IS NOT NULL AND embedding != ''")
    markdown_with_emb = cursor.fetchone()[0]
    
    conn.close()
    
    print("\n" + "="*50)
    print("📊 EMBEDDING STATISTICS")
    print("="*50)
    print(f"Discourse chunks: {discourse_with_emb}/{total_discourse} ({100*discourse_with_emb/total_discourse if total_discourse > 0 else 0:.1f}%)")
    print(f"Markdown chunks:  {markdown_with_emb}/{total_markdown} ({100*markdown_with_emb/total_markdown if total_markdown > 0 else 0:.1f}%)")
    print("="*50)


async def main():
    """Main execution"""
    if not API_KEY:
        print("❌ ERROR: API_KEY environment variable not set")
        return
    
    print("🚀 Starting embedding precomputation...")
    print(f"Database: {DB_PATH}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Rate limit delay: {RATE_LIMIT_DELAY}s\n")
    
    start_time = time.time()
    
    await precompute_discourse_embeddings()
    await precompute_markdown_embeddings()
    await verify_embeddings()
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed:.1f} seconds")
    print("\n✨ All done! Your database is ready for fast queries.")


if __name__ == "__main__":
    asyncio.run(main())
