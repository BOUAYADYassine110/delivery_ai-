from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Optional
from datetime import datetime
from core.database import get_database
from core.auth import get_current_user
from api.services.gps_tracking import GPSTrackingService
from api.services.real_time_routing import routing_service
from api.services.notification_service import NotificationService
from api.models.tracking import LocationData, TrackingEvent, ActiveTracking
from api.models.user import User

router = APIRouter(prefix="/api/enhanced-tracking", tags=["Enhanced Tracking"])

@router.post("/start/{order_id}")
async def start_enhanced_tracking(
    order_id: str,
    route_data: Dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Start enhanced GPS tracking with real-time routing"""
    
    # Initialize services
    gps_service = GPSTrackingService(db)
    notification_service = NotificationService(db)
    
    # Get order details
    order = await db.orders.find_one({"_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Start GPS tracking
    tracking_session = await gps_service.start_tracking(
        order_id, 
        order.get("courier_id"), 
        route_data
    )
    
    # Start route monitoring
    background_tasks.add_task(
        routing_service.monitor_active_route,
        order_id,
        route_data
    )
    
    # Send notification
    await notification_service.send_delivery_status_update(
        order_id, "pickup_started"
    )
    
    return {
        "status": "success",
        "tracking_session": tracking_session,
        "message": "Enhanced tracking started"
    }

@router.post("/location/{order_id}")
async def update_courier_location(
    order_id: str,
    location_data: LocationData,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update courier location with enhanced processing"""
    
    gps_service = GPSTrackingService(db)
    notification_service = NotificationService(db)
    
    # Update location
    result = await gps_service.update_location(
        order_id, 
        location_data.dict()
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Handle geofence events
    for event in result.get("geofence_events", []):
        if event["type"] == "pickup_arrived":
            await notification_service.send_delivery_status_update(
                order_id, "pickup_arrived", location_data.dict()
            )
        elif event["type"] == "delivery_arrived":
            await notification_service.send_delivery_status_update(
                order_id, "delivery_arrived", location_data.dict()
            )
    
    return {
        "status": "success",
        "location_update": result,
        "message": "Location updated successfully"
    }

@router.get("/live/{order_id}")
async def get_live_tracking(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get live tracking data for an order"""
    
    # Get active tracking
    tracking = await db.active_trackings.find_one({"order_id": order_id})
    if not tracking:
        raise HTTPException(status_code=404, detail="Active tracking not found")
    
    # Get recent tracking events
    recent_events = await db.tracking_events.find(
        {"order_id": order_id}
    ).sort("timestamp", -1).limit(10).to_list(None)
    
    return {
        "active_tracking": tracking,
        "recent_events": recent_events,
        "live_location": tracking.get("current_location"),
        "eta": tracking.get("estimated_completion")
    }

@router.post("/route/optimize/{order_id}")
async def optimize_route_realtime(
    order_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Optimize route in real-time based on traffic and weather"""
    
    # Get current tracking
    tracking = await db.active_trackings.find_one({"order_id": order_id})
    if not tracking:
        raise HTTPException(status_code=404, detail="Active tracking not found")
    
    current_location = tracking.get("current_location")
    if not current_location:
        raise HTTPException(status_code=400, detail="Current location not available")
    
    # Calculate new optimal route
    destination = tracking["route"]["destination"]
    new_route = await routing_service.calculate_optimal_route(
        f"{current_location['lat']},{current_location['lng']}",
        f"{destination['lat']},{destination['lng']}"
    )
    
    # Update route if better
    if routing_service._should_reroute(tracking["route"], new_route):
        # Update tracking with new route
        await db.active_trackings.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "route": new_route,
                    "reroute_count": tracking.get("reroute_count", 0) + 1
                }
            }
        )
        
        # Send notification
        notification_service = NotificationService(db)
        await notification_service.send_notification(
            str(tracking["customer_id"]),
            "rerouted",
            {"order_id": order_id},
            {"eta": new_route.get("estimated_time")}
        )
        
        return {
            "status": "success",
            "new_route": new_route,
            "message": "Route optimized successfully"
        }
    else:
        return {
            "status": "no_change",
            "message": "Current route is already optimal"
        }

@router.post("/delivery/complete/{order_id}")
async def complete_delivery_with_proof(
    order_id: str,
    proof_data: Dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Complete delivery with proof of delivery"""
    
    gps_service = GPSTrackingService(db)
    notification_service = NotificationService(db)
    
    # Complete delivery
    result = await gps_service.complete_delivery(order_id, proof_data)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Send completion notification
    await notification_service.send_delivery_status_update(
        order_id, "delivered", proof_data
    )
    
    # Calculate delivery metrics
    background_tasks.add_task(
        calculate_delivery_metrics,
        order_id,
        db
    )
    
    return {
        "status": "success",
        "message": "Delivery completed successfully",
        "proof_of_delivery": proof_data
    }

@router.get("/analytics/{order_id}")
async def get_delivery_analytics(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get delivery analytics and metrics"""
    
    # Get tracking history
    tracking_events = await db.tracking_events.find(
        {"order_id": order_id}
    ).sort("timestamp", 1).to_list(None)
    
    # Get delivery metrics
    metrics = await db.delivery_metrics.find_one({"order_id": order_id})
    
    # Calculate analytics
    analytics = await calculate_route_analytics(tracking_events, metrics)
    
    return {
        "order_id": order_id,
        "tracking_events": tracking_events,
        "metrics": metrics,
        "analytics": analytics
    }

@router.get("/weather-traffic/{lat}/{lng}")
async def get_weather_traffic_conditions(
    lat: float,
    lng: float,
    current_user: User = Depends(get_current_user)
):
    """Get current weather and traffic conditions for a location"""
    
    # Get weather and traffic data
    conditions = await routing_service._get_weather_conditions(
        None,  # session will be created internally
        f"{lat},{lng}",
        f"{lat},{lng}"
    )
    
    return {
        "location": {"lat": lat, "lng": lng},
        "weather": conditions,
        "timestamp": datetime.now().isoformat()
    }

async def calculate_delivery_metrics(order_id: str, db):
    """Calculate delivery performance metrics"""
    
    # Get all tracking events for the order
    events = await db.tracking_events.find(
        {"order_id": order_id}
    ).sort("timestamp", 1).to_list(None)
    
    if not events:
        return
    
    # Find key events
    start_event = next((e for e in events if e["event_type"] == "pickup_started"), None)
    pickup_event = next((e for e in events if e["event_type"] == "package_picked_up"), None)
    delivery_event = next((e for e in events if e["event_type"] == "delivery_completed"), None)
    
    if not all([start_event, pickup_event, delivery_event]):
        return
    
    # Calculate metrics
    total_duration = (delivery_event["timestamp"] - start_event["timestamp"]).total_seconds()
    
    # Calculate total distance from location updates
    location_events = [e for e in events if e["event_type"] == "location_update" and e.get("location")]
    total_distance = 0
    
    for i in range(1, len(location_events)):
        prev_loc = location_events[i-1]["location"]
        curr_loc = location_events[i]["location"]
        
        # Simple distance calculation (in production, use proper geospatial functions)
        import math
        lat1, lng1 = prev_loc["lat"], prev_loc["lng"]
        lat2, lng2 = curr_loc["lat"], curr_loc["lng"]
        
        R = 6371000  # Earth radius in meters
        lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
        delta_lat, delta_lng = math.radians(lat2-lat1), math.radians(lng2-lng1)
        
        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        total_distance += distance
    
    # Get order and courier info
    order = await db.orders.find_one({"_id": order_id})
    courier_id = order.get("courier_id") if order else None
    
    # Create metrics record
    metrics = {
        "order_id": order_id,
        "courier_id": courier_id,
        "total_distance": total_distance,
        "total_duration": int(total_duration),
        "pickup_time": pickup_event["timestamp"],
        "delivery_time": delivery_event["timestamp"],
        "route_efficiency": min(100, (3600 / total_duration) * 100),  # Simple efficiency score
        "delivery_attempts": 1,
        "created_at": datetime.now()
    }
    
    await db.delivery_metrics.insert_one(metrics)

async def calculate_route_analytics(tracking_events: List[Dict], metrics: Dict) -> Dict:
    """Calculate route analytics from tracking data"""
    
    if not tracking_events:
        return {}
    
    # Basic analytics
    total_events = len(tracking_events)
    location_updates = len([e for e in tracking_events if e["event_type"] == "location_update"])
    reroute_count = len([e for e in tracking_events if e["event_type"] == "reroute"])
    
    # Time analysis
    start_time = tracking_events[0]["timestamp"]
    end_time = tracking_events[-1]["timestamp"]
    total_time = (end_time - start_time).total_seconds() / 3600  # hours
    
    return {
        "total_events": total_events,
        "location_updates": location_updates,
        "reroute_count": reroute_count,
        "total_time_hours": round(total_time, 2),
        "average_speed": round(metrics.get("total_distance", 0) / 1000 / max(total_time, 0.1), 2) if metrics else 0,
        "efficiency_score": metrics.get("route_efficiency", 0) if metrics else 0
    }