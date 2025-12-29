from beanie import Document
from pydantic import Field
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    admin = "admin"
    client = "client"
    employee = "employee"

class User(Document):
    email: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: str
    role: UserRole = UserRole.client
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"
