from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from api.services.real_time_routing import RealTimeRoutingService
from api.services.multi_package_optimizer import MultiPackageOptimizer

router = APIRouter(prefix="/api/route", tags=["enhanced_routing"])

class RouteRequest(BaseModel):
    start_location: Dict[str, float]
    waypoints: List[Dict[str, float]]
    vehicle_type: str = "car"
    optimize: bool = True

@router.post("/calculate")
async def calculate_enhanced_route(request: RouteRequest):
    try:
        routing_service = RealTimeRoutingService()
        route_data = await routing_service.calculate_optimized_route(
            request.start_location,
            request.waypoints,
            request.vehicle_type
        )
        return {
            "success": True,
            "route": route_data,
            "optimization_applied": request.optimize,
            "total_waypoints": len(request.waypoints)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route calculation failed: {str(e)}")

@router.get("/driver/{driver_id}/current")
async def get_driver_current_route(driver_id: str):
    from main import drivers_db, orders_db
    
    try:
        driver = next((d for d in drivers_db if d["id"] == driver_id), None)
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        active_orders = [o for o in orders_db if 
                        o.get("assigned_driver") == driver_id and 
                        o["status"] in ["assigned", "accepted", "picked_up", "in_transit"]]
        
        if not active_orders:
            return {"success": False, "message": "No active orders for driver"}
        
        optimizer = MultiPackageOptimizer()
        routing_service = RealTimeRoutingService()
        
        multi_route = optimizer.optimize_multi_delivery_route(
            driver["current_location"],
            active_orders
        )
        
        waypoints = []
        for point in multi_route["route"]:
            if point["type"] != "start":
                waypoints.append(point["location"])
        
        if waypoints:
            detailed_route = await routing_service.calculate_optimized_route(
                driver["current_location"],
                waypoints,
                driver["vehicle_type"]
            )
            
            detailed_route.update({
                "multi_package_optimization": {
                    "total_packages": len(active_orders),
                    "estimated_savings": multi_route["fuel_savings"],
                    "efficiency_score": multi_route["efficiency_score"],
                    "total_stops": len(multi_route["route"]) - 1
                },
                "waypoints": [
                    {
                        "lat": point["location"]["lat"],
                        "lng": point["location"]["lng"],
                        "type": point["type"],
                        "order_id": point.get("order_id"),
                        "address": point.get("order", {}).get("pickup_address" if point["type"] == "pickup" else "delivery_address", ""),
                        "contact": point.get("order", {}).get("sender_name" if point["type"] == "pickup" else "receiver_name", ""),
                        "phone": point.get("order", {}).get("sender_phone" if point["type"] == "pickup" else "receiver_phone", "")
                    }
                    for point in multi_route["route"] if point["type"] != "start"
                ]
            })
            
            return {
                "success": True,
                "route": detailed_route
            }
        
        return {"success": False, "message": "Could not generate route"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route generation failed: {str(e)}")

@router.post("/optimize/{driver_id}")
async def optimize_driver_route(driver_id: str):
    from main import drivers_db, orders_db
    
    try:
        driver = next((d for d in drivers_db if d["id"] == driver_id), None)
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        active_orders = [o for o in orders_db if 
                        o.get("assigned_driver") == driver_id and 
                        o["status"] in ["assigned", "accepted", "picked_up", "in_transit"]]
        
        if not active_orders:
            return {"success": False, "message": "No orders to optimize"}
        
        optimizer = MultiPackageOptimizer()
        routing_service = RealTimeRoutingService()
        
        current_route = optimizer.optimize_multi_delivery_route(
            driver["current_location"],
            active_orders
        )
        
        waypoints = [point["location"] for point in current_route["route"] if point["type"] != "start"]
        
        if waypoints:
            optimized_route = await routing_service.calculate_optimized_route(
                driver["current_location"],
                waypoints,
                driver["vehicle_type"]
            )
            
            return {
                "success": True,
                "optimization_results": {
                    "original_distance": current_route["total_distance"],
                    "optimized_distance": optimized_route["distance"] / 1000,
                    "original_time": current_route["total_time"],
                    "optimized_time": optimized_route["optimized_duration"] / 60,
                    "cost_savings": current_route["fuel_savings"],
                    "efficiency_improvement": current_route["efficiency_score"]
                },
                "route": optimized_route
            }
        
        return {"success": False, "message": "Could not optimize route"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route optimization failed: {str(e)}")