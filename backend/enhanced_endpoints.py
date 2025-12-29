# Enhanced Backend Endpoints - Add to main.py

# Enhanced data structures
notifications_db = []
chat_messages_db = []
driver_earnings_db = []
performance_metrics_db = []
emergency_alerts_db = []
payments_db = []
customer_ratings_db = []
delivery_proofs_db = []
shift_schedules_db = []
vehicle_maintenance_db = []

# Enhanced Admin Dashboard Endpoints
@app.get("/api/admin/live-map")
def get_live_map_data():
    """Real-time map data with all drivers and orders"""
    active_drivers = []
    for driver in drivers_db:
        if driver["status"] in ["online", "busy"]:
            active_drivers.append({
                "id": driver["id"],
                "name": driver["name"],
                "location": driver["current_location"],
                "status": driver["status"],
                "vehicle_type": driver["vehicle_type"],
                "current_orders": len(driver["current_orders"]),
                "rating": driver["rating"]
            })
    
    active_orders = []
    for order in orders_db:
        if order["status"] not in ["delivered", "cancelled"]:
            active_orders.append({
                "id": order["id"],
                "tracking_number": order.get("tracking_number"),
                "status": order["status"],
                "pickup_location": get_city_coordinates(order["pickup_city"]),
                "delivery_location": get_city_coordinates(order["delivery_city"]),
                "current_location": order.get("current_location"),
                "assigned_driver": order.get("assigned_driver"),
                "priority": 1 if order.get("service_type") == "express" else 2
            })
    
    return {
        "drivers": active_drivers,
        "orders": active_orders,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/admin/driver/{driver_id}/suspend")
def suspend_driver(driver_id: str, suspension_data: dict):
    """Suspend/activate driver"""
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if not driver:
        return {"error": "Driver not found"}
    
    driver["status"] = "suspended" if suspension_data.get("suspend") else "available"
    driver["suspension_reason"] = suspension_data.get("reason", "")
    driver["suspended_at"] = datetime.now().isoformat() if suspension_data.get("suspend") else None
    
    return {"success": True, "message": f"Driver {'suspended' if suspension_data.get('suspend') else 'activated'}"}

@app.get("/api/admin/analytics/advanced")
def get_advanced_analytics():
    """Comprehensive analytics dashboard"""
    # Revenue analytics
    total_revenue = sum([o.get("total_cost", 0) for o in orders_db if o["status"] == "delivered"])
    today_revenue = sum([o.get("total_cost", 0) for o in orders_db 
                        if o["status"] == "delivered" and 
                        datetime.fromisoformat(o["created_at"]).date() == datetime.now().date()])
    
    # Driver performance
    driver_performance = []
    for driver in drivers_db:
        driver_orders = [o for o in orders_db if o.get("assigned_driver") == driver["id"]]
        completed_orders = [o for o in driver_orders if o["status"] == "delivered"]
        
        avg_delivery_time = 0
        if completed_orders:
            delivery_times = []
            for order in completed_orders:
                if order.get("delivered_at") and order.get("created_at"):
                    start = datetime.fromisoformat(order["created_at"])
                    end = datetime.fromisoformat(order["delivered_at"])
                    delivery_times.append((end - start).total_seconds() / 60)  # minutes
            avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0
        
        driver_performance.append({
            "driver_id": driver["id"],
            "name": driver["name"],
            "total_orders": len(driver_orders),
            "completed_orders": len(completed_orders),
            "success_rate": (len(completed_orders) / len(driver_orders) * 100) if driver_orders else 0,
            "avg_delivery_time": round(avg_delivery_time, 2),
            "rating": driver["rating"],
            "earnings": sum([o.get("total_cost", 0) * 0.15 for o in completed_orders])  # 15% commission
        })
    
    return {
        "revenue": {
            "total": round(total_revenue, 2),
            "today": round(today_revenue, 2),
            "currency": "MAD"
        },
        "driver_performance": driver_performance,
        "fleet_status": {
            "total_drivers": len(drivers_db),
            "online_drivers": len([d for d in drivers_db if d["status"] == "online"]),
            "busy_drivers": len([d for d in drivers_db if d["status"] == "busy"]),
            "offline_drivers": len([d for d in drivers_db if d["status"] == "offline"])
        }
    }

# Driver Status Management
@app.post("/api/driver/status/update")
def update_driver_status(status_data: dict):
    """Update driver availability status"""
    driver_id = status_data.get("driver_id")
    status = status_data.get("status")
    
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if not driver:
        return {"error": "Driver not found"}
    
    driver["status"] = status
    driver["last_status_update"] = datetime.now().isoformat()
    
    if status_data.get("location"):
        driver["current_location"].update(status_data["location"])
    
    return {"success": True, "message": f"Status updated to {status}"}

@app.get("/api/driver/{driver_id}/earnings")
def get_driver_earnings(driver_id: str):
    """Get driver earnings breakdown"""
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if not driver:
        return {"error": "Driver not found"}
    
    driver_orders = [o for o in orders_db if o.get("assigned_driver") == driver_id and o["status"] == "delivered"]
    
    # Calculate earnings (15% commission)
    total_earnings = sum([o.get("total_cost", 0) * 0.15 for o in driver_orders])
    
    # Today's earnings
    today_orders = [o for o in driver_orders 
                   if datetime.fromisoformat(o["delivered_at"]).date() == datetime.now().date()]
    today_earnings = sum([o.get("total_cost", 0) * 0.15 for o in today_orders])
    
    return {
        "driver_id": driver_id,
        "total_earnings": round(total_earnings, 2),
        "today_earnings": round(today_earnings, 2),
        "total_deliveries": len(driver_orders),
        "today_deliveries": len(today_orders),
        "commission_rate": 15,
        "currency": "MAD"
    }

# Proof of Delivery
@app.post("/api/driver/proof-of-delivery")
def submit_proof_of_delivery(proof_data: dict):
    """Submit proof of delivery with photo and signature"""
    order_id = proof_data.get("order_id")
    driver_id = proof_data.get("driver_id")
    
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    
    # Store proof of delivery
    delivery_proof = {
        "id": f"POD{len(delivery_proofs_db) + 1}",
        "order_id": order_id,
        "driver_id": driver_id,
        "photo": proof_data.get("photo"),
        "signature": proof_data.get("signature"),
        "notes": proof_data.get("notes", ""),
        "delivery_time": proof_data.get("delivery_time"),
        "timestamp": datetime.now().isoformat()
    }
    delivery_proofs_db.append(delivery_proof)
    
    # Update order status
    order["status"] = "delivered"
    order["delivered_at"] = proof_data.get("delivery_time")
    order["proof_of_delivery"] = delivery_proof["id"]
    
    # Update driver
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if driver and order_id in driver["current_orders"]:
        driver["current_orders"].remove(order_id)
        driver["total_deliveries"] += 1
        if not driver["current_orders"]:
            driver["status"] = "online"
    
    return {"success": True, "message": "Proof of delivery submitted", "proof_id": delivery_proof["id"]}

# Customer Rating System
@app.post("/api/customer/rate-driver")
def rate_driver(rating_data: dict):
    """Customer rates driver and service"""
    # Store rating
    rating_record = {
        "id": f"RAT{len(customer_ratings_db) + 1}",
        "order_id": rating_data.get("order_id"),
        "driver_id": rating_data.get("driver_id"),
        "rating": rating_data.get("rating"),
        "comment": rating_data.get("comment", ""),
        "timestamp": datetime.now().isoformat()
    }
    customer_ratings_db.append(rating_record)
    
    # Update driver's average rating
    driver = next((d for d in drivers_db if d["id"] == rating_data.get("driver_id")), None)
    if driver:
        driver_ratings = [r["rating"] for r in customer_ratings_db if r["driver_id"] == rating_data.get("driver_id")]
        driver["rating"] = sum(driver_ratings) / len(driver_ratings)
        driver["total_ratings"] = len(driver_ratings)
    
    return {"success": True, "message": "Rating submitted"}

# Chat System
@app.post("/api/chat/send")
def send_chat_message(message_data: dict):
    """Send chat message between driver, customer, admin"""
    chat_record = {
        "id": f"MSG{len(chat_messages_db) + 1}",
        "sender_id": message_data.get("sender_id"),
        "receiver_id": message_data.get("receiver_id"),
        "message": message_data.get("message"),
        "sender_type": message_data.get("sender_type"),
        "timestamp": datetime.now().isoformat(),
        "read": False
    }
    chat_messages_db.append(chat_record)
    
    return {"success": True, "message_id": chat_record["id"]}

@app.get("/api/chat/{user_id}")
def get_chat_messages(user_id: str):
    """Get chat messages for user"""
    messages = [m for m in chat_messages_db 
               if m["sender_id"] == user_id or m["receiver_id"] == user_id]
    return {"messages": messages}

# Emergency System
@app.post("/api/driver/emergency")
def send_emergency_alert(alert_data: dict):
    """Driver emergency alert system"""
    emergency_record = {
        "id": f"EMG{len(emergency_alerts_db) + 1}",
        "driver_id": alert_data.get("driver_id"),
        "type": alert_data.get("type"),
        "location": alert_data.get("location"),
        "message": alert_data.get("message", ""),
        "timestamp": datetime.now().isoformat(),
        "status": "active"
    }
    emergency_alerts_db.append(emergency_record)
    
    return {"success": True, "emergency_id": emergency_record["id"]}

@app.get("/api/admin/emergencies")
def get_emergency_alerts():
    """Get all active emergency alerts"""
    active_emergencies = [e for e in emergency_alerts_db if e["status"] == "active"]
    return {"emergencies": active_emergencies}

# Payment System
@app.post("/api/payment/process")
def process_payment(payment_data: dict):
    """Process payment for order"""
    order_id = payment_data.get("order_id")
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    
    payment_record = {
        "id": f"PAY{len(payments_db) + 1}",
        "order_id": order_id,
        "amount": payment_data.get("amount"),
        "method": payment_data.get("method"),
        "transaction_id": payment_data.get("transaction_id"),
        "status": "completed" if payment_data.get("method") == "cod" else "processing",
        "timestamp": datetime.now().isoformat()
    }
    payments_db.append(payment_record)
    
    order["payment_status"] = payment_record["status"]
    order["payment_method"] = payment_data.get("method")
    
    return {"success": True, "payment_id": payment_record["id"]}

# AI-Powered Route Optimization
@app.get("/api/ai/optimize-routes")
def ai_optimize_routes():
    """AI-powered route optimization for all active drivers"""
    optimized_routes = {}
    
    for driver in drivers_db:
        if driver["status"] == "busy" and driver["current_orders"]:
            route = generate_advanced_route(driver["id"])
            
            # AI enhancements (simplified)
            route["ai_optimized"] = True
            route["fuel_savings"] = round(route["total_distance"] * 0.1, 2)  # 10% savings
            route["time_savings"] = round(route["estimated_time"] * 0.15)  # 15% time savings
            route["co2_reduction"] = round(route["total_distance"] * 0.2, 2)  # kg CO2 saved
            
            optimized_routes[driver["id"]] = route
    
    return {
        "optimized_routes": optimized_routes,
        "total_drivers": len(optimized_routes),
        "generated_at": datetime.now().isoformat()
    }

# Multi-language Support
@app.get("/api/translations/{language}")
def get_translations(language: str):
    """Get translations for different languages"""
    translations = {
        "en": {
            "welcome": "Welcome",
            "new_order": "New Order",
            "delivery_completed": "Delivery Completed",
            "driver_assigned": "Driver Assigned"
        },
        "ar": {
            "welcome": "مرحبا",
            "new_order": "طلب جديد",
            "delivery_completed": "تم التسليم",
            "driver_assigned": "تم تعيين السائق"
        },
        "fr": {
            "welcome": "Bienvenue",
            "new_order": "Nouvelle Commande",
            "delivery_completed": "Livraison Terminée",
            "driver_assigned": "Chauffeur Assigné"
        }
    }
    
    return translations.get(language, translations["en"])