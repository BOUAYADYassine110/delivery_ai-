"""
Configuration Helper
Centralized access to environment variables
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "delivery_system")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# AI
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# External APIs
ORS_API_KEY = os.getenv("ORS_API_KEY", "")
OWM_API_KEY = os.getenv("OWM_API_KEY", "")

# Application
APP_NAME = os.getenv("APP_NAME", "Multi-Agent Delivery System")
APP_VERSION = os.getenv("APP_VERSION", "3.0")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Server
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8001"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Business Logic
DRIVER_COMMISSION_RATE = float(os.getenv("DRIVER_COMMISSION_RATE", "0.15"))
BASE_PRICE_INTRA_CITY = float(os.getenv("BASE_PRICE_INTRA_CITY", "25.0"))
BASE_PRICE_INTER_CITY = float(os.getenv("BASE_PRICE_INTER_CITY", "50.0"))
