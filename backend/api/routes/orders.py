from fastapi import APIRouter, HTTPException
from typing import List
import random
import string

from api.models.order import Order
from api.models.tracking import TrackingEvent
from api.schemas.order import OrderCreate, OrderResponse

router = APIRouter(prefix="/api/orders", tags=["orders"])

def generate_tracking_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

@router.post("/")
async def create_order(order: OrderCreate):
    try:
        import httpx
        from math import radians, sin, cos, sqrt, atan2
        from backend.api.services.delivery_router import DeliveryRouter
        
        delivery_info = await DeliveryRouter.detect_delivery_type(
            order.sender_lat, order.sender_lng,
            order.receiver_lat, order.receiver_lng
        )
        
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            return R * 2 * atan2(sqrt(a), sqrt(1-a))
        
        distance = haversine(order.sender_lat, order.sender_lng, order.receiver_lat, order.receiver_lng)
        base_price = 15.0
        weight_cost = order.weight * 2.0
        distance_cost = distance * 0.5
        service_multiplier = {'standard': 1.0, 'express': 1.5, 'overnight': 2.0}.get(order.service_type, 1.0)
        price = (base_price + weight_cost + distance_cost) * service_multiplier
        
        from api.services.data_logger import DataLogger
        route_geometry = None
        route_duration = None
        route_distance = None
        
        route_data = await DataLogger.log_route_api_call(
            None, order.sender_lat, order.sender_lng, order.receiver_lat, order.receiver_lng
        )
        
        if route_data and route_data.get('code') == 'Ok' and route_data.get('routes'):
            route = route_data['routes'][0]
            route_geometry = route['geometry']['coordinates']
            route_duration = route.get('duration')
            route_distance = route.get('distance')
        
        db_order = Order(
            tracking_number=generate_tracking_number(),
            sender_name=order.sender_name,
            sender_address=order.sender_address,
            sender_lat=order.sender_lat,
            sender_lng=order.sender_lng,
            sender_city=delivery_info.get('sender_city'),
            receiver_name=order.receiver_name,
            receiver_address=order.receiver_address,
            receiver_lat=order.receiver_lat,
            receiver_lng=order.receiver_lng,
            receiver_city=delivery_info.get('receiver_city'),
            delivery_type=delivery_info.get('type'),
            weight=order.weight,
            dimensions=order.dimensions,
            service_type=order.service_type,
            status="pending",
            price=round(price, 2),
            current_location=order.sender_address,
            current_lat=order.sender_lat,
            current_lng=order.sender_lng,
            route_geometry=route_geometry,
            route_duration=route_duration,
            route_distance=route_distance
        )
        await db_order.insert()
        
        await DataLogger.create_analytics_record(
            order_id=str(db_order.id),
            tracking_number=db_order.tracking_number,
            route_distance_planned=route_distance / 1000 if route_distance else distance,
            duration_estimated=route_duration / 60 if route_duration else 0,
            price_charged=db_order.price
        )
        
        await DataLogger.log_delivery_event(
            order_id=str(db_order.id),
            event_type="order_created",
            location_lat=order.sender_lat,
            location_lng=order.sender_lng,
            location_name=order.sender_address,
            notes=f"Order created for {order.service_type} delivery"
        )
        
        tracking = TrackingEvent(
            order_id=str(db_order.id),
            status="pending",
            location=order.sender_address,
            description="Order created and pending pickup",
            agent_name="Client Agent"
        )
        await tracking.insert()
        
        import asyncio
        
        async def process_in_background():
            try:
                order_dict = {
                    "order_id": str(db_order.id),
                    "tracking_number": db_order.tracking_number,
                    "sender_name": order.sender_name,
                    "sender_address": order.sender_address,
                    "sender_city": delivery_info.get('sender_city'),
                    "receiver_name": order.receiver_name,
                    "receiver_address": order.receiver_address,
                    "receiver_city": delivery_info.get('receiver_city'),
                    "weight": order.weight,
                    "dimensions": order.dimensions,
                    "service_type": order.service_type,
                    "pickup_location": f"{order.sender_lat},{order.sender_lng}",
                    "delivery_location": f"{order.receiver_lat},{order.receiver_lng}"
                }
                await DeliveryRouter.route_order(order_dict, delivery_info.get('type'))
            except Exception as e:
                print(f"Agent workflow error: {e}")
        
        asyncio.create_task(process_in_background())
        print(f"Order created: {db_order.tracking_number} - Type: {delivery_info.get('type')}")
        print(f"Route: {delivery_info.get('sender_city')} -> {delivery_info.get('receiver_city')}")
        print(f"AI agents processing in background...")
        
        return {**db_order.dict(), "id": str(db_order.id)}
    except Exception as e:
        print(f"Order creation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_orders(skip: int = 0, limit: int = 100):
    try:
        orders = await Order.find_all().sort(-Order.created_at).skip(skip).limit(limit).to_list()
        return [{**order.dict(), "id": str(order.id)} for order in orders]
    except Exception as e:
        print(f"Error fetching orders: {e}")
        return []

@router.get("/{order_id}")
async def get_order(order_id: str):
    order = await Order.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {**order.dict(), "id": str(order.id)}

@router.get("/tracking/{tracking_number}")
async def get_order_by_tracking(tracking_number: str):
    order = await Order.find_one(Order.tracking_number == tracking_number)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {**order.dict(), "id": str(order.id)}
