
# BOT GPT - Conversational AI Backend

A production-ready conversational AI backend with RAG (Retrieval-Augmented Generation) support, built with FastAPI, MongoDB, and Streamlit.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-latest-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.29.0-red.svg)

## 🎯 Features

- 💬 **Open Chat Mode**: Direct conversations with LLM (Llama 3.1 via Groq)
- 📚 **RAG Mode**: Chat with your documents (PDF, TXT)
- 🗄️ **Persistent Storage**: MongoDB for conversations and documents
- 🎨 **Interactive UI**: Streamlit-based chat interface
- 📊 **Document Management**: Upload, view, and delete documents
- 💾 **Conversation History**: Browse and resume past conversations
- 🔍 **Semantic Search**: TF-IDF based document retrieval
- 📝 **Comprehensive Logging**: File and console logging with rotation


## 📋 Prerequisites

- Python 3.10 or higher
- MongoDB (local or Docker)
- Groq API key (free tier available)

## 🚀 Quick Start

### 1. Clone the Repository

git clone <your-repo-url>
cd bot-gpt-backend


### 2. Create Virtual Environment

python3 -m venv botgpt-env
source botgpt-env/bin/activate # On Windows: botgpt-env\Scripts\activate


### 3. Install Dependencies

pip install -r requirements.txt


### 4. Setup MongoDB

**Option A: Using Docker**
docker run -d -p 27017:27017 --name mongodb mongo:latest

text

**Option B: Install Locally**
- Download from [MongoDB Official Site](https://www.mongodb.com/try/download/community)
- Start MongoDB service

### 5. Configure Environment

Create a `.env` file in the project root:

MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=bot_gpt

LLM Configuration (Groq)
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

RAG Configuration
CHUNK_SIZE=500
TOP_K=3

text

**Get Groq API Key**: Sign up at [console.groq.com](https://console.groq.com) (free tier available)

### 6. Run the Backend

python main.py


Backend will start at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### 7. Run the Frontend

Open a new terminal:

cd frontend
streamlit run app.py


Frontend will open at: `http://localhost:8501`


## 📁 Project Structure

```
bot-gpt-backend/
├── main.py                 # FastAPI app with all routes
├── database.py             # MongoDB operations & CRUD
├── llm_service.py          # LLM integration (Groq)
├── rag_service.py          # RAG pipeline (embeddings + retrieval)
├── models.py               # Pydantic schemas
├── config.py               # Settings & configuration
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── .env.example            # Example environment file
├── logs/                   # Application logs (auto-created)
│   └── bot_gpt.log
├── frontend/
│   └── app.py             # Streamlit UI
├── Dockerfile             # Docker configuration (optional)
├── docker-compose.yml     # Docker Compose (optional)
└── README.md              # This file
```


## 🔌 API Endpoints

### Conversations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/conversations` | Create new conversation with first message |
| GET | `/api/conversations` | List all conversations |
| GET | `/api/conversations/{id}` | Get conversation by ID |
| POST | `/api/conversations/{id}/messages` | Add message to conversation |
| DELETE | `/api/conversations/{id}` | Delete conversation |

### Documents (RAG)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents` | Upload document for RAG |
| GET | `/api/documents` | List all documents |
| GET | `/api/documents/{id}` | Get document info |
| DELETE | `/api/documents/{id}` | Delete document |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check & API status |

## 💡 Usage Examples

### Open Chat Mode

1. Open the Streamlit UI
2. Select **"Open Chat"** mode in sidebar
3. Type your message and press Enter
4. Get instant AI responses

### RAG Mode (Chat with Documents)

1. Select **"RAG Mode"** in sidebar
2. Click **"Upload Document"** and choose a PDF or TXT file
3. Wait for processing (chunking + embedding)
4. Ask questions about the document
5. Get grounded responses with context from your document

### Managing Conversations

- **View History**: All conversations are listed in the sidebar
- **Resume Chat**: Click any conversation to continue
- **Delete Chat**: Click 🗑️ button next to conversation
- **New Chat**: Click "➕ New Conversation" button

### Managing Documents

- **View Uploads**: Click "📚 Document Library" expander in sidebar
- **Delete Document**: Click 🗑️ button next to document

## 🗄️ Database Schema

### Conversations Collection

{
"conversation_id": "uuid",
"mode": "open_chat | rag",
"document_id": "uuid (if RAG)",
"messages": [
{
"role": "user | assistant",
"content": "message text",
"timestamp": "datetime",
"tokens": 150,
"retrieved_chunks": []
}
],
"total_tokens": 500,
"created_at": "datetime",
"updated_at": "datetime"
}


### Documents Collection

{
"document_id": "uuid",
"filename": "research_paper.pdf",
"chunks": [
{
"chunk_id": "uuid",
"text": "chunk content",
"embedding": [],
"chunk_index": 0
}
],
"total_chunks": 25,
"uploaded_at": "datetime"
}



🔧 Technologies Used
Backend
FastAPI - Modern async web framework

Motor - Async MongoDB driver

Pydantic - Data validation

Groq - Fast LLM inference (Llama 3.1)

RAG Pipeline
sentence-transformers - Text embedding models (all-MiniLM-L6-v2)

HuggingFace Hub - Model repository and inference

scikit-learn - Cosine similarity calculations

pypdf - PDF text extraction

NumPy - Vector operations

Frontend
Streamlit - Interactive web UI

Requests - HTTP client

Database
MongoDB - NoSQL document database

## 📊 Logging & Monitoring

Logs are stored in `logs/bot_gpt.log` with automatic rotation:

2025-11-21 17:30:15 - main - INFO - Creating conversation - Mode: rag
2025-11-21 17:30:16 - llm_service - INFO - Calling LLM with 2 messages
2025-11-21 17:30:18 - llm_service - INFO - ✓ LLM response: 245 tokens
2025-11-21 17:30:18 - main - INFO - ✓ Conversation created successfully



**Log Levels:**
- ✓ INFO - Successful operations
- ⚠ WARNING - Non-critical issues
- ✗ ERROR - Failures with stack traces

## ⚙️ Configuration

Edit `config.py` or `.env` file:

Chunk size for RAG
CHUNK_SIZE = 500 # characters per chunk

Number of chunks to retrieve
TOP_K = 3

LLM Model
GROQ_MODEL = "llama-3.1-8b-instant" # or llama-3.1-70b-versatile



## 🐳 Docker Deployment (Optional)

### Build and Run with Docker Compose

Create .env file with your API keys first
Start all services
docker-compose up -d

View logs
docker-compose logs -f

Stop services
docker-compose down



Services:
- Backend: `http://localhost:8000`
- MongoDB: `localhost:27017`

## 🧪 Testing

### Test Backend API

Health check
curl http://localhost:8000/

Create conversation
curl -X POST http://localhost:8000/api/conversations
-H "Content-Type: application/json"
-d '{"mode": "open_chat", "first_message": "Hello!"}'

List conversations
curl http://localhost:8000/api/conversations



### Using Swagger UI

Navigate to `http://localhost:8000/docs` for interactive API testing.

## 🚨 Troubleshooting

### MongoDB Connection Error

Check if MongoDB is running
docker ps # if using Docker

or
brew services list # if using Homebrew on macOS



### Groq API Error

- Verify your API key in `.env`
- Check rate limits at [console.groq.com](https://console.groq.com)
- Free tier: 30 requests/minute

### Import Errors

Reinstall dependencies
pip install --upgrade -r requirements.txt



### Port Already in Use

Change port in main.py
uvicorn.run("main:app", host="0.0.0.0", port=8001) # Use 8001 instead



## 📝 Design Decisions
Why Sentence Transformers?
For this case study, sentence-transformers provides:

✅ Semantic search - Understanding meaning, not just keywords

✅ Pre-trained models - No training required

✅ Fast inference - Local embedding generation

✅ State-of-art accuracy - Better than traditional TF-IDF

✅ Small model size - all-MiniLM-L6-v2 (80MB) runs locally

Embedding Model: all-MiniLM-L6-v2
384-dimensional vectors - Compact but effective

Fast - 14,000 sentences/second on CPU

Balanced - Good accuracy for general use cases

No GPU required - Runs on any machine

Why MongoDB?
✅ Flexible schema for conversation messages

✅ Easy to store nested documents (chunks, embeddings)

✅ Good for prototyping and iteration

✅ Can store vector embeddings as arrays

Why Groq?
✅ Free tier with high rate limits

✅ Fast inference (< 1s response time)

✅ Llama 3.1 models (70B and 8B)

✅ OpenAI-compatible API

RAG Pipeline Details (ADD THIS NEW SECTION)
How RAG Works in This Project:

Document Upload

User uploads PDF/TXT file

Text is extracted and split into 500-character chunks

Each chunk is embedded using sentence-transformers

Embeddings (384-dim vectors) are stored in MongoDB

Query Processing

User asks a question

Question is converted to embedding vector

Cosine similarity search finds top 3 relevant chunks

Retrieved chunks are injected into LLM prompt

Response Generation

LLM receives context + user question

Generates grounded response based on document content

Response is returned to user with chunk references

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [MongoDB Tutorial](https://www.mongodb.com/docs/manual/tutorial/)
- [Groq API Docs](https://console.groq.com/docs)

## 📄 License

MIT License - feel free to use this project for learning and development.

## 📧 Support

For questions or issues:
- Check logs in `logs/bot_gpt.log`
- Review API docs at `/docs`
- Verify environment variables in `.env`

---
Demonstrates: Backend Architecture, API Design, LLM Integration, RAG Implementation, Database Modeling