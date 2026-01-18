# Admin API Routes - Complete Implementation
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel
from auth import get_current_admin

router = APIRouter()

# Pydantic Models
class OrderFilter(BaseModel):
    status: Optional[str] = None
    city: Optional[str] = None
    driver_id: Optional[str] = None
    service_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

class OrderReassign(BaseModel):
    order_id: str
    new_driver_id: str
    reason: str = ""

class DriverSuspend(BaseModel):
    suspend: bool
    reason: str = ""

# ============= DASHBOARD OVERVIEW =============
@router.get("/dashboard/overview")
def get_dashboard_overview(current_admin: dict = Depends(get_current_admin)):
    """Main dashboard statistics"""
    from main import orders_db, drivers_db, refresh_data
    refresh_data()
    
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Order statistics
    total_orders = len(orders_db)
    today_orders = len([o for o in orders_db if datetime.fromisoformat(o["created_at"]) >= today_start])
    active_orders = len([o for o in orders_db if o["status"] in ["assigned", "picked_up", "in_transit"]])
    completed_today = len([o for o in orders_db if o["status"] == "delivered" and 
                          o.get("delivered_at") and datetime.fromisoformat(o["delivered_at"]) >= today_start])
    
    # Revenue
    total_revenue = sum([o.get("total_cost", 0) for o in orders_db if o["status"] == "delivered"])
    today_revenue = sum([o.get("total_cost", 0) for o in orders_db 
                        if o["status"] == "delivered" and o.get("delivered_at") and
                        datetime.fromisoformat(o["delivered_at"]) >= today_start])
    
    # Driver statistics
    total_drivers = len(drivers_db)
    active_drivers = len([d for d in drivers_db if d["status"] in ["available", "busy"]])
    busy_drivers = len([d for d in drivers_db if d["status"] == "busy"])
    
    # Performance metrics
    completed_orders = [o for o in orders_db if o["status"] == "delivered"]
    avg_delivery_time = 0
    if completed_orders:
        times = []
        for o in completed_orders:
            if o.get("delivered_at") and o.get("created_at"):
                delta = datetime.fromisoformat(o["delivered_at"]) - datetime.fromisoformat(o["created_at"])
                times.append(delta.total_seconds() / 60)
        avg_delivery_time = sum(times) / len(times) if times else 0
    
    success_rate = (len(completed_orders) / total_orders * 100) if total_orders > 0 else 0
    
    return {
        "orders": {
            "total": total_orders,
            "today": today_orders,
            "active": active_orders,
            "completed_today": completed_today,
            "pending": len([o for o in orders_db if o["status"] == "pending_assignment"])
        },
        "revenue": {
            "total": round(total_revenue, 2),
            "today": round(today_revenue, 2),
            "currency": "MAD"
        },
        "drivers": {
            "total": total_drivers,
            "active": active_drivers,
            "busy": busy_drivers,
            "offline": total_drivers - active_drivers
        },
        "performance": {
            "avg_delivery_time_minutes": round(avg_delivery_time, 1),
            "success_rate": round(success_rate, 1),
            "customer_satisfaction": 4.7
        }
    }

# ============= LIVE MAP =============
@router.get("/live-map")
def get_live_map(current_admin: dict = Depends(get_current_admin)):
    """Real-time map data"""
    from main import drivers_db, orders_db, get_city_coordinates
    
    drivers = []
    for d in drivers_db:
        if d["status"] != "offline":
            drivers.append({
                "id": d["id"],
                "name": d["name"],
                "location": d["current_location"],
                "status": d["status"],
                "vehicle_type": d["vehicle_type"],
                "current_orders": d["current_orders"],
                "rating": d["rating"]
            })
    
    orders = []
    for o in orders_db:
        if o["status"] not in ["delivered", "cancelled"]:
            orders.append({
                "id": o["id"],
                "tracking_number": o.get("tracking_number"),
                "status": o["status"],
                "pickup_location": get_city_coordinates(o["pickup_city"]),
                "delivery_location": get_city_coordinates(o["delivery_city"]),
                "current_location": o.get("current_location"),
                "assigned_driver": o.get("assigned_driver"),
                "service_type": o.get("service_type")
            })
    
    return {"drivers": drivers, "orders": orders, "timestamp": datetime.now().isoformat()}

# ============= ORDER MANAGEMENT =============
@router.get("/orders")
def get_all_orders(
    status: Optional[str] = None,
    city: Optional[str] = None,
    driver_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_admin: dict = Depends(get_current_admin)
):
    """Get all orders with filters"""
    from main import orders_db, drivers_db, refresh_data
    refresh_data()
    
    filtered = orders_db.copy()
    
    # Apply filters
    if status:
        filtered = [o for o in filtered if o["status"] == status]
    if city:
        filtered = [o for o in filtered if o["pickup_city"].lower() == city.lower() or 
                   o["delivery_city"].lower() == city.lower()]
    if driver_id:
        filtered = [o for o in filtered if o.get("assigned_driver") == driver_id]
    if search:
        search_lower = search.lower()
        filtered = [o for o in filtered if 
                   search_lower in o.get("tracking_number", "").lower() or
                   search_lower in o.get("sender_name", "").lower() or
                   search_lower in o.get("receiver_name", "").lower()]
    
    # Sort by created_at desc
    filtered.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Pagination
    total = len(filtered)
    paginated = filtered[offset:offset + limit]
    
    # Enrich with driver info
    for order in paginated:
        if order.get("assigned_driver"):
            driver = next((d for d in drivers_db if d["id"] == order["assigned_driver"]), None)
            order["driver_info"] = {
                "name": driver["name"],
                "phone": driver["phone"],
                "vehicle_type": driver["vehicle_type"]
            } if driver else None
    
    return {"orders": paginated, "total": total, "limit": limit, "offset": offset}

@router.get("/orders/{order_id}")
def get_order_details(order_id: str, current_admin: dict = Depends(get_current_admin)):
    """Get detailed order information"""
    from main import orders_db, drivers_db
    
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get driver info
    driver_info = None
    if order.get("assigned_driver"):
        driver = next((d for d in drivers_db if d["id"] == order["assigned_driver"]), None)
        if driver:
            driver_info = {
                "id": driver["id"],
                "name": driver["name"],
                "phone": driver["phone"],
                "email": driver["email"],
                "vehicle_type": driver["vehicle_type"],
                "rating": driver["rating"],
                "current_location": driver["current_location"]
            }
    
    return {"order": order, "driver": driver_info}

@router.post("/orders/{order_id}/reassign")
async def reassign_order(order_id: str, data: OrderReassign, current_admin: dict = Depends(get_current_admin)):
    """Manually reassign order to different driver"""
    from main import orders_db, drivers_db, storage
    
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    new_driver = next((d for d in drivers_db if d["id"] == data.new_driver_id), None)
    if not new_driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    # Remove from old driver
    if order.get("assigned_driver"):
        old_driver = next((d for d in drivers_db if d["id"] == order["assigned_driver"]), None)
        if old_driver and order_id in old_driver["current_orders"]:
            old_driver["current_orders"].remove(order_id)
            if not old_driver["current_orders"]:
                old_driver["status"] = "available"
            storage.update_driver(old_driver["id"], old_driver)
    
    # Assign to new driver
    order["assigned_driver"] = data.new_driver_id
    order["status"] = "assigned"
    order["reassigned_at"] = datetime.now().isoformat()
    order["reassign_reason"] = data.reason
    
    if order_id not in new_driver["current_orders"]:
        new_driver["current_orders"].append(order_id)
    new_driver["status"] = "busy"
    
    storage.update_order(order_id, order)
    storage.update_driver(new_driver["id"], new_driver)
    
    return {"success": True, "message": f"Order reassigned to {new_driver['name']}"}

@router.post("/orders/{order_id}/cancel")
def cancel_order(order_id: str, reason: str = "", current_admin: dict = Depends(get_current_admin)):
    """Cancel an order"""
    from main import orders_db, drivers_db, storage
    
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Remove from driver
    if order.get("assigned_driver"):
        driver = next((d for d in drivers_db if d["id"] == order["assigned_driver"]), None)
        if driver and order_id in driver["current_orders"]:
            driver["current_orders"].remove(order_id)
            if not driver["current_orders"]:
                driver["status"] = "available"
            storage.update_driver(driver["id"], driver)
    
    order["status"] = "cancelled"
    order["cancelled_at"] = datetime.now().isoformat()
    order["cancel_reason"] = reason
    order["cancelled_by"] = "admin"
    
    storage.update_order(order_id, order)
    
    return {"success": True, "message": "Order cancelled"}

# ============= DRIVER MANAGEMENT =============
@router.get("/drivers")
def get_all_drivers(
    city: Optional[str] = None,
    status: Optional[str] = None,
    current_admin: dict = Depends(get_current_admin)
):
    """Get all drivers with filters"""
    from main import drivers_db, orders_db, refresh_data
    refresh_data()
    
    filtered = drivers_db.copy()
    
    if city:
        filtered = [d for d in filtered if d.get("assigned_city", "").lower() == city.lower()]
    if status:
        filtered = [d for d in filtered if d["status"] == status]
    
    # Enrich with current orders info
    for driver in filtered:
        driver_orders = [o for o in orders_db if o.get("assigned_driver") == driver["id"]]
        driver["stats"] = {
            "active_orders": len(driver["current_orders"]),
            "total_orders": len(driver_orders),
            "completed": len([o for o in driver_orders if o["status"] == "delivered"]),
            "success_rate": (len([o for o in driver_orders if o["status"] == "delivered"]) / 
                           len(driver_orders) * 100) if driver_orders else 0
        }
    
    return {"drivers": filtered, "total": len(filtered)}

@router.get("/drivers/{driver_id}")
def get_driver_details(driver_id: str, current_admin: dict = Depends(get_current_admin)):
    """Get detailed driver information"""
    from main import drivers_db, orders_db
    
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    # Get driver orders
    driver_orders = [o for o in orders_db if o.get("assigned_driver") == driver_id]
    completed = [o for o in driver_orders if o["status"] == "delivered"]
    
    # Calculate earnings
    earnings = sum([o.get("total_cost", 0) * 0.15 for o in completed])
    
    # Calculate average delivery time
    avg_time = 0
    if completed:
        times = []
        for o in completed:
            if o.get("delivered_at") and o.get("created_at"):
                delta = datetime.fromisoformat(o["delivered_at"]) - datetime.fromisoformat(o["created_at"])
                times.append(delta.total_seconds() / 60)
        avg_time = sum(times) / len(times) if times else 0
    
    return {
        "driver": driver,
        "statistics": {
            "total_orders": len(driver_orders),
            "completed_orders": len(completed),
            "active_orders": len(driver["current_orders"]),
            "success_rate": (len(completed) / len(driver_orders) * 100) if driver_orders else 0,
            "total_earnings": round(earnings, 2),
            "avg_delivery_time": round(avg_time, 1)
        },
        "recent_orders": sorted(driver_orders, key=lambda x: x["created_at"], reverse=True)[:10]
    }

@router.post("/drivers/{driver_id}/suspend")
def suspend_driver(driver_id: str, data: DriverSuspend, current_admin: dict = Depends(get_current_admin)):
    """Suspend or activate driver"""
    from main import drivers_db, storage
    
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    if data.suspend:
        driver["status"] = "suspended"
        driver["suspension_reason"] = data.reason
        driver["suspended_at"] = datetime.now().isoformat()
    else:
        driver["status"] = "available"
        driver["suspension_reason"] = None
        driver["suspended_at"] = None
    
    storage.update_driver(driver_id, driver)
    
    return {"success": True, "message": f"Driver {'suspended' if data.suspend else 'activated'}"}

# ============= ANALYTICS =============
@router.get("/analytics/revenue")
def get_revenue_analytics(
    period: str = "week",
    current_admin: dict = Depends(get_current_admin)
):
    """Revenue analytics by period"""
    from main import orders_db
    
    now = datetime.now()
    if period == "day":
        start = now.replace(hour=0, minute=0, second=0)
    elif period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now - timedelta(days=30)
    else:
        start = now - timedelta(days=7)
    
    completed = [o for o in orders_db if o["status"] == "delivered" and o.get("delivered_at")]
    period_orders = [o for o in completed if datetime.fromisoformat(o["delivered_at"]) >= start]
    
    total_revenue = sum([o.get("total_cost", 0) for o in period_orders])
    
    # Revenue by city
    by_city = {}
    for o in period_orders:
        city = o["pickup_city"]
        by_city[city] = by_city.get(city, 0) + o.get("total_cost", 0)
    
    # Revenue by service type
    by_service = {
        "standard": sum([o.get("total_cost", 0) for o in period_orders if o.get("service_type") == "standard"]),
        "express": sum([o.get("total_cost", 0) for o in period_orders if o.get("service_type") == "express"])
    }
    
    # Revenue by type
    by_type = {
        "intra_city": sum([o.get("total_cost", 0) for o in period_orders if not o.get("is_inter_city")]),
        "inter_city": sum([o.get("total_cost", 0) for o in period_orders if o.get("is_inter_city")])
    }
    
    return {
        "period": period,
        "total_revenue": round(total_revenue, 2),
        "total_orders": len(period_orders),
        "avg_order_value": round(total_revenue / len(period_orders), 2) if period_orders else 0,
        "by_city": {k: round(v, 2) for k, v in by_city.items()},
        "by_service_type": {k: round(v, 2) for k, v in by_service.items()},
        "by_order_type": {k: round(v, 2) for k, v in by_type.items()},
        "currency": "MAD"
    }

@router.get("/analytics/performance")
def get_performance_analytics(current_admin: dict = Depends(get_current_admin)):
    """System performance metrics"""
    from main import orders_db, drivers_db
    
    completed = [o for o in orders_db if o["status"] == "delivered"]
    
    # Delivery times
    delivery_times = []
    for o in completed:
        if o.get("delivered_at") and o.get("created_at"):
            delta = datetime.fromisoformat(o["delivered_at"]) - datetime.fromisoformat(o["created_at"])
            delivery_times.append(delta.total_seconds() / 60)
    
    avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0
    
    # Success rate
    total_orders = len(orders_db)
    success_rate = (len(completed) / total_orders * 100) if total_orders > 0 else 0
    
    # By city
    by_city = {}
    for city in ["Casablanca", "Rabat", "Marrakech", "Agadir", "El Jadida", "Salé"]:
        city_orders = [o for o in orders_db if o["pickup_city"] == city]
        city_completed = [o for o in city_orders if o["status"] == "delivered"]
        by_city[city] = {
            "total_orders": len(city_orders),
            "completed": len(city_completed),
            "success_rate": (len(city_completed) / len(city_orders) * 100) if city_orders else 0
        }
    
    # Driver utilization
    active_drivers = len([d for d in drivers_db if d["status"] in ["available", "busy"]])
    busy_drivers = len([d for d in drivers_db if d["status"] == "busy"])
    utilization = (busy_drivers / active_drivers * 100) if active_drivers > 0 else 0
    
    return {
        "avg_delivery_time_minutes": round(avg_delivery_time, 1),
        "success_rate": round(success_rate, 1),
        "total_deliveries": len(completed),
        "by_city": by_city,
        "driver_utilization": round(utilization, 1),
        "active_drivers": active_drivers
    }

@router.get("/analytics/advanced")
def get_advanced_analytics(current_admin: dict = Depends(get_current_admin)):
    """Advanced analytics with driver performance"""
    from main import orders_db, drivers_db
    
    # Revenue
    total_revenue = sum([o.get("total_cost", 0) for o in orders_db if o["status"] == "delivered"])
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_revenue = sum([o.get("total_cost", 0) for o in orders_db 
                        if o["status"] == "delivered" and o.get("delivered_at") and
                        datetime.fromisoformat(o["delivered_at"]) >= today_start])
    
    # Driver performance
    driver_performance = []
    for driver in drivers_db:
        driver_orders = [o for o in orders_db if o.get("assigned_driver") == driver["id"]]
        completed_orders = [o for o in driver_orders if o["status"] == "delivered"]
        
        avg_delivery_time = 0
        if completed_orders:
            times = []
            for order in completed_orders:
                if order.get("delivered_at") and order.get("created_at"):
                    delta = datetime.fromisoformat(order["delivered_at"]) - datetime.fromisoformat(order["created_at"])
                    times.append(delta.total_seconds() / 60)
            avg_delivery_time = sum(times) / len(times) if times else 0
        
        driver_performance.append({
            "driver_id": driver["id"],
            "name": driver["name"],
            "total_orders": len(driver_orders),
            "completed_orders": len(completed_orders),
            "success_rate": (len(completed_orders) / len(driver_orders) * 100) if driver_orders else 0,
            "avg_delivery_time": round(avg_delivery_time, 2),
            "rating": driver["rating"],
            "earnings": sum([o.get("total_cost", 0) * 0.15 for o in completed_orders])
        })
    
    # Fleet status
    fleet_status = {
        "total_drivers": len(drivers_db),
        "online_drivers": len([d for d in drivers_db if d["status"] == "available"]),
        "busy_drivers": len([d for d in drivers_db if d["status"] == "busy"]),
        "offline_drivers": len([d for d in drivers_db if d["status"] == "offline"])
    }
    
    return {
        "revenue": {
            "total": round(total_revenue, 2),
            "today": round(today_revenue, 2),
            "currency": "MAD"
        },
        "driver_performance": driver_performance,
        "fleet_status": fleet_status
    }

# ============= AI-POWERED ASSIGNMENT =============
@router.get("/orders/{order_id}/driver-recommendations")
async def get_driver_recommendations(order_id: str, current_admin: dict = Depends(get_current_admin)):
    """Get AI-powered driver recommendations for order"""
    from main import orders_db, drivers_db, assign_best_driver, calculate_ultimate_driver_score, get_city_coordinates
    
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    pickup_coords = get_city_coordinates(order["pickup_city"])
    
    # Get all available drivers in city
    city_drivers = [d for d in drivers_db if 
                   d["assigned_city"].lower() == order["pickup_city"].lower() and
                   d["status"] in ["available", "busy"]]
    
    # Score each driver
    recommendations = []
    for driver in city_drivers:
        score = calculate_ultimate_driver_score(driver, order, pickup_coords)
        recommendations.append({
            "driver_id": driver["id"],
            "name": driver["name"],
            "vehicle_type": driver["vehicle_type"],
            "rating": driver["rating"],
            "status": driver["status"],
            "current_orders": len(driver["current_orders"]),
            "score": round(score, 2),
            "available": driver["status"] == "available"
        })
    
    # Sort by score
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "order_id": order_id,
        "recommendations": recommendations[:5],
        "total_drivers": len(recommendations)
    }

@router.post("/orders/{order_id}/auto-reassign")
async def auto_reassign_order(order_id: str, current_admin: dict = Depends(get_current_admin)):
    """Use AI Agent to automatically reassign order to best driver"""
    print(f"\n🤖 AI AGENT REASSIGN for order {order_id}", flush=True)
    from main import orders_db, drivers_db, storage, CREW_AVAILABLE
    
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get available drivers in pickup city
    city_drivers = [d for d in drivers_db if 
                   d.get("status") in ["available", "online"] and 
                   d.get("assigned_city", "").lower() == order["pickup_city"].lower()]
    
    print(f"   Found {len(city_drivers)} drivers in {order['pickup_city']}", flush=True)
    print(f"   CREW_AVAILABLE: {CREW_AVAILABLE}", flush=True)
    
    # Try AI Agent first
    ai_reasoning = None
    best_driver = None
    
    if CREW_AVAILABLE:
        try:
            print("   🤖 Calling CrewAI Agent...", flush=True)
            from api.services.agent_service import AgentService
            agent_service = AgentService()
            result = await agent_service.recommend_driver(order, city_drivers)
            
            if result and result.get("driver"):
                best_driver = result["driver"]
                ai_reasoning = result.get("ai_reasoning", "AI Agent recommendation")
                print(f"   ✅ AI Agent selected: {best_driver['name']}", flush=True)
            else:
                print("   ⚠️ AI Agent returned no driver", flush=True)
        except Exception as e:
            print(f"   ❌ AI Agent error: {e}", flush=True)
            import traceback
            traceback.print_exc()
    else:
        print("   ⚠️ CrewAI not available", flush=True)
    
    # Fallback to algorithm if AI failed
    if not best_driver:
        print("   Using fallback algorithm", flush=True)
        from main import assign_best_driver
        excluded = [order["assigned_driver"]] if order.get("assigned_driver") else []
        best_driver = assign_best_driver(order, excluded_drivers=excluded)
        ai_reasoning = "Algorithm-based (AI unavailable or failed)"
    
    if not best_driver:
        raise HTTPException(status_code=404, detail="No suitable driver found")
    
    # Remove from old driver
    if order.get("assigned_driver"):
        old_driver = next((d for d in drivers_db if d["id"] == order["assigned_driver"]), None)
        if old_driver and order_id in old_driver["current_orders"]:
            old_driver["current_orders"].remove(order_id)
            if not old_driver["current_orders"]:
                old_driver["status"] = "available"
            storage.update_driver(old_driver["id"], old_driver)
    
    # Assign to new driver
    order["assigned_driver"] = best_driver["id"]
    order["status"] = "assigned"
    order["reassigned_at"] = datetime.now().isoformat()
    order["reassign_reason"] = ai_reasoning or "AI auto-reassignment"
    
    if order_id not in best_driver["current_orders"]:
        best_driver["current_orders"].append(order_id)
    best_driver["status"] = "busy"
    
    storage.update_order(order_id, order)
    storage.update_driver(best_driver["id"], best_driver)
    
    print(f"   ✅ Reassignment complete\n", flush=True)
    
    return {
        "success": True,
        "message": f"Order reassigned to {best_driver['name']}",
        "ai_reasoning": ai_reasoning,
        "driver": {
            "id": best_driver["id"],
            "name": best_driver["name"],
            "vehicle_type": best_driver["vehicle_type"],
            "rating": best_driver["rating"]
        }
    }

# ============= WAREHOUSE MANAGEMENT =============
@router.get("/warehouses/{warehouse_id}/status")
async def get_warehouse_status(warehouse_id: str, current_admin: dict = Depends(get_current_admin)):
    """Get detailed warehouse status with AI insights"""
    from main import warehouses_db, orders_db
    try:
        from backend.api.services.warehouse_agent import check_warehouse_capacity, predict_warehouse_capacity
        agent_available = True
    except:
        agent_available = False
    
    warehouse = next((w for w in warehouses_db if w["id"] == warehouse_id), None)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Get packages in warehouse
    warehouse_packages = [o for o in orders_db if 
                         o.get("current_warehouse") == warehouse_id or
                         (o["status"] == "at_origin_warehouse" and o["pickup_city"] == warehouse["city"])]
    
    result = {
        "warehouse": warehouse,
        "packages": warehouse_packages,
        "package_count": len(warehouse_packages),
        "utilization": round((warehouse["current_packages"] / warehouse["capacity"]) * 100, 1)
    }
    
    # Add AI insights if available
    if agent_available:
        capacity_check = await check_warehouse_capacity(warehouse_id, warehouses_db, 0)
        prediction = await predict_warehouse_capacity(warehouse_id, warehouses_db, {})
        result["ai_insights"] = {
            "capacity_status": capacity_check,
            "prediction": prediction
        }
    
    return result

@router.post("/warehouses/{warehouse_id}/update")
async def update_warehouse(warehouse_id: str, update_data: dict, current_admin: dict = Depends(get_current_admin)):
    """Update warehouse details"""
    from main import warehouses_db, storage
    
    warehouse = next((w for w in warehouses_db if w["id"] == warehouse_id), None)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Update allowed fields
    allowed_fields = ["status", "manager", "phone", "capacity"]
    for field in allowed_fields:
        if field in update_data:
            warehouse[field] = update_data[field]
    
    warehouse["updated_at"] = datetime.now().isoformat()
    storage.update_warehouse(warehouse_id, warehouse)
    
    return {"success": True, "warehouse": warehouse}

# ============= ALERTS =============
@router.get("/alerts")
def get_system_alerts(current_admin: dict = Depends(get_current_admin)):
    """Get system alerts and issues"""
    from main import orders_db, drivers_db
    
    alerts = []
    
    # Delayed orders
    now = datetime.now()
    for order in orders_db:
        if order["status"] in ["assigned", "picked_up", "in_transit"]:
            if order.get("estimated_delivery"):
                eta = datetime.fromisoformat(order["estimated_delivery"])
                if now > eta:
                    alerts.append({
                        "type": "delayed_order",
                        "severity": "high",
                        "message": f"Order {order['tracking_number']} is delayed",
                        "order_id": order["id"],
                        "delay_minutes": int((now - eta).total_seconds() / 60)
                    })
    
    # Low driver availability
    for city in ["Casablanca", "Rabat", "Marrakech", "Agadir", "El Jadida", "Salé"]:
        city_drivers = [d for d in drivers_db if d.get("assigned_city") == city]
        available = [d for d in city_drivers if d["status"] == "available"]
        if len(available) < 1 and len(city_drivers) > 0:
            alerts.append({
                "type": "low_driver_availability",
                "severity": "medium",
                "message": f"Low driver availability in {city}",
                "city": city,
                "available_drivers": len(available)
            })
    
    # Suspended drivers
    suspended = [d for d in drivers_db if d["status"] == "suspended"]
    if suspended:
        alerts.append({
            "type": "suspended_drivers",
            "severity": "low",
            "message": f"{len(suspended)} driver(s) currently suspended",
            "count": len(suspended)
        })
    
    return {"alerts": alerts, "total": len(alerts)}
