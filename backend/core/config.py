from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "delivery_system"
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str = "dev-secret-key"
    OLLAMA_HOST: str = "http://localhost:11434"
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
