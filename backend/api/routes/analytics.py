from fastapi import APIRouter
from api.services.data_logger import DataLogger
from api.models.analytics import DeliveryAnalytics, APICallLog, DeliveryEvent
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/delivery-data")
async def get_delivery_analytics():
    """Get all delivery analytics data"""
    analytics = await DeliveryAnalytics.find_all().to_list()
    return {"total_records": len(analytics), "data": analytics}

@router.get("/api-calls")
async def get_api_calls():
    """Get all API call logs"""
    logs = await APICallLog.find_all().to_list()
    return {"total_calls": len(logs), "data": logs}

@router.get("/events")
async def get_delivery_events():
    """Get all delivery events"""
    events = await DeliveryEvent.find_all().to_list()
    return {"total_events": len(events), "data": events}

@router.get("/export/csv")
async def export_to_csv():
    """Export analytics data to CSV for ML training"""
    file_path = await DataLogger.export_to_csv("delivery_data.csv")
    return FileResponse(
        path=file_path,
        filename="delivery_data.csv",
        media_type="text/csv"
    )

@router.get("/stats")
async def get_statistics():
    """Get delivery statistics"""
    all_analytics = await DeliveryAnalytics.find_all().to_list()
    
    total_deliveries = len(all_analytics)
    
    durations = [a.duration_actual for a in all_analytics if a.duration_actual]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    distances = [a.route_distance_actual for a in all_analytics if a.route_distance_actual]
    avg_distance = sum(distances) / len(distances) if distances else 0
    
    total_api_calls = await APICallLog.find_all().count()
    
    return {
        "total_deliveries": total_deliveries,
        "avg_duration_minutes": round(avg_duration, 2),
        "avg_distance_km": round(avg_distance, 2),
        "total_api_calls": total_api_calls
    }
