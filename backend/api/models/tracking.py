from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

class TrackingEventType(str, Enum):
    ORDER_CREATED = "order_created"
    COURIER_ASSIGNED = "courier_assigned"
    PICKUP_STARTED = "pickup_started"
    PICKUP_ARRIVED = "pickup_arrived"
    PACKAGE_PICKED_UP = "package_picked_up"
    IN_TRANSIT = "in_transit"
    LOCATION_UPDATE = "location_update"
    REROUTE = "reroute"
    DELIVERY_ARRIVED = "delivery_arrived"
    DELIVERY_COMPLETED = "delivery_completed"
    WAREHOUSE_ARRIVAL = "warehouse_arrival"
    WAREHOUSE_DEPARTURE = "warehouse_departure"
    CUSTOMS_CLEARANCE = "customs_clearance"
    DELAYED = "delayed"
    EXCEPTION = "exception"

class LocationData(BaseModel):
    lat: float
    lng: float
    address: Optional[str] = None
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    altitude: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class ETAData(BaseModel):
    eta: datetime
    distance_remaining: float
    estimated_speed: float
    time_remaining_minutes: int
    confidence_level: Optional[str] = "medium"

class RouteData(BaseModel):
    origin: LocationData
    destination: LocationData
    waypoints: Optional[List[LocationData]] = []
    distance: float
    duration: int
    polyline: Optional[str] = None
    traffic_level: Optional[str] = "normal"
    weather_impact: Optional[str] = "low"
    route_score: Optional[float] = 100.0

class ProofOfDelivery(BaseModel):
    signature: Optional[str] = None
    photo: Optional[str] = None
    recipient_name: Optional[str] = None
    delivery_notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    location: Optional[LocationData] = None

class TrackingEvent(Document):
    order_id: str
    event_type: TrackingEventType
    timestamp: datetime = Field(default_factory=datetime.now)
    location: Optional[LocationData] = None
    eta: Optional[ETAData] = None
    route: Optional[RouteData] = None
    courier_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = {}
    proof_of_delivery: Optional[ProofOfDelivery] = None
    
    class Settings:
        name = "tracking_events"
        indexes = [
            "order_id",
            "event_type", 
            "timestamp",
            "courier_id"
        ]

class GeofenceEvent(BaseModel):
    geofence_id: str
    geofence_type: str  # pickup, delivery, warehouse
    center: LocationData
    radius: float
    triggered: bool = False
    trigger_time: Optional[datetime] = None

class ActiveTracking(Document):
    order_id: str
    courier_id: str
    customer_id: str
    status: str = "active"
    current_location: Optional[LocationData] = None
    route: Optional[RouteData] = None
    geofences: List[GeofenceEvent] = []
    start_time: datetime = Field(default_factory=datetime.now)
    last_update: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    reroute_count: int = 0
    
    class Settings:
        name = "active_trackings"
        indexes = [
            "order_id",
            "courier_id",
            "customer_id",
            "status"
        ]

class DeliveryMetrics(Document):
    order_id: str
    courier_id: str
    total_distance: float
    total_duration: int  # seconds
    pickup_time: Optional[datetime] = None
    delivery_time: Optional[datetime] = None
    route_efficiency: Optional[float] = None  # 0-100 score
    customer_rating: Optional[int] = None  # 1-5 stars
    delivery_attempts: int = 1
    fuel_consumption: Optional[float] = None
    carbon_footprint: Optional[float] = None
    
    class Settings:
        name = "delivery_metrics"
        indexes = [
            "order_id",
            "courier_id",
            "delivery_time"
        ]