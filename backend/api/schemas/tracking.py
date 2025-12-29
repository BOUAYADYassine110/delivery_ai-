from pydantic import BaseModel
from datetime import datetime

class TrackingEventResponse(BaseModel):
    id: str
    order_id: str
    status: str
    location: str
    description: str
    agent_name: str
    timestamp: datetime
    
    class Config:
        from_attributes = True
