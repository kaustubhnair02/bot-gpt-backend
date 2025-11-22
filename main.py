from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import Database, ConversationRepo, DocumentRepo
from llm_service import LLMService
from rag_service import RAGService
from models import (
    ConversationCreate, ConversationResponse, MessageCreate,
    ConversationDB, DocumentDB
)
from datetime import datetime
from typing import List
import logging
import base64
from uuid import uuid4

from config import settings, setup_logging
import logging
import traceback

# Setup logging
setup_logging()


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
llm_service = LLMService()
rag_service = RAGService()


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting up...")
    await Database.connect()
    yield
    # Shutdown
    logger.info("Shutting down...")
    await Database.close()


# Initialize FastAPI app
app = FastAPI(
    title="BOT GPT Backend",
    description="Conversational AI Backend with RAG support",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== HEALTH CHECK ====================

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "BOT GPT Backend is running",
        "version": "1.0.0"
    }


# ==================== CONVERSATION ENDPOINTS ====================

#v1
@app.post("/api/conversations", response_model=ConversationResponse, tags=["Conversations"])
async def create_conversation(data: ConversationCreate):
    """Create a new conversation with first message"""
    try:
        logger.info(f"Creating conversation - Mode: {data.mode}")
        
        # Validate RAG mode requirements
        if data.mode == "rag" and not data.document_id:
            logger.warning("RAG mode requested without document_id")
            raise HTTPException(status_code=400, detail="document_id required for RAG mode")
        
        # Create conversation object
        conversation = ConversationDB(mode=data.mode, document_id=data.document_id)
        
        # Prepare first message
        user_message = {
            "role": "user",
            "content": data.first_message,
            "timestamp": datetime.utcnow(),
            "tokens": llm_service.count_tokens(data.first_message)
        }
        
        # Get LLM response
        logger.info(f"Calling LLM for conversation: {conversation.conversation_id}")
        
        if data.mode == "open_chat":
            messages_for_llm = [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": data.first_message}
            ]
            response = await llm_service.generate_response(messages_for_llm)
            
        else:  # RAG mode
            logger.info(f"RAG mode - Retrieving document: {data.document_id}")
            document = await DocumentRepo.get_by_id(data.document_id)
            if not document:
                logger.error(f"Document not found: {data.document_id}")
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Retrieve relevant chunks
            relevant_chunks = rag_service.retrieve_relevant_chunks(
                query=data.first_message,
                document_chunks=document["chunks"]
            )
            logger.info(f"Retrieved {len(relevant_chunks)} chunks for RAG")
            
            # Build RAG prompt
            rag_prompt = rag_service.build_rag_prompt(data.first_message, relevant_chunks)
            
            messages_for_llm = [
                {"role": "system", "content": "You are a helpful assistant that answers based on provided context."},
                {"role": "user", "content": rag_prompt}
            ]
            
            response = await llm_service.generate_response(messages_for_llm)
            response["retrieved_chunks"] = [c["chunk_id"] for c in relevant_chunks]
        
        logger.info(f"LLM response generated - Tokens: {response['tokens']}")
        
        # Create assistant message
        assistant_message = {
            "role": "assistant",
            "content": response["content"],
            "timestamp": datetime.utcnow(),
            "tokens": response["tokens"],
            "model": response["model"],
            "retrieved_chunks": response.get("retrieved_chunks", [])
        }
        
        # Add messages to conversation
        conversation.messages = [user_message, assistant_message]
        conversation.total_tokens = user_message["tokens"] + assistant_message["tokens"]
        
        # Save to database
        logger.info(f"Saving conversation to database: {conversation.conversation_id}")
        saved_conv = await ConversationRepo.create(conversation.model_dump())
        
        logger.info(f"✓ Conversation created successfully: {conversation.conversation_id}")
        
        return ConversationResponse(
            conversation_id=saved_conv["conversation_id"],
            mode=saved_conv["mode"],
            messages=saved_conv["messages"],
            created_at=saved_conv["created_at"],
            updated_at=saved_conv["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Error creating conversation: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations", tags=["Conversations"])
async def list_conversations():
    """Get all conversations (sorted by recent) with document info for RAG mode"""
    try:
        conversations = await ConversationRepo.get_all()
        
        # Format response with document info
        result = []
        for c in conversations:
            conv_data = {
                "conversation_id": c["conversation_id"],
                "mode": c["mode"],
                "message_count": len(c["messages"]),
                "total_tokens": c["total_tokens"],
                "created_at": c["created_at"],
                "updated_at": c["updated_at"],
                "preview": c["messages"][0]["content"][:100] if c["messages"] else "",
                "document_name": None  # Default for open_chat
            }
            
            # If RAG mode, fetch document name
            if c["mode"] == "rag" and c.get("document_id"):
                document = await DocumentRepo.get_by_id(c["document_id"])
                if document:
                    conv_data["document_name"] = document["filename"]
            
            result.append(conv_data)
        
        return {
            "count": len(result),
            "conversations": result
        }
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


#v1
@app.post("/api/conversations/{conversation_id}/messages", tags=["Conversations"])
async def add_message(conversation_id: str, message: MessageCreate):
    """Add a new message to existing conversation"""
    try:
        logger.info(f"Adding message to conversation: {conversation_id}")
        
        # Get conversation
        conversation = await ConversationRepo.get_by_id(conversation_id)
        if not conversation:
            logger.error(f"Conversation not found: {conversation_id}")
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Create user message
        user_message = {
            "role": "user",
            "content": message.content,
            "timestamp": datetime.utcnow(),
            "tokens": llm_service.count_tokens(message.content)
        }
        
        # Add to conversation
        await ConversationRepo.add_message(conversation_id, user_message)
        
        # Prepare context
        all_messages = conversation["messages"] + [user_message]
        context = llm_service.prepare_context(all_messages, max_history=10)
        logger.info(f"Prepared context with {len(context)} messages")
        
        # Get LLM response
        logger.info(f"Calling LLM for message response")
        
        if conversation["mode"] == "open_chat":
            messages_for_llm = [{"role": "system", "content": "You are a helpful AI assistant."}] + context
            response = await llm_service.generate_response(messages_for_llm)
            
        else:  # RAG mode
            document = await DocumentRepo.get_by_id(conversation["document_id"])
            if not document:
                logger.error(f"Document not found: {conversation['document_id']}")
                raise HTTPException(status_code=404, detail="Document not found")
            
            relevant_chunks = rag_service.retrieve_relevant_chunks(
                query=message.content,
                document_chunks=document["chunks"]
            )
            logger.info(f"Retrieved {len(relevant_chunks)} chunks for RAG")
            
            rag_prompt = rag_service.build_rag_prompt(message.content, relevant_chunks)
            
            messages_for_llm = [
                {"role": "system", "content": "Answer based on provided context."},
                {"role": "user", "content": rag_prompt}
            ]
            
            response = await llm_service.generate_response(messages_for_llm)
            response["retrieved_chunks"] = [c["chunk_id"] for c in relevant_chunks]
        
        logger.info(f"LLM response generated - Tokens: {response['tokens']}")
        
        # Create assistant message
        assistant_message = {
            "role": "assistant",
            "content": response["content"],
            "timestamp": datetime.utcnow(),
            "tokens": response["tokens"],
            "model": response["model"],
            "retrieved_chunks": response.get("retrieved_chunks", [])
        }
        
        # Save assistant response
        await ConversationRepo.add_message(conversation_id, assistant_message)
        
        logger.info(f"✓ Message added successfully to conversation: {conversation_id}")
        
        return {
            "user_message": user_message,
            "assistant_message": assistant_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Error adding message: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))



@app.delete("/api/conversations/{conversation_id}", tags=["Conversations"])
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    try:
        logger.info(f"Deleting conversation: {conversation_id}")
        
        success = await ConversationRepo.delete(conversation_id)
        
        if not success:
            logger.warning(f"Conversation not found: {conversation_id}")
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        logger.info(f"✓ Deleted conversation: {conversation_id}")
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Error deleting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




# ==================== DOCUMENT ENDPOINTS (RAG) ====================
#v1
@app.post("/api/documents", tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """Upload document for RAG"""
    try:
        logger.info(f"Document upload started: {file.filename}")
        
        # Validate file type
        allowed_types = ["text/plain", "application/pdf"]
        if file.content_type not in allowed_types:
            logger.warning(f"Invalid file type: {file.content_type}")
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: txt, pdf")
        
        # Read file content
        content = await file.read()
        logger.info(f"File read successfully: {len(content)} bytes")
        
        # Extract text
        if file.content_type == "text/plain":
            text = content.decode("utf-8")
        else:  # PDF
            from pypdf import PdfReader
            from io import BytesIO
            
            logger.info("Extracting text from PDF")
            pdf_reader = PdfReader(BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        logger.info(f"Text extracted: {len(text)} characters")
        
        # Chunk text
        chunks = rag_service.chunk_text(text)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = rag_service.generate_embeddings(chunks)
        
        # Create document chunks
        document_chunks = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            document_chunks.append({
                "chunk_id": str(uuid4()),
                "text": chunk,
                "embedding": embedding.tolist(),
                "chunk_index": i
            })
        
        # Create document object
        document = DocumentDB(
            filename=file.filename,
            chunks=document_chunks,
            total_chunks=len(document_chunks)
        )
        
        # Save to database
        logger.info(f"Saving document to database: {document.document_id}")
        document_dict = document.model_dump()
        saved_doc = await DocumentRepo.create(document_dict)
        
        logger.info(f"✓ Document uploaded successfully: {document.document_id}")
        
        return {
            "document_id": document.document_id,
            "filename": document.filename,
            "total_chunks": document.total_chunks,
            "uploaded_at": document.uploaded_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Error uploading document: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/api/documents/{document_id}", tags=["Documents"])
async def get_document(document_id: str):
    """Get document metadata (not full chunks)"""
    try:
        document = await DocumentRepo.get_by_id(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "document_id": document["document_id"],
            "filename": document["filename"],
            "total_chunks": document["total_chunks"],
            "uploaded_at": document["uploaded_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
# :::::::: Get list of documents :::::::::

@app.get("/api/documents", tags=["Documents"])
async def list_documents():
    """Get all uploaded documents"""
    try:
        logger.info("Fetching all documents")
        
        db = Database.get_db()
        cursor = db.documents.find().sort("uploaded_at", -1)
        documents = await cursor.to_list(length=100)
        
        # Format response (exclude embeddings for efficiency)
        result = []
        for doc in documents:
            result.append({
                "document_id": doc["document_id"],
                "filename": doc["filename"],
                "total_chunks": doc["total_chunks"],
                "uploaded_at": doc["uploaded_at"]
            })
        
        logger.info(f"✓ Retrieved {len(result)} documents")
        
        return {
            "count": len(result),
            "documents": result
        }
        
    except Exception as e:
        logger.error(f"✗ Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@app.delete("/api/documents/{document_id}", tags=["Documents"])
async def delete_document(document_id: str):
    """Delete a document"""
    try:
        success = await DocumentRepo.delete(document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info(f"Deleted document: {document_id}")
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== RUN APP ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
