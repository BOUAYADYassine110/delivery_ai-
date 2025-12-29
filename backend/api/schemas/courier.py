from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CourierCreate(BaseModel):
    name: str
    phone: str
    vehicle_type: str
    vehicle_number: str

class CourierResponse(BaseModel):
    id: int
    user_id: Optional[int]
    name: str
    phone: str
    vehicle_type: str
    vehicle_number: str
    status: str
    current_lat: Optional[float]
    current_lng: Optional[float]
    rating: float
    total_deliveries: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class LocationUpdate(BaseModel):
    lat: float
    lng: float
