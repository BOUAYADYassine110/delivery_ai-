from fastapi import APIRouter, HTTPException
from typing import List

from api.models.tracking import TrackingEvent
from api.schemas.tracking import TrackingEventResponse

router = APIRouter(prefix="/api/tracking", tags=["tracking"])

@router.get("/{order_id}")
async def get_tracking_events(order_id: str):
    events = await TrackingEvent.find(TrackingEvent.order_id == order_id).sort(-TrackingEvent.timestamp).to_list()
    return [{**event.dict(), "id": str(event.id)} for event in events]
