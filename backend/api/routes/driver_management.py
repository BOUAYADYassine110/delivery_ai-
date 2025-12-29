from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

router = APIRouter()

class DriverStatusUpdate(BaseModel):
    driver_id: str
    status: str  # available, busy, offline, break
    location: Optional[dict] = None

class AssignmentResponse(BaseModel):
    driver_id: str
    order_id: str
    accepted: bool
    reason: Optional[str] = None
    estimated_pickup_time: Optional[str] = None

class DeliveryMilestone(BaseModel):
    driver_id: str
    order_id: str
    milestone: str  # picked_up, in_transit, delivered, failed
    location: dict
    notes: Optional[str] = None
    proof_photo: Optional[str] = None

# In-memory storage (replace with database)
driver_assignments = {}
assignment_history = []

@router.post("/driver/status/update")
async def update_driver_status(status_update: DriverStatusUpdate):
    """Update driver availability status"""
    from main import drivers_db
    
    driver = next((d for d in drivers_db if d["id"] == status_update.driver_id), None)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    # Update driver status
    driver["status"] = status_update.status
    driver["last_status_update"] = datetime.now().isoformat()
    
    if status_update.location:
        driver["current_location"].update(status_update.location)
    
    # Log status change
    status_log = {
        "driver_id": status_update.driver_id,
        "old_status": driver.get("previous_status", "unknown"),
        "new_status": status_update.status,
        "timestamp": datetime.now().isoformat(),
        "location": status_update.location
    }
    
    driver["previous_status"] = driver["status"]
    
    return {
        "success": True,
        "message": f"Driver status updated to {status_update.status}",
        "driver": driver,
        "status_log": status_log
    }

@router.post("/driver/assignment/respond")
async def respond_to_assignment(response: AssignmentResponse):
    """Driver responds to delivery assignment"""
    from main import orders_db, drivers_db
    from api.services.smart_assignment import SmartAssignmentService
    
    order = next((o for o in orders_db if o["id"] == response.order_id), None)
    driver = next((d for d in drivers_db if d["id"] == response.driver_id), None)
    
    if not order or not driver:
        raise HTTPException(status_code=404, detail="Order or driver not found")
    
    # Record response
    response_record = {
        "driver_id": response.driver_id,
        "order_id": response.order_id,
        "accepted": response.accepted,
        "reason": response.reason,
        "timestamp": datetime.now().isoformat(),
        "estimated_pickup_time": response.estimated_pickup_time
    }
    
    assignment_history.append(response_record)
    
    if response.accepted:
        # Accept assignment
        order["status"] = "accepted"
        order["assigned_driver"] = response.driver_id
        order["accepted_at"] = datetime.now().isoformat()
        order["estimated_pickup_time"] = response.estimated_pickup_time
        
        if response.order_id not in driver["current_orders"]:
            driver["current_orders"].append(response.order_id)
        
        driver["status"] = "busy"
        
        return {
            "success": True,
            "message": "Assignment accepted",
            "order": order,
            "next_action": "proceed_to_pickup"
        }
    else:
        # Reject assignment - find another driver
        assignment_service = SmartAssignmentService()
        
        # Get list of drivers who already rejected this order
        rejected_drivers = [
            h["driver_id"] for h in assignment_history 
            if h["order_id"] == response.order_id and not h["accepted"]
        ]
        
        next_driver = await assignment_service.reassign_order(order, rejected_drivers)
        
        if next_driver:
            order["assigned_driver"] = next_driver["id"]
            order["status"] = "pending_acceptance"
            order["assignment_attempts"] = order.get("assignment_attempts", 0) + 1
            
            return {
                "success": True,
                "message": f"Order reassigned to {next_driver['name']}",
                "new_driver": next_driver,
                "assignment_attempts": order["assignment_attempts"]
            }
        else:
            order["status"] = "pending_assignment"
            order["assigned_driver"] = None
            
            return {
                "success": True,
                "message": "No available drivers found",
                "order_status": "pending_assignment"
            }

@router.post("/driver/milestone/update")
async def update_delivery_milestone(milestone: DeliveryMilestone):
    """Update delivery milestone (pickup, transit, delivery)"""
    from main import orders_db, drivers_db
    
    order = next((o for o in orders_db if o["id"] == milestone.order_id), None)
    driver = next((d for d in drivers_db if d["id"] == milestone.driver_id), None)
    
    if not order or not driver:
        raise HTTPException(status_code=404, detail="Order or driver not found")
    
    # Update order status
    order["status"] = milestone.milestone
    order[f"{milestone.milestone}_at"] = datetime.now().isoformat()
    order[f"{milestone.milestone}_location"] = milestone.location
    
    if milestone.notes:
        order[f"{milestone.milestone}_notes"] = milestone.notes
    
    if milestone.proof_photo:
        order[f"{milestone.milestone}_proof"] = milestone.proof_photo
    
    # Update current location
    order["current_location"] = {
        "lat": milestone.location["lat"],
        "lng": milestone.location["lng"],
        "timestamp": datetime.now().isoformat()
    }
    
    # Handle milestone-specific logic
    if milestone.milestone == "picked_up":
        order["pickup_confirmed"] = True
        # Send notification to customer
        
    elif milestone.milestone == "delivered":
        # Complete delivery
        order["delivery_confirmed"] = True
        
        # Remove from driver's current orders
        if milestone.order_id in driver["current_orders"]:
            driver["current_orders"].remove(milestone.order_id)
            driver["total_deliveries"] += 1
        
        # Update driver status if no more orders
        if not driver["current_orders"]:
            driver["status"] = "available"
    
    elif milestone.milestone == "failed":
        order["failure_reason"] = milestone.notes
        # Reassign or return to warehouse
    
    return {
        "success": True,
        "message": f"Milestone {milestone.milestone} updated",
        "order": order,
        "driver": driver
    }

@router.get("/driver/{driver_id}/assignments")
async def get_driver_assignments(driver_id: str):
    """Get current and pending assignments for driver"""
    from main import orders_db
    
    # Current orders
    current_orders = [
        o for o in orders_db 
        if o.get("assigned_driver") == driver_id and 
        o["status"] in ["accepted", "picked_up", "in_transit"]
    ]
    
    # Pending assignments
    pending_assignments = [
        o for o in orders_db 
        if o.get("assigned_driver") == driver_id and 
        o["status"] == "pending_acceptance"
    ]
    
    # Assignment history
    driver_history = [
        h for h in assignment_history 
        if h["driver_id"] == driver_id
    ]
    
    return {
        "driver_id": driver_id,
        "current_orders": current_orders,
        "pending_assignments": pending_assignments,
        "assignment_history": driver_history[-10:],  # Last 10
        "total_current": len(current_orders),
        "total_pending": len(pending_assignments)
    }

@router.get("/admin/assignments/overview")
async def get_assignments_overview():
    """Admin overview of all assignments and driver statuses"""
    from main import orders_db, drivers_db
    
    # Orders by status
    orders_by_status = {}
    for order in orders_db:
        status = order["status"]
        if status not in orders_by_status:
            orders_by_status[status] = []
        orders_by_status[status].append(order)
    
    # Drivers by status
    drivers_by_status = {}
    for driver in drivers_db:
        status = driver["status"]
        if status not in drivers_by_status:
            drivers_by_status[status] = []
        drivers_by_status[status].append(driver)
    
    # Recent assignment activity
    recent_assignments = assignment_history[-20:]  # Last 20 assignments
    
    # Problem orders (multiple rejections)
    problem_orders = []
    for order in orders_db:
        rejections = len([
            h for h in assignment_history 
            if h["order_id"] == order["id"] and not h["accepted"]
        ])
        if rejections >= 2:
            problem_orders.append({
                "order": order,
                "rejection_count": rejections
            })
    
    return {
        "orders_by_status": orders_by_status,
        "drivers_by_status": drivers_by_status,
        "recent_assignments": recent_assignments,
        "problem_orders": problem_orders,
        "total_active_orders": len([o for o in orders_db if o["status"] in ["accepted", "picked_up", "in_transit"]]),
        "available_drivers": len([d for d in drivers_db if d["status"] == "available"])
    }

@router.post("/admin/assignment/force")
async def force_assignment(order_id: str, driver_id: str):
    """Admin force assignment of order to specific driver"""
    from main import orders_db, drivers_db
    
    order = next((o for o in orders_db if o["id"] == order_id), None)
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    
    if not order or not driver:
        raise HTTPException(status_code=404, detail="Order or driver not found")
    
    # Force assignment
    order["assigned_driver"] = driver_id
    order["status"] = "accepted"  # Skip acceptance step
    order["force_assigned"] = True
    order["force_assigned_at"] = datetime.now().isoformat()
    
    if order_id not in driver["current_orders"]:
        driver["current_orders"].append(order_id)
    
    driver["status"] = "busy"
    
    # Log force assignment
    assignment_history.append({
        "driver_id": driver_id,
        "order_id": order_id,
        "accepted": True,
        "reason": "Force assigned by admin",
        "timestamp": datetime.now().isoformat(),
        "force_assigned": True
    })
    
    return {
        "success": True,
        "message": f"Order force assigned to {driver['name']}",
        "order": order,
        "driver": driver
    }