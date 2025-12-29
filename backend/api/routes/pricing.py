from fastapi import APIRouter
from api.schemas.order import PricingRequest
from api.services.agent_service import AgentService

router = APIRouter(prefix="/api/pricing", tags=["pricing"])

@router.post("/calculate")
async def calculate_pricing(request: PricingRequest):
    result = await AgentService.calculate_price(request.weight, request.distance, request.service_type)
    return result
