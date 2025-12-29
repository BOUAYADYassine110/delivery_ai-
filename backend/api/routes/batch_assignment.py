from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from api.services.multi_package_optimizer import MultiPackageOptimizer

router = APIRouter(prefix="/api/batch", tags=["batch_assignment"])

class BatchAssignmentRequest(BaseModel):
    order_ids: List[str]
    driver_id: str = None  # Optional - if not provided, find best driver

class MultiOrderCreate(BaseModel):
    orders: List[dict]
    optimize_assignment: bool = True

@router.post("/assign-multiple")
async def assign_multiple_orders(request: BatchAssignmentRequest):
    """Assign multiple orders to optimal driver with route optimization"""
    from main import orders_db, drivers_db
    
    # Get orders
    orders = [o for o in orders_db if o["id"] in request.order_ids]
    if not orders:
        raise HTTPException(status_code=404, detail="No valid orders found")
    
    optimizer = MultiPackageOptimizer()
    
    if request.driver_id:
        # Assign to specific driver
        driver = next((d for d in drivers_db if d["id"] == request.driver_id), None)
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        # Check capacity
        current_load = len(driver["current_orders"])
        max_capacity = optimizer._get_max_capacity(driver["vehicle_type"])
        
        if current_load + len(orders) > max_capacity:
            raise HTTPException(status_code=400, detail=f"Exceeds driver capacity ({max_capacity})")
        
        # Assign orders
        for order in orders:
            order["assigned_driver"] = driver["id"]
            order["status"] = "assigned"
            driver["current_orders"].append(order["id"])
        
        # Generate optimized route
        route_data = optimizer.optimize_multi_delivery_route(
            driver["current_location"],
            [o for o in orders_db if o.get("assigned_driver") == driver["id"]]
        )
        
        return {
            "success": True,
            "assigned_driver": driver,
            "orders_assigned": len(orders),
            "route_optimization": route_data,
            "estimated_savings": route_data["fuel_savings"]
        }
    
    else:
        # Find best driver for batch
        best_driver = None
        best_score = 0
        
        available_drivers = [d for d in drivers_db if d["status"] in ["available", "busy"]]
        
        for driver in available_drivers:
            score = optimizer.calculate_batch_assignment_score(driver, orders)
            if score > best_score:
                best_score = score
                best_driver = driver
        
        if not best_driver:
            raise HTTPException(status_code=404, detail="No available drivers")
        
        # Assign to best driver
        for order in orders:
            order["assigned_driver"] = best_driver["id"]
            order["status"] = "assigned"
            best_driver["current_orders"].append(order["id"])
        
        best_driver["status"] = "busy"
        
        # Generate optimized route
        route_data = optimizer.optimize_multi_delivery_route(
            best_driver["current_location"],
            [o for o in orders_db if o.get("assigned_driver") == best_driver["id"]]
        )
        
        return {
            "success": True,
            "assigned_driver": best_driver,
            "orders_assigned": len(orders),
            "assignment_score": best_score,
            "route_optimization": route_data,
            "estimated_savings": route_data["fuel_savings"]
        }

@router.post("/create-optimized-batch")
async def create_optimized_batch(request: MultiOrderCreate):
    """Create multiple orders and assign them optimally"""
    from main import orders_db, drivers_db
    import random
    from datetime import datetime, timedelta
    
    created_orders = []
    
    # Create orders
    for order_data in request.orders:
        order_id = f"ORD{random.randint(1000, 9999)}"
        tracking_number = f"TRK{random.randint(100, 999)}"
        
        new_order = {
            "id": order_id,
            "tracking_number": tracking_number,
            "status": "pending_assignment",
            **order_data,
            "created_at": datetime.now().isoformat(),
            "assigned_driver": None
        }
        
        orders_db.append(new_order)
        created_orders.append(new_order)
    
    if request.optimize_assignment:
        # Find optimal driver assignment
        optimizer = MultiPackageOptimizer()
        best_driver = None
        best_score = 0
        
        available_drivers = [d for d in drivers_db if d["status"] in ["available", "busy"]]
        
        for driver in available_drivers:
            score = optimizer.calculate_batch_assignment_score(driver, created_orders)
            if score > best_score:
                best_score = score
                best_driver = driver
        
        if best_driver:
            # Assign all orders to best driver
            for order in created_orders:
                order["assigned_driver"] = best_driver["id"]
                order["status"] = "assigned"
                best_driver["current_orders"].append(order["id"])
            
            best_driver["status"] = "busy"
            
            # Generate optimized route
            route_data = optimizer.optimize_multi_delivery_route(
                best_driver["current_location"],
                [o for o in orders_db if o.get("assigned_driver") == best_driver["id"]]
            )
            
            return {
                "success": True,
                "orders_created": len(created_orders),
                "assigned_driver": best_driver,
                "route_optimization": route_data,
                "estimated_savings": route_data["fuel_savings"],
                "efficiency_score": route_data["efficiency_score"]
            }
    
    return {
        "success": True,
        "orders_created": len(created_orders),
        "orders": created_orders
    }

@router.get("/driver/{driver_id}/capacity")
async def get_driver_capacity(driver_id: str):
    """Get driver's current capacity and optimization potential"""
    from main import drivers_db, orders_db
    
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    optimizer = MultiPackageOptimizer()
    max_capacity = optimizer._get_max_capacity(driver["vehicle_type"])
    current_load = len(driver["current_orders"])
    
    # Get current route optimization
    current_orders = [o for o in orders_db if o.get("assigned_driver") == driver_id]
    route_data = optimizer.optimize_multi_delivery_route(
        driver["current_location"],
        current_orders
    ) if current_orders else None
    
    return {
        "driver_id": driver_id,
        "vehicle_type": driver["vehicle_type"],
        "max_capacity": max_capacity,
        "current_load": current_load,
        "available_slots": max_capacity - current_load,
        "utilization_percentage": round((current_load / max_capacity) * 100, 1),
        "current_route": route_data,
        "can_accept_more": current_load < max_capacity
    }

@router.post("/optimize-existing/{driver_id}")
async def optimize_existing_route(driver_id: str):
    """Re-optimize existing driver route for better efficiency"""
    from main import drivers_db, orders_db
    
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    current_orders = [o for o in orders_db if o.get("assigned_driver") == driver_id and 
                     o["status"] in ["assigned", "accepted", "picked_up", "in_transit"]]
    
    if not current_orders:
        return {"message": "No orders to optimize"}
    
    optimizer = MultiPackageOptimizer()
    
    # Get current route metrics
    old_route = optimizer.optimize_multi_delivery_route(driver["current_location"], current_orders)
    
    # Re-optimize (this will use improved algorithms)
    new_route = optimizer.optimize_multi_delivery_route(driver["current_location"], current_orders)
    
    savings = old_route["total_cost"] - new_route["total_cost"]
    time_saved = old_route["total_time"] - new_route["total_time"]
    
    return {
        "success": True,
        "driver_id": driver_id,
        "orders_optimized": len(current_orders),
        "old_metrics": {
            "distance": old_route["total_distance"],
            "time": old_route["total_time"],
            "cost": old_route["total_cost"]
        },
        "new_metrics": {
            "distance": new_route["total_distance"],
            "time": new_route["total_time"],
            "cost": new_route["total_cost"]
        },
        "improvements": {
            "cost_savings": round(savings, 2),
            "time_saved": round(time_saved, 1),
            "efficiency_gain": round(new_route["efficiency_score"] - old_route["efficiency_score"], 1)
        },
        "optimized_route": new_route
    }