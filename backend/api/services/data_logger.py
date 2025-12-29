from datetime import datetime
from api.models.analytics import DeliveryAnalytics, APICallLog, DeliveryEvent
import time

class DataLogger:
    """Service to log all delivery data for ML training"""
    
    @staticmethod
    async def log_api_call(order_id: str, api_name: str, endpoint: str, 
                     request_params: dict, response_data: dict, response_time: float, status_code: int):
        """Log external API calls"""
        log = APICallLog(
            order_id=order_id,
            api_name=api_name,
            endpoint=endpoint,
            request_params=request_params,
            response_data=response_data,
            response_time=response_time,
            status_code=status_code
        )
        await log.insert()
        return log
    
    @staticmethod
    async def log_delivery_event(order_id: str, event_type: str, 
                          location_lat: float = None, location_lng: float = None,
                          location_name: str = None, weather: dict = None, 
                          traffic: str = None, courier_id: str = None, notes: str = None):
        """Log delivery events"""
        event = DeliveryEvent(
            order_id=order_id,
            event_type=event_type,
            location_lat=location_lat,
            location_lng=location_lng,
            location_name=location_name,
            weather_conditions=weather,
            traffic_conditions=traffic,
            courier_id=courier_id,
            notes=notes
        )
        await event.insert()
        return event
    
    @staticmethod
    async def create_analytics_record(order_id: str, tracking_number: str,
                               route_distance_planned: float, duration_estimated: float,
                               price_charged: float):
        """Create initial analytics record"""
        analytics = DeliveryAnalytics(
            order_id=order_id,
            tracking_number=tracking_number,
            route_distance_planned=route_distance_planned,
            duration_estimated=duration_estimated,
            price_charged=price_charged
        )
        await analytics.insert()
        return analytics
    
    @staticmethod
    async def update_analytics(order_id: str, **kwargs):
        """Update analytics record with new data"""
        analytics = await DeliveryAnalytics.find_one(DeliveryAnalytics.order_id == order_id)
        
        if analytics:
            for key, value in kwargs.items():
                if hasattr(analytics, key):
                    setattr(analytics, key, value)
            await analytics.save()
        return analytics
    
    @staticmethod
    async def log_route_api_call(order_id: str, sender_lat: float, sender_lng: float,
                                 receiver_lat: float, receiver_lng: float):
        """Log OSRM API call and response"""
        import httpx
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"http://router.project-osrm.org/route/v1/driving/{sender_lng},{sender_lat};{receiver_lng},{receiver_lat}"
                response = await client.get(
                    url,
                    params={"overview": "full", "geometries": "geojson"},
                    timeout=3.0
                )
                response_time = time.time() - start_time
                
                if order_id:
                    await DataLogger.log_api_call(
                        order_id=order_id,
                        api_name="OSRM",
                        endpoint=url,
                        request_params={"start": f"{sender_lng},{sender_lat}", "end": f"{receiver_lng},{receiver_lat}"},
                        response_data=response.json() if response.status_code == 200 else {},
                        response_time=response_time,
                        status_code=response.status_code
                    )
                
                return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Route API logging error: {e}")
            return None
    
    @staticmethod
    async def log_weather_api_call(order_id: str, lat: float, lng: float):
        """Log weather API call and response"""
        import httpx
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.open-meteo.com/v1/forecast"
                response = await client.get(
                    url,
                    params={
                        "latitude": lat,
                        "longitude": lng,
                        "current": "temperature_2m,weather_code,wind_speed_10m"
                    },
                    timeout=3.0
                )
                response_time = time.time() - start_time
                
                await DataLogger.log_api_call(
                    order_id=order_id,
                    api_name="OpenMeteo",
                    endpoint=url,
                    request_params={"lat": lat, "lng": lng},
                    response_data=response.json() if response.status_code == 200 else {},
                    response_time=response_time,
                    status_code=response.status_code
                )
                
                return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Weather API logging error: {e}")
            return None
    
    @staticmethod
    async def export_to_csv(output_file: str = "delivery_data.csv"):
        """Export all analytics data to CSV for ML training"""
        import csv
        
        analytics = await DeliveryAnalytics.find_all().to_list()
        
        if not analytics:
            print("No data to export")
            return
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            writer.writerow([
                'order_id', 'tracking_number', 'route_distance_planned', 'route_distance_actual',
                'duration_estimated', 'duration_actual', 'weather_impact', 'traffic_level',
                'traffic_delays', 'courier_id', 'courier_rating', 'acceptance_time',
                'price_charged', 'cost_estimate', 'profit_margin', 'customer_satisfaction',
                'created_at', 'picked_up_at', 'delivered_at'
            ])
            
            for record in analytics:
                writer.writerow([
                    record.order_id, record.tracking_number, record.route_distance_planned,
                    record.route_distance_actual, record.duration_estimated, record.duration_actual,
                    record.weather_impact, record.traffic_level, record.traffic_delays,
                    record.courier_id, record.courier_rating, record.acceptance_time,
                    record.price_charged, record.cost_estimate, record.profit_margin,
                    record.customer_satisfaction, record.created_at, record.picked_up_at,
                    record.delivered_at
                ])
        
        print(f"Data exported to {output_file}")
        return output_file
