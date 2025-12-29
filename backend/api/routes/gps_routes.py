from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter()

class GPSUpdate(BaseModel):
    driver_id: str
    order_id: Optional[str] = None
    latitude: float
    longitude: float
    accuracy: float = 5.0
    speed: float = 0.0
    heading: float = 0.0
    timestamp: Optional[str] = None

class GeofenceCheck(BaseModel):
    latitude: float
    longitude: float
    target_lat: float
    target_lng: float
    radius: float = 100.0

# In-memory storage for GPS data (replace with database in production)
gps_data = {}
geofence_events = []

@router.post("/gps/update")
async def update_gps_location(gps_update: GPSUpdate):
    """Update driver GPS location with enhanced tracking"""
    
    # Store GPS data
    if gps_update.driver_id not in gps_data:
        gps_data[gps_update.driver_id] = []
    
    location_data = {
        "latitude": gps_update.latitude,
        "longitude": gps_update.longitude,
        "accuracy": gps_update.accuracy,
        "speed": gps_update.speed,
        "heading": gps_update.heading,
        "timestamp": gps_update.timestamp or datetime.now().isoformat(),
        "order_id": gps_update.order_id
    }
    
    gps_data[gps_update.driver_id].append(location_data)
    
    # Keep only last 100 locations per driver
    if len(gps_data[gps_update.driver_id]) > 100:
        gps_data[gps_update.driver_id] = gps_data[gps_update.driver_id][-100:]
    
    # Check for geofence events if order_id provided
    geofence_alerts = []
    if gps_update.order_id:
        # Mock pickup/delivery coordinates (replace with database lookup)
        pickup_coords = {"lat": 33.5731, "lng": -7.5898}
        delivery_coords = {"lat": 33.5750, "lng": -7.5900}
        
        # Check pickup geofence
        pickup_distance = calculate_distance(
            gps_update.latitude, gps_update.longitude,
            pickup_coords["lat"], pickup_coords["lng"]
        )
        
        # Check delivery geofence
        delivery_distance = calculate_distance(
            gps_update.latitude, gps_update.longitude,
            delivery_coords["lat"], delivery_coords["lng"]
        )
        
        if pickup_distance <= 0.1:  # 100 meters
            geofence_alerts.append({
                "type": "pickup_arrival",
                "message": "Driver arrived at pickup location",
                "distance": pickup_distance * 1000
            })
        
        if delivery_distance <= 0.1:  # 100 meters
            geofence_alerts.append({
                "type": "delivery_arrival", 
                "message": "Driver arrived at delivery location",
                "distance": delivery_distance * 1000
            })
    
    return {
        "success": True,
        "message": "GPS location updated",
        "location": location_data,
        "geofence_alerts": geofence_alerts,
        "tracking_quality": get_tracking_quality(gps_update.accuracy, gps_update.speed)
    }

@router.get("/gps/driver/{driver_id}")
async def get_driver_gps_history(driver_id: str, limit: int = 50):
    """Get GPS history for a driver"""
    
    if driver_id not in gps_data:
        return {"locations": [], "total": 0}
    
    locations = gps_data[driver_id][-limit:]
    
    return {
        "driver_id": driver_id,
        "locations": locations,
        "total": len(locations),
        "last_update": locations[-1]["timestamp"] if locations else None
    }

@router.post("/gps/geofence/check")
async def check_geofence(geofence_check: GeofenceCheck):
    """Check if location is within geofence"""
    
    distance = calculate_distance(
        geofence_check.latitude, geofence_check.longitude,
        geofence_check.target_lat, geofence_check.target_lng
    ) * 1000  # Convert to meters
    
    is_within = distance <= geofence_check.radius
    
    return {
        "within_geofence": is_within,
        "distance_meters": round(distance, 2),
        "radius_meters": geofence_check.radius,
        "status": "inside" if is_within else "outside"
    }

@router.get("/gps/route/{order_id}")
async def get_order_route_tracking(order_id: str):
    """Get real-time route tracking for an order"""
    
    # Find GPS data for this order
    route_points = []
    for driver_id, locations in gps_data.items():
        for location in locations:
            if location.get("order_id") == order_id:
                route_points.append({
                    "lat": location["latitude"],
                    "lng": location["longitude"],
                    "timestamp": location["timestamp"],
                    "speed": location["speed"],
                    "accuracy": location["accuracy"]
                })
    
    # Sort by timestamp
    route_points.sort(key=lambda x: x["timestamp"])
    
    # Calculate route statistics
    total_distance = 0
    if len(route_points) > 1:
        for i in range(1, len(route_points)):
            prev_point = route_points[i-1]
            curr_point = route_points[i]
            total_distance += calculate_distance(
                prev_point["lat"], prev_point["lng"],
                curr_point["lat"], curr_point["lng"]
            )
    
    return {
        "order_id": order_id,
        "route_points": route_points,
        "total_points": len(route_points),
        "total_distance_km": round(total_distance, 2),
        "start_time": route_points[0]["timestamp"] if route_points else None,
        "last_update": route_points[-1]["timestamp"] if route_points else None
    }

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two GPS coordinates in kilometers"""
    import math
    
    R = 6371  # Earth's radius in km
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_lat/2)**2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def get_tracking_quality(accuracy: float, speed: float) -> str:
    """Determine GPS tracking quality"""
    if accuracy <= 5:
        return "excellent"
    elif accuracy <= 15:
        return "good"
    elif accuracy <= 50:
        return "fair"
    else:
        return "poor"