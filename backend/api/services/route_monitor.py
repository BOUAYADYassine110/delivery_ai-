import httpx
from api.models.order import Order
from api.services.data_logger import DataLogger

class RouteMonitor:
    """Monitor routes for traffic and weather changes, trigger rerouting"""
    
    @staticmethod
    async def check_route_conditions(order_id: str):
        """Check if route needs rerouting due to traffic/weather"""
        
        order = await Order.get(order_id)
        if not order or order.status not in ['picked_up', 'in_transit']:
            return {"needs_reroute": False}
        
        weather = await RouteMonitor.get_weather(order.receiver_lat, order.receiver_lng)
        
        bad_weather = False
        if weather:
            temp = weather.get('current', {}).get('temperature_2m', 20)
            wind = weather.get('current', {}).get('wind_speed_10m', 0)
            
            if temp < 0 or temp > 40 or wind > 50:
                bad_weather = True
        
        traffic_heavy = False
        
        needs_reroute = bad_weather or traffic_heavy
        
        if needs_reroute:
            new_route = await RouteMonitor.calculate_new_route(
                order.current_lat, order.current_lng,
                order.receiver_lat, order.receiver_lng,
                order_id
            )
            
            if new_route:
                order.route_geometry = new_route['geometry']
                order.route_duration = new_route['duration']
                order.route_distance = new_route['distance']
                await order.save()
                
                await DataLogger.log_delivery_event(
                    order_id=order_id,
                    event_type="route_changed",
                    location_lat=order.current_lat,
                    location_lng=order.current_lng,
                    weather=weather,
                    traffic="heavy" if traffic_heavy else "normal",
                    notes=f"Rerouted due to {'weather' if bad_weather else 'traffic'}"
                )
                
                return {
                    "needs_reroute": True,
                    "reason": "weather" if bad_weather else "traffic",
                    "new_route": new_route
                }
        
        return {"needs_reroute": False}
    
    @staticmethod
    async def get_weather(lat: float, lng: float):
        """Get current weather conditions"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": lat,
                        "longitude": lng,
                        "current": "temperature_2m,weather_code,wind_speed_10m"
                    },
                    timeout=3.0
                )
                if response.status_code == 200:
                    return response.json()
        except:
            pass
        return None
    
    @staticmethod
    async def calculate_new_route(from_lat: float, from_lng: float, 
                                  to_lat: float, to_lng: float, order_id: str):
        """Calculate alternative route"""
        try:
            route_data = await DataLogger.log_route_api_call(
                order_id, from_lat, from_lng, to_lat, to_lng
            )
            
            if route_data and route_data.get('code') == 'Ok' and route_data.get('routes'):
                route = route_data['routes'][0]
                return {
                    'geometry': route['geometry']['coordinates'],
                    'duration': route.get('duration'),
                    'distance': route.get('distance')
                }
        except:
            pass
        return None
