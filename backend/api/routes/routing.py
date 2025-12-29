from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from api.services.real_time_routing import RealTimeRoutingService

router = APIRouter()

class RouteRequest(BaseModel):
    driver_location: dict  # {"lat": float, "lng": float}
    waypoints: List[dict]  # [{"lat": float, "lng": float, "type": "pickup|delivery", "address": str}]
    vehicle_type: str = "bike"
    driver_id: Optional[str] = None

class RouteOptimizationRequest(BaseModel):
    driver_id: str
    order_ids: List[str]

@router.post("/route/calculate")
async def calculate_optimized_route(request: RouteRequest):
    """Calculate optimized route with real-time conditions"""
    
    routing_service = RealTimeRoutingService()
    
    try:
        optimized_route = await routing_service.calculate_optimized_route(
            driver_location=request.driver_location,
            waypoints=request.waypoints,
            vehicle_type=request.vehicle_type
        )
        
        return {
            "success": True,
            "route": optimized_route,
            "generated_at": routing_service.datetime.now().isoformat() if hasattr(routing_service, 'datetime') else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route calculation failed: {str(e)}")

@router.post("/route/optimize-multi-stop")
async def optimize_multi_stop_route(request: RouteOptimizationRequest):
    """Optimize route for multiple pickup/delivery stops"""
    from main import orders_db, drivers_db
    
    # Get driver and orders
    driver = next((d for d in drivers_db if d["id"] == request.driver_id), None)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    orders = [o for o in orders_db if o["id"] in request.order_ids]
    if not orders:
        raise HTTPException(status_code=404, detail="No orders found")
    
    # Build waypoints from orders
    waypoints = []
    for order in orders:
        # Add pickup point
        if order["status"] in ["accepted", "assigned"]:
            pickup_coords = get_address_coordinates(order["pickup_address"], order["pickup_city"])
            waypoints.append({
                "lat": pickup_coords["lat"],
                "lng": pickup_coords["lng"],
                "type": "pickup",
                "address": order["pickup_address"],
                "order_id": order["id"],
                "contact": order.get("sender_name", "Sender"),
                "phone": order.get("sender_phone", "")
            })
        
        # Add delivery point
        if order["status"] in ["picked_up", "in_transit"]:
            delivery_coords = get_address_coordinates(order["delivery_address"], order["delivery_city"])
            waypoints.append({
                "lat": delivery_coords["lat"],
                "lng": delivery_coords["lng"],
                "type": "delivery",
                "address": order["delivery_address"],
                "order_id": order["id"],
                "contact": order.get("receiver_name", "Receiver"),
                "phone": order.get("receiver_phone", "")
            })
    
    if not waypoints:
        return {"success": False, "message": "No active waypoints found"}
    
    # Optimize waypoint order (simple nearest neighbor for now)
    optimized_waypoints = optimize_waypoint_order(driver["current_location"], waypoints)
    
    # Calculate route
    routing_service = RealTimeRoutingService()
    optimized_route = await routing_service.calculate_optimized_route(
        driver_location=driver["current_location"],
        waypoints=optimized_waypoints,
        vehicle_type=driver.get("vehicle_type", "bike")
    )
    
    # Add waypoint details to route
    optimized_route["waypoints"] = optimized_waypoints
    optimized_route["total_stops"] = len(optimized_waypoints)
    
    return {
        "success": True,
        "driver": driver,
        "route": optimized_route,
        "optimization_summary": {
            "total_distance": f"{optimized_route['distance'] / 1000:.1f} km",
            "estimated_time": f"{optimized_route['optimized_duration'] // 60} minutes",
            "stops": len(optimized_waypoints),
            "route_quality": optimized_route.get("route_quality", "good")
        }
    }

@router.get("/route/driver/{driver_id}/current")
async def get_current_driver_route(driver_id: str):
    """Get current optimized route for driver"""
    from main import orders_db, drivers_db
    
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    # Get active orders for driver
    active_orders = [o for o in orders_db if 
                    o.get("assigned_driver") == driver_id and 
                    o["status"] in ["accepted", "assigned", "picked_up", "in_transit"]]
    
    if not active_orders:
        return {"success": False, "message": "No active orders for driver"}
    
    # Use multi-stop optimization
    order_ids = [o["id"] for o in active_orders]
    request = RouteOptimizationRequest(driver_id=driver_id, order_ids=order_ids)
    
    return await optimize_multi_stop_route(request)

@router.get("/route/weather/{lat}/{lng}")
async def get_route_weather(lat: float, lng: float):
    """Get weather conditions for route location"""
    
    routing_service = RealTimeRoutingService()
    weather = await routing_service.get_weather_conditions({"lat": lat, "lng": lng})
    
    return {
        "location": {"lat": lat, "lng": lng},
        "weather": weather,
        "driving_conditions": {
            "visibility": "poor" if weather.get("is_foggy") else "good",
            "road_conditions": "wet" if weather.get("is_rainy") else "dry",
            "recommended_speed": get_recommended_speed(weather),
            "safety_level": get_safety_level(weather)
        }
    }

def get_address_coordinates(address: str, city: str) -> dict:
    """Get coordinates for address (simplified)"""
    # City center coordinates as fallback
    city_coords = {
        "casablanca": {"lat": 33.5731, "lng": -7.5898},
        "rabat": {"lat": 34.0209, "lng": -6.8416},
        "marrakech": {"lat": 31.6295, "lng": -7.9811},
        "el jadida": {"lat": 33.2316, "lng": -8.5007},
        "salé": {"lat": 34.0531, "lng": -6.7985},
        "agadir": {"lat": 30.4278, "lng": -9.5981}
    }
    
    base_coords = city_coords.get(city.lower(), city_coords["casablanca"])
    
    # Add small random offset for different addresses
    import random
    offset = 0.01
    return {
        "lat": base_coords["lat"] + random.uniform(-offset, offset),
        "lng": base_coords["lng"] + random.uniform(-offset, offset)
    }

def optimize_waypoint_order(start_location: dict, waypoints: List[dict]) -> List[dict]:
    """Optimize waypoint order using nearest neighbor algorithm"""
    if not waypoints:
        return []
    
    # Separate pickups and deliveries
    pickups = [wp for wp in waypoints if wp["type"] == "pickup"]
    deliveries = [wp for wp in waypoints if wp["type"] == "delivery"]
    
    # Process pickups first (nearest neighbor)
    optimized = []
    current_location = start_location
    remaining_pickups = pickups.copy()
    
    while remaining_pickups:
        nearest = min(remaining_pickups, key=lambda wp: 
                     calculate_distance(current_location["lat"], current_location["lng"], 
                                      wp["lat"], wp["lng"]))
        optimized.append(nearest)
        current_location = nearest
        remaining_pickups.remove(nearest)
    
    # Then process deliveries
    remaining_deliveries = deliveries.copy()
    while remaining_deliveries:
        nearest = min(remaining_deliveries, key=lambda wp: 
                     calculate_distance(current_location["lat"], current_location["lng"], 
                                      wp["lat"], wp["lng"]))
        optimized.append(nearest)
        current_location = nearest
        remaining_deliveries.remove(nearest)
    
    return optimized

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between coordinates"""
    import math
    R = 6371
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_lat/2)**2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def get_recommended_speed(weather: dict) -> str:
    """Get recommended speed based on weather"""
    if weather.get("is_foggy"):
        return "very_slow"
    elif weather.get("is_rainy"):
        return "slow"
    elif weather.get("is_windy"):
        return "moderate"
    else:
        return "normal"

def get_safety_level(weather: dict) -> str:
    """Get safety level based on weather"""
    danger_score = 0
    
    if weather.get("is_foggy"):
        danger_score += 3
    if weather.get("is_rainy"):
        danger_score += 2
    if weather.get("is_windy"):
        danger_score += 1
    
    if danger_score >= 3:
        return "high_risk"
    elif danger_score >= 2:
        return "moderate_risk"
    elif danger_score >= 1:
        return "low_risk"
    else:
        return "safe"