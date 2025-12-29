from fastapi import APIRouter, HTTPException
from api.models.order import Order
from api.models.tracking import TrackingEvent
from api.services.delivery_workflow import DeliveryWorkflow

router = APIRouter(prefix="/api/delivery", tags=["delivery"])

@router.post("/{order_id}/assign-courier")
async def assign_courier(order_id: str):
    """Assign courier to order using City Hub Agent"""
    order = await Order.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    workflow = DeliveryWorkflow()
    result = await workflow.assign_courier(order_id, order.sender_address)
    
    tracking = TrackingEvent(
        order_id=order_id,
        status="assigned",
        location=order.sender_address,
        description=f"Assigned to courier {result['courier_id']}",
        agent_name="City Hub Agent"
    )
    await tracking.insert()
    
    return result

@router.post("/{order_id}/update-status")
async def update_status(order_id: str, status: str, location: str):
    """Update delivery status using Tracking Agent"""
    order = await Order.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    workflow = DeliveryWorkflow()
    result = await workflow.update_delivery_status(order_id, status, location)
    
    order.status = status
    order.current_location = location
    await order.save()
    
    tracking = TrackingEvent(
        order_id=order_id,
        status=status,
        location=location,
        description=result['description'],
        agent_name="Tracking Agent"
    )
    await tracking.insert()
    
    return result

@router.get("/performance")
async def get_performance():
    """Get performance metrics using Monitoring Agent"""
    orders = await Order.find_all().to_list()
    order_ids = [str(o.id) for o in orders]
    
    workflow = DeliveryWorkflow()
    result = await workflow.monitor_performance(order_ids)
    
    return result
