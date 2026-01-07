"""
Add this endpoint to main.py to manually assign drivers to orders loaded from database
"""

@app.post("/api/orders/{order_id}/assign-driver")
async def assign_driver_to_order(order_id: str):
    """Manually assign driver to an existing order"""
    refresh_data()
    
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    
    if order.get("assigned_driver"):
        return {"message": "Order already has a driver assigned", "order": order}
    
    # Get available drivers in the pickup city
    city_drivers = [d for d in drivers_db if 
                   d.get("status") in ["available", "online"] and 
                   d.get("assigned_city", "").lower() == order["pickup_city"].lower()]
    
    if not city_drivers:
        return {"error": f"No available drivers in {order['pickup_city']}"}
    
    # Use smart assignment
    from api.services.smart_assignment import SmartAssignmentService
    assignment_service = SmartAssignmentService()
    
    best_driver = await assignment_service.find_best_driver(order, city_drivers)
    
    if best_driver:
        order["assigned_driver"] = best_driver["id"]
        order["status"] = "assigned"
        best_driver["current_orders"].append(order_id)
        best_driver["status"] = "busy"
        
        # Save changes
        storage.update_order(order_id, order)
        storage.update_driver(best_driver["id"], best_driver)
        
        # Start simulation
        from api.services.delivery_simulator import simulator
        simulator.start_simulation(order_id, order, orders_db)
        
        return {
            "message": "Driver assigned successfully",
            "order": clean_mongo_doc(order) if USE_MONGODB else order,
            "driver": best_driver["name"]
        }
    
    return {"error": "No suitable driver found"}
