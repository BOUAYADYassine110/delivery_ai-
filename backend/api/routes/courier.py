from fastapi import APIRouter, HTTPException
from typing import List

from api.models.courier import Courier
from api.models.order import Order
from api.schemas.courier import CourierCreate, CourierResponse, LocationUpdate

router = APIRouter(prefix="/api/couriers", tags=["couriers"])

@router.post("/", response_model=CourierResponse)
async def create_courier(courier: CourierCreate):
    db_courier = Courier(**courier.dict())
    await db_courier.insert()
    return db_courier

@router.get("/", response_model=List[CourierResponse])
async def get_couriers():
    return await Courier.find_all().to_list()

@router.get("/{courier_id}", response_model=CourierResponse)
async def get_courier(courier_id: str):
    courier = await Courier.get(courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    return courier

@router.post("/{courier_id}/location")
async def update_location(courier_id: str, location: LocationUpdate):
    courier = await Courier.get(courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    courier.current_lat = location.lat
    courier.current_lng = location.lng
    await courier.save()
    
    active_order = await Order.find_one(Order.status.in_(["picked_up", "in_transit"]))
    
    if active_order:
        active_order.current_lat = location.lat
        active_order.current_lng = location.lng
        await active_order.save()
    
    return {"status": "success", "lat": location.lat, "lng": location.lng}

@router.get("/{courier_id}/active-order")
async def get_active_order(courier_id: str):
    from api.services.route_monitor import RouteMonitor
    
    courier = await Courier.get(courier_id)
    
    if courier and courier.assigned_order_id:
        order = await Order.get(courier.assigned_order_id)
        if order:
            route_check = await RouteMonitor.check_route_conditions(str(order.id))
            return {"order": order, "route_update": route_check}
    
    order = await Order.find_one(Order.status.in_(["picked_up", "in_transit"]))
    
    if order:
        return {"order": order, "route_update": {"needs_reroute": False}}
    
    pending_order = await Order.find_one(Order.status == "pending", sort=[("created_at", 1)])
    
    return {"order": pending_order, "route_update": {"needs_reroute": False}}

@router.post("/{courier_id}/accept/{order_id}")
async def accept_order(courier_id: str, order_id: str):
    from api.services.data_logger import DataLogger
    from datetime import datetime
    
    order = await Order.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    courier = await Courier.get(courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    order.status = "picked_up"
    await order.save()
    
    courier.status = "busy"
    courier.assigned_order_id = order_id
    await courier.save()
    
    await DataLogger.log_delivery_event(
        order_id=order_id,
        event_type="order_accepted",
        courier_id=courier_id,
        location_lat=order.sender_lat,
        location_lng=order.sender_lng,
        notes=f"Courier {courier.name} accepted order"
    )
    
    await DataLogger.update_analytics(
        order_id=order_id,
        courier_id=courier_id,
        picked_up_at=datetime.utcnow()
    )
    
    return {"status": "success", "message": "Order accepted"}

@router.post("/{courier_id}/complete/{order_id}")
async def complete_delivery(courier_id: str, order_id: str):
    from api.services.data_logger import DataLogger
    from datetime import datetime
    from api.models.analytics import DeliveryAnalytics
    
    order = await Order.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    courier = await Courier.get(courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    order.status = "delivered"
    order.current_lat = order.receiver_lat
    order.current_lng = order.receiver_lng
    await order.save()
    
    courier.status = "available"
    courier.assigned_order_id = None
    courier.total_deliveries += 1
    await courier.save()
    
    analytics = await DeliveryAnalytics.find_one(DeliveryAnalytics.order_id == order_id)
    
    if analytics and analytics.picked_up_at:
        duration_actual = (datetime.utcnow() - analytics.picked_up_at).total_seconds() / 60
        
        await DataLogger.update_analytics(
            order_id=order_id,
            delivered_at=datetime.utcnow(),
            duration_actual=duration_actual,
            courier_rating=courier.rating
        )
    
    await DataLogger.log_delivery_event(
        order_id=order_id,
        event_type="order_delivered",
        courier_id=courier_id,
        location_lat=order.receiver_lat,
        location_lng=order.receiver_lng,
        notes=f"Delivery completed by {courier.name}"
    )
    
    return {"status": "success", "message": "Delivery completed"}
