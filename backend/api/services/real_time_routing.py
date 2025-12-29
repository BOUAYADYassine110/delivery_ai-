import requests
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import math

class RealTimeRoutingService:
    def __init__(self):
        self.osrm_base = "https://router.project-osrm.org/route/v1"
        self.weather_cache = {}
        self.traffic_cache = {}
        
    async def calculate_optimized_route(self, driver_location: dict, waypoints: List[dict], 
                                      vehicle_type: str = "bike") -> dict:
        """Calculate optimized route considering real-time conditions"""
        
        # Get weather conditions for route area
        weather = await self.get_weather_conditions(driver_location)
        
        # Get traffic conditions (simulated based on time and weather)
        traffic = self.get_traffic_conditions(weather)
        
        # Calculate base route using OSRM
        route_data = await self.get_osrm_route(driver_location, waypoints, vehicle_type)
        
        # Apply real-time optimizations
        optimized_route = await self.apply_real_time_optimizations(
            route_data, weather, traffic, vehicle_type
        )
        
        return optimized_route
    
    async def get_osrm_route(self, start: dict, waypoints: List[dict], vehicle_type: str) -> dict:
        """Enhanced OSRM routing with multiple fallbacks and optimization"""
        try:
            profile = self.get_osrm_profile(vehicle_type)
            
            # Try multiple OSRM servers for reliability
            servers = [
                "https://router.project-osrm.org/route/v1",
                "https://routing.openstreetmap.de/routed-car/route/v1",
                "https://api.openrouteservice.org/v2/directions"
            ]
            
            for server_url in servers:
                try:
                    if "openrouteservice" in server_url:
                        return await self.get_ors_route(start, waypoints, vehicle_type)
                    else:
                        return await self.get_osrm_server_route(server_url, start, waypoints, profile)
                except Exception as e:
                    print(f"Server {server_url} failed: {e}")
                    continue
            
            # All servers failed, use enhanced fallback
            return await self.get_enhanced_fallback_route(start, waypoints, vehicle_type)
                
        except Exception as e:
            print(f"OSRM routing error: {e}")
            return await self.get_enhanced_fallback_route(start, waypoints, vehicle_type)
    
    async def get_osrm_server_route(self, server_url: str, start: dict, waypoints: List[dict], profile: str) -> dict:
        """Get route from specific OSRM server"""
        coords = [f"{start['lng']},{start['lat']}"]
        for wp in waypoints:
            coords.append(f"{wp['lng']},{wp['lat']}")
        
        coordinates = ";".join(coords)
        url = f"{server_url}/{profile}/{coordinates}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
            "annotations": "true",
            "alternatives": "true"
        }
        
        response = requests.get(url, params=params, timeout=8)
        data = response.json()
        
        if data.get("routes"):
            # Select best route from alternatives
            best_route = self.select_best_route(data["routes"])
            return {
                "coordinates": best_route["geometry"]["coordinates"],
                "distance": best_route["distance"],
                "duration": best_route["duration"],
                "steps": self.parse_route_steps(best_route.get("legs", [])),
                "confidence": "high",
                "source": "osrm"
            }
        
        raise Exception("No routes found")
    
    async def get_ors_route(self, start: dict, waypoints: List[dict], vehicle_type: str) -> dict:
        """Get route from OpenRouteService as alternative"""
        coords = [[start['lng'], start['lat']]]
        for wp in waypoints:
            coords.append([wp['lng'], wp['lat']])
        
        profile_map = {
            "cycling": "cycling-regular",
            "driving": "driving-car"
        }
        
        profile = profile_map.get(self.get_osrm_profile(vehicle_type), "driving-car")
        
        url = f"https://api.openrouteservice.org/v2/directions/{profile}/geojson"
        
        payload = {
            "coordinates": coords,
            "instructions": True,
            "elevation": False
        }
        
        response = requests.post(url, json=payload, timeout=8)
        data = response.json()
        
        if data.get("features"):
            feature = data["features"][0]
            props = feature["properties"]
            
            return {
                "coordinates": feature["geometry"]["coordinates"],
                "distance": props["summary"]["distance"],
                "duration": props["summary"]["duration"],
                "steps": self.parse_ors_steps(props.get("segments", [])),
                "confidence": "medium",
                "source": "ors"
            }
        
        raise Exception("ORS routing failed")
    
    def select_best_route(self, routes: List[dict]) -> dict:
        """Select best route from alternatives based on multiple criteria"""
        if len(routes) == 1:
            return routes[0]
        
        best_route = routes[0]
        best_score = 0
        
        for route in routes:
            # Score based on distance, duration, and complexity
            distance_score = 1000 / (route["distance"] / 1000 + 1)  # Shorter is better
            duration_score = 600 / (route["duration"] / 60 + 1)     # Faster is better
            
            # Prefer routes with fewer turns (less complex)
            steps_count = len(route.get("legs", [{}])[0].get("steps", []))
            complexity_score = 100 / (steps_count + 1)
            
            total_score = distance_score + duration_score + complexity_score
            
            if total_score > best_score:
                best_score = total_score
                best_route = route
        
        return best_route
    
    def parse_ors_steps(self, segments: List[dict]) -> List[dict]:
        """Parse OpenRouteService steps"""
        steps = []
        for segment in segments:
            for step in segment.get("steps", []):
                steps.append({
                    "instruction": step.get("instruction", "Continue"),
                    "distance": step.get("distance", 0),
                    "duration": step.get("duration", 0),
                    "type": step.get("type", "straight")
                })
        return steps
    
    def get_osrm_profile(self, vehicle_type: str) -> str:
        """Map vehicle type to OSRM routing profile"""
        profiles = {
            "bike": "cycling",
            "scooter": "cycling", 
            "car": "driving",
            "van": "driving",
            "truck": "driving"
        }
        return profiles.get(vehicle_type, "cycling")
    
    def parse_route_steps(self, legs: List[dict]) -> List[dict]:
        """Parse OSRM route steps into navigation instructions"""
        steps = []
        
        for leg in legs:
            for step in leg.get("steps", []):
                instruction = step.get("maneuver", {})
                
                steps.append({
                    "instruction": self.get_instruction_text(instruction),
                    "distance": step.get("distance", 0),
                    "duration": step.get("duration", 0),
                    "coordinates": step.get("geometry", {}).get("coordinates", []),
                    "type": instruction.get("type", "straight")
                })
        
        return steps
    
    def get_instruction_text(self, maneuver: dict) -> str:
        """Convert OSRM maneuver to readable instruction"""
        maneuver_type = maneuver.get("type", "straight")
        modifier = maneuver.get("modifier", "")
        
        instructions = {
            "depart": "Start your journey",
            "arrive": "You have arrived at your destination",
            "turn": f"Turn {modifier}" if modifier else "Turn",
            "continue": "Continue straight",
            "merge": "Merge",
            "on-ramp": "Take the ramp",
            "off-ramp": "Take the exit",
            "fork": f"Keep {modifier}" if modifier else "Keep going",
            "roundabout": "Enter the roundabout"
        }
        
        return instructions.get(maneuver_type, "Continue")
    
    async def get_weather_conditions(self, location: dict) -> dict:
        """Get current weather conditions"""
        cache_key = f"{location['lat']:.2f},{location['lng']:.2f}"
        
        if cache_key in self.weather_cache:
            cached = self.weather_cache[cache_key]
            if (datetime.now() - cached['timestamp']).seconds < 1800:  # 30 min cache
                return cached['data']
        
        try:
            url = f"https://api.open-meteo.com/v1/current"
            params = {
                "latitude": location['lat'],
                "longitude": location['lng'],
                "current": "temperature_2m,precipitation,weather_code,wind_speed_10m,visibility"
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            current = data.get("current", {})
            weather = {
                "temperature": current.get("temperature_2m", 20),
                "precipitation": current.get("precipitation", 0),
                "weather_code": current.get("weather_code", 0),
                "wind_speed": current.get("wind_speed_10m", 0),
                "visibility": current.get("visibility", 10000),
                "condition": self.get_weather_condition(current.get("weather_code", 0)),
                "is_rainy": current.get("precipitation", 0) > 0.1,
                "is_foggy": current.get("visibility", 10000) < 1000,
                "is_windy": current.get("wind_speed_10m", 0) > 20
            }
            
            self.weather_cache[cache_key] = {
                "data": weather,
                "timestamp": datetime.now()
            }
            
            return weather
            
        except Exception as e:
            print(f"Weather API error: {e}")
            return {
                "temperature": 20,
                "condition": "clear",
                "is_rainy": False,
                "is_foggy": False,
                "is_windy": False
            }
    
    def get_weather_condition(self, code: int) -> str:
        """Convert weather code to condition"""
        if code in [61, 63, 65, 80, 81, 82]:
            return "rainy"
        elif code in [71, 73, 75, 85, 86]:
            return "snowy"
        elif code in [45, 48]:
            return "foggy"
        elif code in [95, 96, 99]:
            return "stormy"
        else:
            return "clear"
    
    def get_traffic_conditions(self, weather: dict) -> dict:
        """Simulate traffic conditions based on time and weather"""
        now = datetime.now()
        hour = now.hour
        
        # Base traffic based on time of day
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            base_traffic = "heavy"
            delay_factor = 1.5
        elif 10 <= hour <= 16:
            base_traffic = "moderate"
            delay_factor = 1.2
        else:
            base_traffic = "light"
            delay_factor = 1.0
        
        # Weather impact on traffic
        if weather.get("is_rainy"):
            delay_factor *= 1.3
        if weather.get("is_foggy"):
            delay_factor *= 1.4
        if weather.get("is_windy"):
            delay_factor *= 1.1
        
        return {
            "condition": base_traffic,
            "delay_factor": delay_factor,
            "congestion_level": min(100, int(delay_factor * 50))
        }
    
    async def apply_real_time_optimizations(self, route_data: dict, weather: dict, 
                                          traffic: dict, vehicle_type: str) -> dict:
        """Apply real-time optimizations to route"""
        
        # Adjust duration based on conditions
        base_duration = route_data["duration"]
        adjusted_duration = base_duration * traffic["delay_factor"]
        
        # Vehicle-specific adjustments
        vehicle_adjustments = {
            "bike": {
                "rain_penalty": 1.4,
                "wind_penalty": 1.2,
                "traffic_benefit": 0.8  # Bikes can navigate traffic better
            },
            "scooter": {
                "rain_penalty": 1.3,
                "wind_penalty": 1.15,
                "traffic_benefit": 0.85
            },
            "car": {
                "rain_penalty": 1.1,
                "wind_penalty": 1.0,
                "traffic_benefit": 1.0
            },
            "van": {
                "rain_penalty": 1.15,
                "wind_penalty": 1.05,
                "traffic_benefit": 1.1
            }
        }
        
        adjustments = vehicle_adjustments.get(vehicle_type, vehicle_adjustments["bike"])
        
        if weather.get("is_rainy"):
            adjusted_duration *= adjustments["rain_penalty"]
        
        if weather.get("is_windy"):
            adjusted_duration *= adjustments["wind_penalty"]
        
        # Apply traffic benefit/penalty
        adjusted_duration *= adjustments["traffic_benefit"]
        
        # Calculate optimized speed
        distance_km = route_data["distance"] / 1000
        optimized_speed = (distance_km / (adjusted_duration / 3600)) if adjusted_duration > 0 else 0
        
        # Generate route warnings
        warnings = []
        if weather.get("is_rainy"):
            warnings.append("⚠️ Rain detected - Drive carefully, reduced visibility")
        if weather.get("is_foggy"):
            warnings.append("⚠️ Fog warning - Very low visibility")
        if traffic["condition"] == "heavy":
            warnings.append("🚦 Heavy traffic - Expect delays")
        
        return {
            "coordinates": route_data["coordinates"],
            "distance": route_data["distance"],
            "original_duration": base_duration,
            "optimized_duration": int(adjusted_duration),
            "steps": route_data["steps"],
            "weather": weather,
            "traffic": traffic,
            "warnings": warnings,
            "optimized_speed": round(optimized_speed, 1),
            "vehicle_type": vehicle_type,
            "eta": datetime.now().timestamp() + adjusted_duration,
            "route_quality": self.calculate_route_quality(weather, traffic),
            "alternative_suggested": self.should_suggest_alternative(weather, traffic, vehicle_type)
        }
    
    def calculate_route_quality(self, weather: dict, traffic: dict) -> str:
        """Calculate overall route quality"""
        score = 100
        
        if weather.get("is_rainy"):
            score -= 20
        if weather.get("is_foggy"):
            score -= 30
        if weather.get("is_windy"):
            score -= 10
        
        if traffic["condition"] == "heavy":
            score -= 25
        elif traffic["condition"] == "moderate":
            score -= 10
        
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        else:
            return "poor"
    
    def should_suggest_alternative(self, weather: dict, traffic: dict, vehicle_type: str) -> bool:
        """Determine if alternative route should be suggested"""
        if weather.get("is_foggy") and vehicle_type in ["bike", "scooter"]:
            return True
        if weather.get("is_rainy") and traffic["condition"] == "heavy":
            return True
        return False
    
    async def get_enhanced_fallback_route(self, start: dict, waypoints: List[dict], vehicle_type: str) -> dict:
        """Enhanced fallback with smart routing algorithms"""
        all_points = [start] + waypoints
        
        # Use A* pathfinding for better route estimation
        optimized_order = self.optimize_waypoint_order(all_points)
        
        coordinates = []
        total_distance = 0
        total_duration = 0
        steps = []
        
        for i in range(len(optimized_order) - 1):
            current = optimized_order[i]
            next_point = optimized_order[i + 1]
            
            # Generate intermediate points for smoother route
            segment_coords = self.generate_route_segment(current, next_point)
            coordinates.extend(segment_coords)
            
            distance = self.calculate_distance(current['lat'], current['lng'], 
                                             next_point['lat'], next_point['lng'])
            total_distance += distance
            
            # Estimate duration based on vehicle type and conditions
            speed = self.get_vehicle_speed(vehicle_type, distance)
            duration = (distance / speed) * 3600  # Convert to seconds
            total_duration += duration
            
            steps.append({
                "instruction": f"Head towards {next_point.get('address', 'destination')}",
                "distance": distance * 1000,
                "duration": duration,
                "type": "straight"
            })
        
        return {
            "coordinates": coordinates,
            "distance": total_distance * 1000,
            "duration": total_duration,
            "steps": steps,
            "confidence": "low",
            "source": "fallback"
        }
    
    def optimize_waypoint_order(self, points: List[dict]) -> List[dict]:
        """Optimize waypoint order using nearest neighbor with 2-opt"""
        if len(points) <= 2:
            return points
        
        # Start with nearest neighbor
        unvisited = points[1:].copy()
        route = [points[0]]
        current = points[0]
        
        while unvisited:
            nearest = min(unvisited, key=lambda p: self.calculate_distance(
                current['lat'], current['lng'], p['lat'], p['lng']
            ))
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        # Apply 2-opt improvement
        return self.two_opt_optimize(route)
    
    def two_opt_optimize(self, route: List[dict]) -> List[dict]:
        """2-opt optimization for route improvement"""
        best_route = route.copy()
        best_distance = self.calculate_route_distance(route)
        improved = True
        
        while improved:
            improved = False
            for i in range(1, len(route) - 2):
                for j in range(i + 1, len(route)):
                    if j - i == 1: continue
                    
                    new_route = route.copy()
                    new_route[i:j] = route[i:j][::-1]
                    
                    new_distance = self.calculate_route_distance(new_route)
                    if new_distance < best_distance:
                        best_route = new_route
                        best_distance = new_distance
                        improved = True
            
            route = best_route
        
        return best_route
    
    def calculate_route_distance(self, route: List[dict]) -> float:
        """Calculate total distance for route"""
        total = 0
        for i in range(len(route) - 1):
            total += self.calculate_distance(
                route[i]['lat'], route[i]['lng'],
                route[i + 1]['lat'], route[i + 1]['lng']
            )
        return total
    
    def generate_route_segment(self, start: dict, end: dict) -> List[List[float]]:
        """Generate smooth route segment between two points"""
        # Create intermediate points for smoother visualization
        coords = [[start['lng'], start['lat']]]
        
        # Add intermediate points based on distance
        distance = self.calculate_distance(start['lat'], start['lng'], end['lat'], end['lng'])
        
        if distance > 5:  # For distances > 5km, add intermediate points
            num_points = min(int(distance / 2), 10)
            for i in range(1, num_points):
                ratio = i / num_points
                lat = start['lat'] + (end['lat'] - start['lat']) * ratio
                lng = start['lng'] + (end['lng'] - start['lng']) * ratio
                coords.append([lng, lat])
        
        coords.append([end['lng'], end['lat']])
        return coords
    
    def get_vehicle_speed(self, vehicle_type: str, distance: float) -> float:
        """Get realistic speed based on vehicle type and distance"""
        base_speeds = {
            "bike": 15,      # km/h
            "scooter": 25,   # km/h  
            "car": 40,       # km/h
            "van": 35,       # km/h
            "truck": 30      # km/h
        }
        
        base_speed = base_speeds.get(vehicle_type, 20)
        
        # Adjust speed based on distance (longer distances = higher average speed)
        if distance > 20:
            base_speed *= 1.2  # Highway speeds
        elif distance < 2:
            base_speed *= 0.7  # City traffic
        
        return base_speed
    
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