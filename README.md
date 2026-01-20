# TDS AI Chatbot - RAG-Based Course Assistant

A Retrieval-Augmented Generation (RAG) chatbot designed to help students with questions about the Tools in Data Science (TDS) course at IIT Madras. The chatbot uses semantic search over course materials and Discourse posts to provide accurate, context-aware answers.

![TDS AI Chatbot Landing Page](docs/screenshot-landing.png)
*Landing page with example questions*

![TDS AI Chatbot Response](docs/screenshot-response.png)
*Detailed response with source attribution*

## 🚀 Features

- **Semantic Search**: Vector embeddings enable intelligent search over course materials and discussion posts
- **Source Attribution**: Every answer includes links to the original course materials
- **Context-Aware Responses**: Combines retrieved information with AI to provide comprehensive answers
- **Multimodal Support**: Can process both text and image inputs
- **Fast & Efficient**: Optimized with query caching, async operations, and limited database scans
- **Modern UI**: Clean, responsive interface built with Next.js and shadcn/ui components

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework with async support
- **Google Gemini 2.5 Flash**: AI model for embeddings (768-dim) and text generation
- **SQLite + aiosqlite**: Lightweight async database for storing embeddings
- **NumPy**: Efficient vector similarity computations (cosine similarity)
- **aiohttp**: Async HTTP client for API requests

### Frontend
- **Next.js 16**: React framework with Turbopack for fast development
- **React 19**: Latest React with modern features
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: High-quality React components built on Radix UI
- **Radix UI**: Accessible, unstyled UI components

### Data Sources
- **Discourse Forum Posts**: Student discussions and Q&A
- **Course Documentation**: Markdown files from the course website

## 🏗️ How It Works

### Architecture

```
┌─────────────┐
│   User Query│
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│           Frontend (Next.js)                │
│  - Input handling                           │
│  - Response rendering                       │
│  - Source link display                      │
└──────────────────┬──────────────────────────┘
                   │ HTTP POST /api
                   ▼
┌─────────────────────────────────────────────┐
│         Backend (FastAPI)                   │
│                                             │
│  1. Generate Query Embedding                │
│     └─> Gemini text-embedding-004 (768-dim)│
│                                             │
│  2. Vector Similarity Search                │
│     └─> SQLite with NumPy cosine similarity │
│     └─> Retrieve top 8 chunks (threshold>0.4)│
│                                             │
│  3. Generate Answer                         │
│     └─> Gemini 2.5 Flash                   │
│     └─> Context: Top 3 chunks (3000 chars) │
│                                             │
│  4. Return Response                         │
│     └─> Answer + Source Links              │
└─────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│         Database (SQLite)                   │
│  - discourse_chunks: Forum posts            │
│  - markdown_chunks: Course docs             │
│  - Each with 768-dim embeddings             │
└─────────────────────────────────────────────┘
```

### RAG Pipeline

1. **Query Processing**: User question is converted to a 768-dimensional embedding vector using Gemini's text-embedding-004 model

2. **Similarity Search**: 
   - Cosine similarity computed against all stored embeddings
   - Results filtered by threshold (0.4) and limited to top 8 matches
   - Chunks without embeddings are skipped efficiently

3. **Context Building**:
   - Top 3 most relevant chunks selected
   - Each chunk provides up to 3000 characters of context
   - Source URLs preserved for attribution

4. **Answer Generation**:
   - Context + question sent to Gemini 2.5 Flash
   - Model generates comprehensive answer
   - Falls back to general knowledge if context is insufficient

5. **Response Delivery**:
   - Answer formatted with markdown support
   - Source links displayed for verification
   - Related materials suggested

### Performance Optimizations

- **Query Caching**: Embeddings cached in-memory (max 100 queries, LRU)
- **Async Operations**: All database and API calls are asynchronous
- **Limited Scans**: Database queries limited to 500 chunks maximum
- **Batch Processing**: Embeddings generated in batches with rate limiting
- **Connection Pooling**: Efficient database connection management

## 📦 Installation

### Prerequisites

- Python 3.13+
- Node.js 18+
- Google Gemini API key

### Backend Setup

```bash
# Navigate to project directory
cd TDS_ai_chatbot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "API_KEY=your_gemini_api_key_here" > .env

# Build knowledge base (if not already done)
python build_kb.py

# Start backend server
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd "AI Chatbot Frontend"

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🗄️ Database Structure

### discourse_chunks
```sql
CREATE TABLE discourse_chunks (
    id INTEGER PRIMARY KEY,
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
```

### markdown_chunks
```sql
CREATE TABLE markdown_chunks (
    id INTEGER PRIMARY KEY,
    file_path TEXT,
    title TEXT,
    chunk_index INTEGER,
    content TEXT,
    url TEXT,
    embedding BLOB
)
```

## 📊 Knowledge Base Statistics

- **Total Embeddings**: ~1,804 chunks
- **Discourse Posts**: ~1,526 chunks from forum discussions
- **Documentation**: ~278 chunks from course materials
- **Embedding Dimensions**: 768 (Gemini text-embedding-004)
- **Average Chunk Size**: ~500-1000 characters

## 🔧 Configuration

Key parameters in `app.py`:

```python
SIMILARITY_THRESHOLD = 0.4    # Minimum cosine similarity for results
MAX_RESULTS = 8               # Maximum search results to consider
MAX_CONTEXT_CHUNKS = 3        # Number of chunks sent to LLM
QUERY_LIMIT = 500             # Maximum chunks to scan
```

## 🎯 API Endpoints

### POST /api
Main chatbot endpoint

**Request:**
```json
{
  "question": "What is Principal Component Analysis?",
  "image": "base64_encoded_image (optional)"
}
```

**Response:**
```json
{
  "answer": "Detailed answer with context...",
  "links": [
    {
      "url": "https://tds.s-anand.net/...",
      "text": "Source preview..."
    }
  ]
}
```

### GET /health
Health check endpoint

## 🚦 Running in Production

For production deployment, consider:

1. **Environment Variables**: Store API keys securely
2. **Database**: Backup regularly, consider read replicas for scaling
3. **Caching**: Implement Redis for distributed query caching
4. **Rate Limiting**: Add rate limiting middleware
5. **Monitoring**: Set up logging and error tracking
6. **CORS**: Configure CORS properly for your domain

## 📝 License

This project is developed for educational purposes as part of the Tools in Data Science course at IIT Madras.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📧 Contact

For questions or support, please reach out through the course Discourse forum.

---

Built with ❤️ for TDS students at IIT Madras
