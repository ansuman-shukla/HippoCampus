from pinecone import Pinecone
from app.core.config import settings
from langchain_community.retrievers import PineconeHybridSearchRetriever
from pinecone_text.sparse import BM25Encoder
import nltk
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

index_name = settings.PINECONE_INDEX
GEMINI_API_KEY = settings.GEMINI_API_KEY
pc = Pinecone(api_key=settings.PINECONE_API_KEY)


# BM25_ENCODER_FILE = r"bm25_encoder.pkl"

# def get_bm25_encoder():
#     """Load or initialize BM25 encoder with persistent storage"""
#     if os.path.exists(BM25_ENCODER_FILE) and os.path.getsize(BM25_ENCODER_FILE) > 0:
#         try:
#             # Create new instance first okay ??

#             encoder = BM25Encoder()
#             # Then load into the instance
#             encoder.load(BM25_ENCODER_FILE)
#             return encoder
#         except Exception as e:
#             print(f"Error loading encoder: {e}, creating new one")
#             os.remove(BM25_ENCODER_FILE)
    
#     # Initialize new encoder and save properly
#     encoder = BM25Encoder.default()
#     os.makedirs(os.path.dirname(BM25_ENCODER_FILE), exist_ok=True)
#     encoder.dump(BM25_ENCODER_FILE)
#     return encoder

# bm25encoder = get_bm25_encoder()



# Initialize Pinecone index
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1024,  # E5-large requires 1024 dimensions
        metric="cosine",  # E5 works best with cosine similarity
        spec=ServerlessSpec(cloud='aws', region='us-east-1')
    )

index = pc.Index(index_name)