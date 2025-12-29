from datetime import datetime
import requests
import math

class SmartAssignmentService:
    def __init__(self):
        self.weather_cache = {}
        
    async def get_weather_conditions(self, city: str) -> dict:
        """Get current weather conditions for a city"""
        if city in self.weather_cache:
            cached = self.weather_cache[city]
            if (datetime.now() - cached['timestamp']).seconds < 1800:  # 30 min cache
                return cached['data']
        
        try:
            # Free weather API (no key needed)
            coords = self.get_city_coordinates(city)
            url = f"https://api.open-meteo.com/v1/current?latitude={coords['lat']}&longitude={coords['lng']}&current=temperature_2m,precipitation,weather_code,wind_speed_10m"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            weather = {
                'temperature': data['current']['temperature_2m'],
                'precipitation': data['current']['precipitation'],
                'weather_code': data['current']['weather_code'],
                'wind_speed': data['current']['wind_speed_10m'],
                'condition': self.get_weather_condition(data['current']['weather_code']),
                'is_rainy': data['current']['precipitation'] > 0.1,
                'is_stormy': data['current']['wind_speed_10m'] > 25
            }
            
            self.weather_cache[city] = {
                'data': weather,
                'timestamp': datetime.now()
            }
            
            return weather
        except:
            # Fallback weather
            return {
                'temperature': 20,
                'precipitation': 0,
                'condition': 'clear',
                'is_rainy': False,
                'is_stormy': False
            }
    
    def get_weather_condition(self, code: int) -> str:
        """Convert weather code to condition"""
        if code in [61, 63, 65, 80, 81, 82]:
            return 'rainy'
        elif code in [71, 73, 75, 85, 86]:
            return 'snowy'
        elif code in [45, 48]:
            return 'foggy'
        elif code in [95, 96, 99]:
            return 'stormy'
        else:
            return 'clear'
    
    def get_city_coordinates(self, city: str) -> dict:
        """Get coordinates for Moroccan cities"""
        coordinates = {
            "casablanca": {"lat": 33.5731, "lng": -7.5898},
            "rabat": {"lat": 34.0209, "lng": -6.8416},
            "marrakech": {"lat": 31.6295, "lng": -7.9811},
            "el jadida": {"lat": 33.2316, "lng": -8.5007},
            "salé": {"lat": 34.0531, "lng": -6.7985},
            "agadir": {"lat": 30.4278, "lng": -9.5981}
        }
        return coordinates.get(city.lower(), coordinates["casablanca"])
    
    async def find_best_driver(self, order: dict, available_drivers: list) -> dict:
        """Find the best driver using advanced scoring algorithm"""
        if not available_drivers:
            return None
        
        pickup_coords = self.get_city_coordinates(order["pickup_city"])
        weather = await self.get_weather_conditions(order["pickup_city"])
        
        best_driver = None
        best_score = -1
        
        for driver in available_drivers:
            if not self.is_driver_suitable(driver, order, weather):
                continue
                
            score = await self.calculate_driver_score(driver, order, pickup_coords, weather)
            
            if score > best_score:
                best_score = score
                best_driver = driver
        
        return best_driver
    
    def is_driver_suitable(self, driver: dict, order: dict, weather: dict) -> bool:
        """Check if driver is suitable for the order given weather conditions"""
        vehicle_type = driver.get("vehicle_type", "bike")
        
        # Relaxed weather restrictions for demo
        # Only block in severe conditions
        if weather.get("is_stormy") and vehicle_type in ["bike", "scooter"]:
            return False  # No two-wheelers in storms only
        
        # Check availability (allow both available and online)
        if driver.get("status") not in ["available", "online"]:
            return False
        
        # Relaxed capacity check
        current_load = sum([self.get_order_weight(oid) for oid in driver.get("current_orders", [])])
        if current_load + order.get("weight", 1) > driver.get("vehicle_capacity", 50):
            return False
        
        # Relaxed max orders
        max_orders = {"bike": 5, "scooter": 6, "car": 8, "van": 10}.get(vehicle_type, 5)
        if len(driver.get("current_orders", [])) >= max_orders:
            return False
        
        return True
    
    async def calculate_driver_score(self, driver: dict, order: dict, pickup_coords: dict, weather: dict) -> float:
        """Calculate comprehensive driver score"""
        score = 0
        
        # Distance factor (40% weight)
        driver_coords = driver.get("current_location", {})
        if driver_coords:
            distance = self.calculate_distance(
                driver_coords.get("lat", pickup_coords["lat"]),
                driver_coords.get("lng", pickup_coords["lng"]),
                pickup_coords["lat"],
                pickup_coords["lng"]
            )
            distance_score = max(0, 100 - distance * 10)  # Penalty for distance
            score += distance_score * 0.4
        
        # Driver rating (25% weight)
        rating_score = (driver.get("rating", 4.0) / 5.0) * 100
        score += rating_score * 0.25
        
        # Vehicle suitability (20% weight)
        vehicle_score = self.get_vehicle_weather_score(driver.get("vehicle_type"), weather, order)
        score += vehicle_score * 0.2
        
        # Current load factor (10% weight)
        current_orders = len(driver.get("current_orders", []))
        max_orders = {"bike": 3, "scooter": 4, "car": 6, "van": 8}.get(driver.get("vehicle_type"), 3)
        load_score = (1 - current_orders / max_orders) * 100
        score += load_score * 0.1
        
        # Experience factor (5% weight)
        experience_score = min(100, driver.get("total_deliveries", 0) * 2)
        score += experience_score * 0.05
        
        return score
    
    def get_vehicle_weather_score(self, vehicle_type: str, weather: dict, order: dict) -> float:
        """Score vehicle suitability based on weather and order"""
        base_scores = {
            "bike": 60,
            "scooter": 70,
            "car": 90,
            "van": 100
        }
        
        score = base_scores.get(vehicle_type, 60)
        
        # Weather adjustments
        if weather.get("is_rainy"):
            if vehicle_type in ["car", "van"]:
                score += 20  # Bonus for enclosed vehicles in rain
            elif vehicle_type in ["bike", "scooter"]:
                score -= 50  # Penalty for exposed vehicles
        
        if weather.get("is_stormy"):
            if vehicle_type == "van":
                score += 10  # Vans are more stable
            elif vehicle_type == "bike":
                score -= 30
        
        # Order type adjustments
        if order.get("service_type") == "express":
            if vehicle_type in ["bike", "scooter"]:
                score += 15  # Two-wheelers are faster in city
        
        if order.get("weight", 1) > 10:
            if vehicle_type in ["car", "van"]:
                score += 20
            else:
                score -= 20
        
        return max(0, min(100, score))
    
    def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between coordinates in km"""
        R = 6371
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def get_order_weight(self, order_id: str) -> float:
        """Get order weight by ID (mock implementation)"""
        return 2.0  # Default weight
    
    async def reassign_order(self, order: dict, excluded_drivers: list = []) -> dict:
        """Reassign order to next best available driver"""
        from main import drivers_db  # Import here to avoid circular imports
        
        available_drivers = [
            d for d in drivers_db 
            if d["id"] not in excluded_drivers and 
            d.get("status") == "available" and
            d.get("current_location", {}).get("city", "").lower() == order["pickup_city"].lower()
        ]
        
        return await self.find_best_driver(order, available_drivers)