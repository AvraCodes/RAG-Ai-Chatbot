"""
Recompute embeddings from backup database
Uses Gemini embeddings (768-dim) instead of OpenAI (1536-dim)
"""

import sqlite3
import json
import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
API_KEY = os.getenv("API_KEY")
BACKUP_DB = "knowledge_base_backup.db"
NEW_DB = "knowledge_base.db"
BATCH_SIZE = 5
RATE_LIMIT_DELAY = 1.5


async def get_embedding(text, session, max_retries=3):
    """Get embedding from Gemini API"""
    url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": API_KEY
    }
    payload = {
        "model": "models/text-embedding-004",
        "content": {
            "parts": [{"text": text[:10000]}]
        }
    }
    
    for attempt in range(max_retries):
        try:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["embedding"]["values"]
                elif response.status == 429:
                    wait_time = (attempt + 1) * 10
                    print(f"⚠️  Rate limit hit, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    error_text = await response.text()
                    print(f"❌ Error {response.status}: {error_text[:100]}")
                    return None
        except Exception as e:
            print(f"⚠️  Exception on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3)
            else:
                return None
    return None


async def recompute_embeddings():
    """Recompute all embeddings using Gemini"""
    
    # Copy backup structure to new database
    backup_conn = sqlite3.connect(BACKUP_DB)
    new_conn = sqlite3.connect(NEW_DB)
    
    # Create tables in new DB
    new_cursor = new_conn.cursor()
    new_cursor.execute('''
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
    
    new_cursor.execute('''
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
    new_conn.commit()
    
    # Process discourse chunks
    print("📊 Processing discourse chunks...")
    backup_cursor = backup_conn.cursor()
    backup_cursor.execute("""
        SELECT post_id, topic_id, topic_title, post_number, author, created_at, 
               likes, chunk_index, content, url 
        FROM discourse_chunks
    """)
    discourse_rows = backup_cursor.fetchall()
    
    print(f"Found {len(discourse_rows)} discourse chunks to process")
    
    async with aiohttp.ClientSession() as session:
        for i in tqdm(range(0, len(discourse_rows), BATCH_SIZE), desc="Discourse"):
            batch = discourse_rows[i:i + BATCH_SIZE]
            
            for row in batch:
                post_id, topic_id, topic_title, post_number, author, created_at, likes, chunk_index, content, url = row
                
                if not content or not content.strip():
                    continue
                
                embedding = await get_embedding(content, session)
                
                if embedding:
                    new_cursor.execute("""
                        INSERT INTO discourse_chunks 
                        (post_id, topic_id, topic_title, post_number, author, created_at, likes, chunk_index, content, url, embedding)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (post_id, topic_id, topic_title, post_number, author, created_at, likes, chunk_index, content, url, json.dumps(embedding)))
                    new_conn.commit()
            
            if i + BATCH_SIZE < len(discourse_rows):
                await asyncio.sleep(RATE_LIMIT_DELAY)
    
    # Process markdown chunks
    print("\n📝 Processing markdown chunks...")
    backup_cursor.execute("""
        SELECT doc_title, original_url, downloaded_at, chunk_index, content
        FROM markdown_chunks
    """)
    markdown_rows = backup_cursor.fetchall()
    
    print(f"Found {len(markdown_rows)} markdown chunks to process")
    
    async with aiohttp.ClientSession() as session:
        for i in tqdm(range(0, len(markdown_rows), BATCH_SIZE), desc="Markdown"):
            batch = markdown_rows[i:i + BATCH_SIZE]
            
            for row in batch:
                doc_title, original_url, downloaded_at, chunk_index, content = row
                
                if not content or not content.strip():
                    continue
                
                embedding = await get_embedding(content, session)
                
                if embedding:
                    new_cursor.execute("""
                        INSERT INTO markdown_chunks 
                        (doc_title, original_url, downloaded_at, chunk_index, content, embedding)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (doc_title, original_url, downloaded_at, chunk_index, content, json.dumps(embedding)))
                    new_conn.commit()
            
            if i + BATCH_SIZE < len(markdown_rows):
                await asyncio.sleep(RATE_LIMIT_DELAY)
    
    backup_conn.close()
    new_conn.close()
    
    print("\n✅ Done! Embeddings recomputed with Gemini.")
    
    # Verify
    verify_conn = sqlite3.connect(NEW_DB)
    verify_cursor = verify_conn.cursor()
    verify_cursor.execute("SELECT COUNT(*) FROM discourse_chunks WHERE embedding IS NOT NULL")
    d = verify_cursor.fetchone()[0]
    verify_cursor.execute("SELECT COUNT(*) FROM markdown_chunks WHERE embedding IS NOT NULL")
    m = verify_cursor.fetchone()[0]
    verify_conn.close()
    
    print(f"✅ {d} discourse chunks with embeddings")
    print(f"✅ {m} markdown chunks with embeddings")


if __name__ == "__main__":
    if not API_KEY:
        print("❌ ERROR: API_KEY environment variable not set")
    else:
        print("🚀 Recomputing embeddings with Gemini (768-dim)...")
        print("⏱️  This will take ~15-30 minutes depending on rate limits\n")
        asyncio.run(recompute_embeddings())
