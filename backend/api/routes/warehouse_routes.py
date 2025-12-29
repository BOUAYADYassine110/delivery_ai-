from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Optional
from datetime import datetime
from core.database import get_database
from core.auth import get_current_user
from api.services.warehouse_management import WarehouseManagementService
from api.services.notification_service import NotificationService
from api.models.user import User

router = APIRouter(prefix="/api/warehouse", tags=["Warehouse Management"])

@router.post("/initialize")
async def initialize_warehouse_system(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Initialize warehouse system with default locations"""
    
    warehouse_service = WarehouseManagementService(db)
    await warehouse_service.initialize_warehouses()
    
    return {
        "status": "success",
        "message": "Warehouse system initialized",
        "warehouses": list(warehouse_service.warehouses.keys())
    }

@router.post("/route-package/{order_id}")
async def route_package_through_warehouses(
    order_id: str,
    route_data: Dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Route package through optimal warehouse chain"""
    
    warehouse_service = WarehouseManagementService(db)
    notification_service = NotificationService(db)
    
    # Get order details
    order = await db.orders.find_one({"_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    origin = route_data.get("origin")
    destination = route_data.get("destination")
    
    if not origin or not destination:
        raise HTTPException(status_code=400, detail="Origin and destination required")
    
    # Calculate warehouse route
    warehouse_route = await warehouse_service.route_package_to_warehouse(
        order_id, origin, destination
    )
    
    # Update order with warehouse route
    await db.orders.update_one(
        {"_id": order_id},
        {
            "$set": {
                "warehouse_route": warehouse_route,
                "status": "routed_to_warehouse",
                "updated_at": datetime.now()
            }
        }
    )
    
    # Send notification
    await notification_service.send_notification(
        str(order["customer_id"]),
        "warehouse_routing",
        {"order_id": order_id},
        {
            "total_warehouses": warehouse_route["total_warehouses"],
            "estimated_delivery": warehouse_route["estimated_delivery"].isoformat()
        }
    )
    
    return {
        "status": "success",
        "warehouse_route": warehouse_route,
        "message": "Package routed through warehouse system"
    }

@router.post("/package-arrival/{order_id}/{warehouse_id}")
async def handle_package_arrival(
    order_id: str,
    warehouse_id: str,
    arrival_data: Dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Handle package arrival at warehouse"""
    
    warehouse_service = WarehouseManagementService(db)
    
    # Process arrival
    result = await warehouse_service.package_arrived_at_warehouse(
        order_id, warehouse_id, arrival_data
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Update order status
    await db.orders.update_one(
        {"_id": order_id},
        {
            "$set": {
                "status": "at_warehouse",
                "current_warehouse": warehouse_id,
                "warehouse_arrival_time": datetime.now()
            }
        }
    )
    
    return {
        "status": "success",
        "message": "Package arrival processed",
        "warehouse_id": warehouse_id
    }

@router.get("/status/{warehouse_id}")
async def get_warehouse_status(
    warehouse_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get current warehouse status and capacity"""
    
    warehouse_service = WarehouseManagementService(db)
    status = await warehouse_service.get_warehouse_status(warehouse_id)
    
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    
    return status

@router.get("/package-history/{order_id}")
async def get_package_warehouse_history(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get warehouse history for a package"""
    
    warehouse_service = WarehouseManagementService(db)
    history = await warehouse_service.get_package_warehouse_history(order_id)
    
    return {
        "order_id": order_id,
        "warehouse_history": history
    }

@router.get("/all-warehouses")
async def get_all_warehouses(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get all warehouse locations and info"""
    
    warehouses = await db.warehouses.find({}).to_list(None)
    
    return {
        "warehouses": warehouses,
        "total_count": len(warehouses)
    }

@router.post("/simulate-processing/{order_id}/{warehouse_id}")
async def simulate_warehouse_processing(
    order_id: str,
    warehouse_id: str,
    processing_data: Dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Simulate warehouse processing (for testing)"""
    
    warehouse_service = WarehouseManagementService(db)
    
    # Check if warehouse exists
    if warehouse_id not in warehouse_service.warehouses:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Simulate processing time (reduced for demo)
    processing_time = processing_data.get("processing_hours", 0.1)  # 6 minutes for demo
    
    # Start processing
    background_tasks.add_task(
        simulate_processing_completion,
        order_id,
        warehouse_id,
        processing_time,
        db
    )
    
    return {
        "status": "success",
        "message": f"Processing started at warehouse {warehouse_id}",
        "estimated_completion": datetime.now().isoformat(),
        "processing_time_hours": processing_time
    }

@router.get("/analytics/performance")
async def get_warehouse_performance_analytics(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get warehouse performance analytics"""
    
    # Get warehouse events from last 30 days
    from datetime import timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    events = await db.warehouse_events.find(
        {"timestamp": {"$gte": thirty_days_ago}}
    ).to_list(None)
    
    # Calculate analytics
    analytics = calculate_warehouse_analytics(events)
    
    return {
        "period": "last_30_days",
        "analytics": analytics,
        "total_events": len(events)
    }

async def simulate_processing_completion(order_id: str, warehouse_id: str, 
                                       processing_hours: float, db):
    """Simulate warehouse processing completion"""
    
    import asyncio
    
    # Wait for processing time (converted to seconds)
    await asyncio.sleep(processing_hours * 3600)
    
    # Update order status
    await db.orders.update_one(
        {"_id": order_id},
        {
            "$set": {
                "status": "processed_at_warehouse",
                "warehouse_processing_completed": datetime.now()
            }
        }
    )
    
    # Create completion event
    await db.warehouse_events.insert_one({
        "order_id": order_id,
        "event_type": "processing_completed",
        "warehouse_id": warehouse_id,
        "timestamp": datetime.now(),
        "details": {"processing_duration_hours": processing_hours}
    })
    
    # Notify customer
    from core.websocket import manager
    await manager.broadcast({
        "type": "warehouse_processing_completed",
        "order_id": order_id,
        "warehouse_id": warehouse_id,
        "message": "Package processing completed at warehouse",
        "timestamp": datetime.now().isoformat()
    })

def calculate_warehouse_analytics(events: List[Dict]) -> Dict:
    """Calculate warehouse performance analytics"""
    
    if not events:
        return {}
    
    # Group events by warehouse
    warehouse_stats = {}
    
    for event in events:
        warehouse_id = event.get("warehouse_id")
        if not warehouse_id:
            continue
            
        if warehouse_id not in warehouse_stats:
            warehouse_stats[warehouse_id] = {
                "total_packages": 0,
                "arrivals": 0,
                "departures": 0,
                "processing_times": []
            }
        
        stats = warehouse_stats[warehouse_id]
        
        if event["event_type"] == "package_arrived":
            stats["arrivals"] += 1
            stats["total_packages"] += 1
        elif event["event_type"] == "dispatched_to_next_warehouse":
            stats["departures"] += 1
        elif event["event_type"] == "processing_completed":
            processing_time = event.get("details", {}).get("processing_duration_hours", 0)
            if processing_time:
                stats["processing_times"].append(processing_time)
    
    # Calculate averages
    for warehouse_id, stats in warehouse_stats.items():
        if stats["processing_times"]:
            stats["avg_processing_time"] = sum(stats["processing_times"]) / len(stats["processing_times"])
        else:
            stats["avg_processing_time"] = 0
        
        stats["throughput"] = stats["departures"]
        stats["efficiency"] = (stats["departures"] / max(stats["arrivals"], 1)) * 100
    
    return warehouse_stats