from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional

class Courier(Document):
    user_id: Optional[int] = None
    email: str = Field(index=True, unique=True)
    password_hash: str
    name: str
    phone: str
    vehicle_type: str
    vehicle_number: str
    status: str = "available"
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    assigned_order_id: Optional[str] = None
    rating: float = 5.0
    total_deliveries: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "couriers"
