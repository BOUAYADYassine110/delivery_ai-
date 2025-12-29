from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, Dict, List

class Order(Document):
    tracking_number: str = Field(index=True, unique=True)
    sender_name: str
    sender_address: str
    sender_lat: Optional[float] = None
    sender_lng: Optional[float] = None
    sender_city: Optional[str] = None
    receiver_name: str
    receiver_address: str
    receiver_lat: Optional[float] = None
    receiver_lng: Optional[float] = None
    receiver_city: Optional[str] = None
    delivery_type: Optional[str] = None
    weight: float
    dimensions: Optional[Dict] = None
    service_type: str
    status: str = "pending"
    price: Optional[float] = None
    current_location: Optional[str] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    route_geometry: Optional[List] = None
    route_duration: Optional[float] = None
    route_distance: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "orders"
