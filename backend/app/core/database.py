from app.core.config import settings
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


uri = settings.MONGODB_URI

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

db = client[settings.MONGODB_DB]

# Create a new collection
collection = db[settings.MONGODB_COLLECTION_USER]
collection_memories = db[settings.MONGODB_COLLECTION_MEMORIES]
collection_notes = db[settings.MONGODB_COLLECTION_NOTES]



