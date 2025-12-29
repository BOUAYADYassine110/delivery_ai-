from fastapi import APIRouter
from api.services.smart_assignment import SmartAssignmentService

router = APIRouter()

@router.get("/debug/assignment/{order_id}")
async def debug_assignment(order_id: str):
    """Debug assignment process for an order"""
    from main import orders_db, drivers_db
    
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    
    assignment_service = SmartAssignmentService()
    
    # Get weather
    weather = await assignment_service.get_weather_conditions(order["pickup_city"])
    
    # Check all drivers
    driver_analysis = []
    for driver in drivers_db:
        is_suitable = assignment_service.is_driver_suitable(driver, order, weather)
        
        if is_suitable:
            score = await assignment_service.calculate_driver_score(
                driver, order, 
                assignment_service.get_city_coordinates(order["pickup_city"]), 
                weather
            )
        else:
            score = 0
        
        driver_analysis.append({
            "driver": driver,
            "suitable": is_suitable,
            "score": score,
            "reasons": get_unsuitability_reasons(driver, order, weather, assignment_service)
        })
    
    # Sort by score
    driver_analysis.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "order": order,
        "weather": weather,
        "driver_analysis": driver_analysis,
        "best_driver": driver_analysis[0] if driver_analysis else None
    }

def get_unsuitability_reasons(driver, order, weather, service):
    """Get reasons why driver might not be suitable"""
    reasons = []
    
    vehicle_type = driver.get("vehicle_type", "bike")
    
    if weather.get("is_stormy") and vehicle_type in ["bike", "scooter"]:
        reasons.append("Vehicle not suitable for storm conditions")
    
    if driver.get("status") not in ["available", "online"]:
        reasons.append(f"Driver status: {driver.get('status')}")
    
    current_load = sum([service.get_order_weight(oid) for oid in driver.get("current_orders", [])])
    if current_load + order.get("weight", 1) > driver.get("vehicle_capacity", 50):
        reasons.append(f"Capacity exceeded: {current_load + order.get('weight', 1)} > {driver.get('vehicle_capacity', 50)}")
    
    max_orders = {"bike": 5, "scooter": 6, "car": 8, "van": 10}.get(vehicle_type, 5)
    if len(driver.get("current_orders", [])) >= max_orders:
        reasons.append(f"Too many orders: {len(driver.get('current_orders', []))} >= {max_orders}")
    
    return reasons if reasons else ["Suitable"]

@router.post("/debug/force-assign/{order_id}/{driver_id}")
async def force_assign_debug(order_id: str, driver_id: str):
    """Force assign order to driver for debugging"""
    from main import orders_db, drivers_db
    
    order = next((o for o in orders_db if o["id"] == order_id), None)
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    
    if not order or not driver:
        return {"error": "Order or driver not found"}
    
    # Force assignment
    order["assigned_driver"] = driver_id
    order["status"] = "assigned"
    
    if order_id not in driver["current_orders"]:
        driver["current_orders"].append(order_id)
    
    return {
        "success": True,
        "message": f"Force assigned order {order_id} to driver {driver['name']}",
        "order": order,
        "driver": driver
    }