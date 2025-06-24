from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_API_KEY: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str  # This is the JWT secret from Supabase dashboard
    MONGODB_DB: str
    MONGODB_URI: str
    PINECONE_API_KEY: str
    PINECONE_INDEX: str
    GEMINI_API_KEY: str
    MONGODB_COLLECTION_USER: str
    MONGODB_COLLECTION_NOTES: str
    MONGODB_COLLECTION_MEMORIES: str


    class Config:
        env_file = ".env"

settings = Settings()