from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, Dict

class DeliveryAnalytics(Document):
    order_id: str = Field(index=True)
    tracking_number: str
    route_distance_planned: Optional[float] = None
    route_distance_actual: Optional[float] = None
    duration_estimated: Optional[float] = None
    duration_actual: Optional[float] = None
    weather_at_pickup: Optional[Dict] = None
    weather_at_delivery: Optional[Dict] = None
    weather_impact: Optional[str] = None
    traffic_level: Optional[str] = None
    traffic_delays: Optional[float] = None
    courier_id: Optional[str] = None
    courier_rating: Optional[float] = None
    acceptance_time: Optional[float] = None
    price_charged: Optional[float] = None
    cost_estimate: Optional[float] = None
    profit_margin: Optional[float] = None
    customer_satisfaction: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    agent_decisions: Optional[Dict] = None
    
    class Settings:
        name = "delivery_analytics"

class APICallLog(Document):
    order_id: str = Field(index=True)
    api_name: str
    endpoint: str
    request_params: Optional[Dict] = None
    response_data: Optional[Dict] = None
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "api_call_logs"

class DeliveryEvent(Document):
    order_id: str = Field(index=True)
    event_type: str
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_name: Optional[str] = None
    weather_conditions: Optional[Dict] = None
    traffic_conditions: Optional[str] = None
    courier_id: Optional[str] = None
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "delivery_events"
