from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class OrderCreate(BaseModel):
    sender_name: str
    sender_address: str
    sender_lat: float
    sender_lng: float
    receiver_name: str
    receiver_address: str
    receiver_lat: float
    receiver_lng: float
    weight: float
    dimensions: Dict[str, float]
    service_type: str

class OrderResponse(BaseModel):
    id: str
    tracking_number: str
    sender_name: str
    sender_address: str
    sender_lat: Optional[float]
    sender_lng: Optional[float]
    sender_city: Optional[str]
    receiver_name: str
    receiver_address: str
    receiver_lat: Optional[float]
    receiver_lng: Optional[float]
    receiver_city: Optional[str]
    delivery_type: Optional[str]
    weight: float
    dimensions: Dict
    service_type: str
    status: str
    price: Optional[float]
    current_location: Optional[str]
    current_lat: Optional[float]
    current_lng: Optional[float]
    route_geometry: Optional[List]
    route_duration: Optional[float]
    route_distance: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True

class PricingRequest(BaseModel):
    weight: float
    distance: float
    service_type: str
