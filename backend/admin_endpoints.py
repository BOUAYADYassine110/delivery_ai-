from fastapi import HTTPException
from datetime import datetime
import asyncio
import json

# Admin endpoints to be added to main.py

# Admin login endpoint
def admin_login_endpoint(request):
    if request.username == "admin" and request.password == "admin123":
        return {
            "access_token": "admin-token-123",
            "token_type": "bearer",
            "admin": {
                "id": "admin1",
                "username": "admin",
                "role": "admin",
                "permissions": ["view_orders", "manage_drivers", "view_analytics"]
            }
        }
    return {"detail": "Invalid admin credentials"}

# Admin orders endpoint
def get_all_orders_endpoint(orders_db):
    return {"orders": orders_db, "total": len(orders_db)}

# Admin drivers endpoint
def get_all_drivers_endpoint(drivers_db):
    return {"drivers": drivers_db, "total": len(drivers_db)}

# Admin analytics endpoint
def get_admin_analytics_endpoint(orders_db, drivers_db):
    total_orders = len(orders_db)
    pending_orders = len([o for o in orders_db if o["status"] in ["pending_assignment", "pending_acceptance"]])
    in_progress = len([o for o in orders_db if o["status"] in ["picked_up", "in_transit", "assigned"]])
    completed = len([o for o in orders_db if o["status"] == "delivered"])
    active_drivers = len([d for d in drivers_db if d["status"] in ["available", "busy"]])
    
    return {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "in_progress": in_progress,
        "completed": completed,
        "active_drivers": active_drivers,
        "revenue": sum([o["total_cost"] for o in orders_db if o["status"] == "delivered"])
    }

# Driver assignment response endpoint
def driver_assignment_response_endpoint(response, orders_db, drivers_db, manager):
    order = next((o for o in orders_db if o["id"] == response.order_id), None)
    driver = next((d for d in drivers_db if d["id"] == response.driver_id), None)
    
    if not order or not driver:
        raise HTTPException(status_code=404, detail="Order or driver not found")
    
    if response.accept:
        order["status"] = "accepted"
        order["accepted_at"] = datetime.now().isoformat()
        driver["current_orders"].append(response.order_id)
        driver["status"] = "busy"
        
        asyncio.create_task(manager.send_to_user({
            "type": "order_accepted",
            "order_id": response.order_id,
            "driver_name": driver["name"],
            "driver_phone": driver["phone"]
        }, order.get("sender_phone", "user1")))
        
        asyncio.create_task(manager.send_to_admin({
            "type": "assignment_accepted",
            "order_id": response.order_id,
            "driver_id": response.driver_id
        }))
        
        return {"success": True, "message": "Assignment accepted"}
    else:
        order["status"] = "pending_assignment"
        order["assigned_driver"] = None
        return {"success": True, "message": "Assignment rejected, finding new driver"}

# GPS tracking endpoint
def update_driver_gps_endpoint(gps_data, orders_db, drivers_db, manager):
    driver = next((d for d in drivers_db if d["id"] == gps_data.driver_id), None)
    order = next((o for o in orders_db if o["id"] == gps_data.order_id), None)
    
    if not driver or not order:
        raise HTTPException(status_code=404, detail="Driver or order not found")
    
    driver["current_location"].update({
        "lat": gps_data.latitude,
        "lng": gps_data.longitude,
        "last_update": gps_data.timestamp or datetime.now().isoformat()
    })
    
    order["current_location"] = {
        "lat": gps_data.latitude,
        "lng": gps_data.longitude,
        "timestamp": gps_data.timestamp or datetime.now().isoformat()
    }
    
    if "route_history" not in order:
        order["route_history"] = []
    order["route_history"].append({
        "lat": gps_data.latitude,
        "lng": gps_data.longitude,
        "timestamp": gps_data.timestamp or datetime.now().isoformat()
    })
    
    asyncio.create_task(manager.send_to_user({
        "type": "location_update",
        "order_id": gps_data.order_id,
        "latitude": gps_data.latitude,
        "longitude": gps_data.longitude,
        "driver_name": driver["name"]
    }, order.get("sender_phone", "user1")))
    
    asyncio.create_task(manager.send_to_admin({
        "type": "driver_location",
        "driver_id": gps_data.driver_id,
        "order_id": gps_data.order_id,
        "location": {"lat": gps_data.latitude, "lng": gps_data.longitude}
    }))
    
    return {"success": True, "message": "GPS location updated"}

# Start delivery endpoint
def start_delivery_route_endpoint(order_id, driver_id, orders_db, drivers_db, manager):
    order = next((o for o in orders_db if o["id"] == order_id), None)
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    
    if not order or not driver:
        raise HTTPException(status_code=404, detail="Order or driver not found")
    
    order["status"] = "in_transit"
    order["started_at"] = datetime.now().isoformat()
    
    asyncio.create_task(manager.send_to_user({
        "type": "delivery_started",
        "order_id": order_id,
        "driver_name": driver["name"],
        "estimated_arrival": order["estimated_delivery"]
    }, order.get("receiver_phone", "user1")))
    
    asyncio.create_task(manager.send_to_admin({
        "type": "delivery_started",
        "order_id": order_id,
        "driver_id": driver_id
    }))
    
    return {"success": True, "message": "Delivery started"}

# Complete delivery endpoint
def complete_delivery_final_endpoint(completion_data, orders_db, drivers_db, manager):
    order_id = completion_data.get("order_id")
    driver_id = completion_data.get("driver_id")
    notes = completion_data.get("notes", "")
    proof_photo = completion_data.get("proof_photo", "")
    
    order = next((o for o in orders_db if o["id"] == order_id), None)
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    
    if not order or not driver:
        raise HTTPException(status_code=404, detail="Order or driver not found")
    
    order["status"] = "delivered"
    order["delivered_at"] = datetime.now().isoformat()
    order["completion_notes"] = notes
    order["proof_photo"] = proof_photo
    
    if order_id in driver["current_orders"]:
        driver["current_orders"].remove(order_id)
        driver["total_deliveries"] += 1
        
        if not driver["current_orders"]:
            driver["status"] = "available"
    
    asyncio.create_task(manager.send_to_user({
        "type": "delivery_completed",
        "order_id": order_id,
        "message": "Your package has been delivered successfully!",
        "proof_photo": proof_photo
    }, order.get("receiver_phone", "user1")))
    
    asyncio.create_task(manager.send_to_admin({
        "type": "delivery_completed",
        "order_id": order_id,
        "driver_id": driver_id,
        "completion_time": order["delivered_at"]
    }))
    
    return {"success": True, "message": "Delivery completed successfully"}