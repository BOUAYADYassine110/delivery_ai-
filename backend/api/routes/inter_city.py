from fastapi import APIRouter, Depends, HTTPException
from api.services.inter_city_workflow import InterCityWorkflow
from api.models.user import User
from core.auth import get_current_user
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/inter-city", tags=["inter-city"])

class InterCityOrderRequest(BaseModel):
    sender_address: str
    receiver_address: str
    origin_city: str
    destination_city: str
    package_description: str
    weight: float
    dimensions: Optional[dict] = None
    service_type: str = "standard"
    is_international: bool = False
    waypoints: Optional[List[str]] = None
    special_requirements: Optional[str] = None

class InterCityOrderResponse(BaseModel):
    order_id: str
    status: str
    estimated_cost: float
    estimated_delivery_time: str
    route_plan: dict
    workflow_result: str

@router.post("/orders", response_model=InterCityOrderResponse)
async def create_inter_city_order(
    order: InterCityOrderRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new inter-city delivery order"""
    try:
        workflow = InterCityWorkflow()

        order_data = {
            **order.dict(),
            "customer_id": str(current_user.id),
            "customer_email": current_user.email,
            "order_type": "inter_city"
        }

        result = await workflow.process_inter_city_order(order_data)

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        # Mock response - in real implementation, save to database
        return {
            "order_id": "IC-" + str(hash(str(order_data))),
            "status": "processing",
            "estimated_cost": 150.00,  # Would be calculated by pricing agent
            "estimated_delivery_time": "2-3 days",
            "route_plan": {
                "origin": order.origin_city,
                "destination": order.destination_city,
                "hubs": ["Hub A", "Hub B"],
                "transportation": "truck"
            },
            "workflow_result": result["result"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders/{order_id}/monitor")
async def monitor_inter_city_delivery(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    """Monitor an active inter-city delivery"""
    try:
        workflow = InterCityWorkflow()

        route_data = {
            "order_id": order_id,
            "current_segment": "en_route",
            "segments": ["pickup", "hub_transfer", "delivery"]
        }

        result = await workflow.monitor_inter_city_delivery(order_id, route_data)

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        return {
            "order_id": order_id,
            "status": "monitoring",
            "current_location": "En route to destination hub",
            "next_update": "in 30 minutes",
            "workflow_result": result["result"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders/{order_id}/complete")
async def complete_inter_city_delivery(
    order_id: str,
    completion_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Complete an inter-city delivery"""
    try:
        workflow = InterCityWorkflow()

        result = await workflow.handle_inter_city_completion(order_id, completion_data)

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        return {
            "order_id": order_id,
            "status": "completed",
            "completion_time": "now",
            "workflow_result": result["result"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pricing/{origin}/{destination}")
async def get_inter_city_pricing(
    origin: str,
    destination: str,
    weight: float = 1.0,
    service_type: str = "standard"
):
    """Get pricing estimate for inter-city delivery"""
    try:
        # Mock pricing calculation - would use pricing agent
        base_price = 50.00
        weight_multiplier = weight * 2.0
        distance_factor = 100.0  # Mock distance-based pricing

        total_price = base_price + weight_multiplier + distance_factor

        return {
            "origin": origin,
            "destination": destination,
            "weight": weight,
            "service_type": service_type,
            "estimated_price": total_price,
            "currency": "USD",
            "breakdown": {
                "base_fee": base_price,
                "weight_fee": weight_multiplier,
                "distance_fee": distance_factor
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/routes/{origin}/{destination}")
async def get_inter_city_route(
    origin: str,
    destination: str,
    waypoints: Optional[str] = None
):
    """Get route information for inter-city delivery"""
    try:
        waypoint_list = waypoints.split(",") if waypoints else []

        # Mock route planning - would use routing agent
        return {
            "origin": origin,
            "destination": destination,
            "waypoints": waypoint_list,
            "total_distance": "500 km",
            "estimated_time": "8-10 hours",
            "hubs": ["Central Hub", "Regional Hub"],
            "transportation_modes": ["truck", "rail"],
            "route_segments": [
                {"from": origin, "to": "Central Hub", "mode": "truck", "distance": "200km"},
                {"from": "Central Hub", "to": "Regional Hub", "mode": "rail", "distance": "150km"},
                {"from": "Regional Hub", "to": destination, "mode": "truck", "distance": "150km"}
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
