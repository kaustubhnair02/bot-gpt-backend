#v1
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect(cls):
        """Connect to MongoDB"""
        try:
            logger.info(f"Connecting to MongoDB: {settings.MONGODB_URL}")
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
            await cls.client.admin.command('ping')
            logger.info(f"✓ Connected to MongoDB: {settings.DATABASE_NAME}")
            
            # Create indexes
            db = cls.client[settings.DATABASE_NAME]
            await db.conversations.create_index("conversation_id", unique=True)
            await db.documents.create_index("document_id", unique=True)
            logger.info("✓ Database indexes created")
        except Exception as e:
            logger.error(f"✗ Failed to connect to MongoDB: {str(e)}")
            raise
    
    @classmethod
    async def close(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")
    
    @classmethod
    def get_db(cls):
        """Get database instance"""
        return cls.client[settings.DATABASE_NAME]


# CRUD Operations
class ConversationRepo:
    
    @staticmethod
    async def create(conversation_data: dict) -> dict:
        """Create new conversation"""
        db = Database.get_db()
        result = await db.conversations.insert_one(conversation_data)
        conversation_data["_id"] = str(result.inserted_id)
        logger.info(f"✓ Conversation saved: {conversation_data['conversation_id']}")
        return conversation_data
    
    @staticmethod
    async def get_by_id(conversation_id: str) -> Optional[dict]:
        """Get conversation by ID"""
        db = Database.get_db()
        conv = await db.conversations.find_one({"conversation_id": conversation_id})
        if conv:
            logger.info(f"✓ Retrieved conversation: {conversation_id}")
        else:
            logger.warning(f"⚠ Conversation not found: {conversation_id}")
        return conv
    
    @staticmethod
    async def get_all() -> List[dict]:
        """Get all conversations"""
        db = Database.get_db()
        cursor = db.conversations.find().sort("updated_at", -1)
        convs = await cursor.to_list(length=100)
        logger.info(f"✓ Retrieved {len(convs)} conversations")
        return convs
    
    @staticmethod
    async def add_message(conversation_id: str, message: dict) -> bool:
        """Add message to conversation"""
        db = Database.get_db()
        from datetime import datetime
        
        result = await db.conversations.update_one(
            {"conversation_id": conversation_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": datetime.utcnow()},
                "$inc": {"total_tokens": message.get("tokens", 0)}
            }
        )
        logger.info(f"✓ Message added to conversation: {conversation_id}")
        return result.modified_count > 0
    
    @staticmethod
    async def delete(conversation_id: str) -> bool:
        """Delete conversation"""
        db = Database.get_db()
        result = await db.conversations.delete_one({"conversation_id": conversation_id})
        if result.deleted_count > 0:
            logger.info(f"✓ Deleted conversation: {conversation_id}")
        return result.deleted_count > 0


class DocumentRepo:
    
    @staticmethod
    async def create(document_data: dict) -> dict:
        """Create new document"""
        db = Database.get_db()
        result = await db.documents.insert_one(document_data)
        document_data["_id"] = str(result.inserted_id)
        logger.info(f"✓ Document saved: {document_data['document_id']}")
        return document_data
    
    @staticmethod
    async def get_by_id(document_id: str) -> Optional[dict]:
        """Get document by ID"""
        db = Database.get_db()
        doc = await db.documents.find_one({"document_id": document_id})
        if doc:
            logger.info(f"✓ Retrieved document: {document_id}")
        else:
            logger.warning(f"⚠ Document not found: {document_id}")
        return doc
    
    @staticmethod
    async def delete(document_id: str) -> bool:
        """Delete document"""
        db = Database.get_db()
        result = await db.documents.delete_one({"document_id": document_id})
        if result.deleted_count > 0:
            logger.info(f"✓ Deleted document: {document_id}")
        return result.deleted_count > 0

