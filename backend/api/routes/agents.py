from fastapi import APIRouter
from api.services.agent_service import AgentService

router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.get("/status")
def get_agents_status():
    return AgentService.get_agent_status()
