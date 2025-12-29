import math
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import itertools

class MultiPackageOptimizer:
    def __init__(self):
        self.fuel_cost_per_km = 0.8  # MAD per km
        self.time_cost_per_minute = 0.5  # MAD per minute
        self.pickup_time = 5  # minutes
        self.delivery_time = 8  # minutes
        
    def optimize_multi_delivery_route(self, driver_location: Dict, orders: List[Dict]) -> Dict:
        """Optimize route for multiple packages using TSP algorithm"""
        if not orders:
            return {"route": [], "total_distance": 0, "total_time": 0, "total_cost": 0}
        
        # Separate pickups and deliveries
        pickups = [o for o in orders if o["status"] in ["assigned", "accepted"]]
        deliveries = [o for o in orders if o["status"] in ["picked_up", "in_transit"]]
        
        # Create location points
        points = [{"type": "start", "location": driver_location, "order_id": None}]
        
        # Add pickup points
        for order in pickups:
            points.append({
                "type": "pickup",
                "location": self._get_coordinates(order["pickup_address"], order["pickup_city"]),
                "order_id": order["id"],
                "order": order
            })
        
        # Add delivery points
        for order in deliveries:
            points.append({
                "type": "delivery", 
                "location": self._get_coordinates(order["delivery_address"], order["delivery_city"]),
                "order_id": order["id"],
                "order": order
            })
        
        # Optimize route using nearest neighbor with 2-opt improvement
        optimized_sequence = self._optimize_tsp(points)
        
        # Calculate route metrics
        route_data = self._calculate_route_metrics(optimized_sequence)
        
        return {
            "route": optimized_sequence,
            "total_distance": route_data["distance"],
            "total_time": route_data["time"],
            "total_cost": route_data["cost"],
            "fuel_savings": route_data["savings"],
            "efficiency_score": route_data["efficiency"]
        }
    
    def _optimize_tsp(self, points: List[Dict]) -> List[Dict]:
        """Traveling Salesman Problem optimization with constraints"""
        if len(points) <= 3:
            return points
        
        # Start with nearest neighbor
        route = self._nearest_neighbor(points)
        
        # Apply 2-opt improvement
        route = self._two_opt_improvement(route)
        
        # Apply pickup-delivery constraints
        route = self._apply_constraints(route)
        
        return route
    
    def _nearest_neighbor(self, points: List[Dict]) -> List[Dict]:
        """Nearest neighbor algorithm for initial route"""
        unvisited = points[1:].copy()  # Exclude start point
        route = [points[0]]  # Start with driver location
        current = points[0]
        
        while unvisited:
            nearest = min(unvisited, key=lambda p: self._calculate_distance(
                current["location"], p["location"]
            ))
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        return route
    
    def _two_opt_improvement(self, route: List[Dict]) -> List[Dict]:
        """2-opt algorithm to improve route efficiency"""
        best_route = route.copy()
        best_distance = self._calculate_total_distance(route)
        improved = True
        
        while improved:
            improved = False
            for i in range(1, len(route) - 2):
                for j in range(i + 1, len(route)):
                    if j - i == 1: continue
                    
                    new_route = route.copy()
                    new_route[i:j] = route[i:j][::-1]  # Reverse segment
                    
                    new_distance = self._calculate_total_distance(new_route)
                    if new_distance < best_distance:
                        best_route = new_route
                        best_distance = new_distance
                        improved = True
            
            route = best_route
        
        return best_route
    
    def _apply_constraints(self, route: List[Dict]) -> List[Dict]:
        """Apply pickup-before-delivery constraints"""
        # Group by order_id
        order_points = {}
        for point in route:
            if point["order_id"]:
                if point["order_id"] not in order_points:
                    order_points[point["order_id"]] = {}
                order_points[point["order_id"]][point["type"]] = point
        
        # Ensure pickup comes before delivery for each order
        constrained_route = [route[0]]  # Start point
        remaining = route[1:].copy()
        
        while remaining:
            # Find next valid point
            for point in remaining:
                if point["type"] == "pickup":
                    constrained_route.append(point)
                    remaining.remove(point)
                    break
                elif point["type"] == "delivery":
                    # Check if pickup is already done
                    order_id = point["order_id"]
                    pickup_done = any(p["order_id"] == order_id and p["type"] == "pickup" 
                                    for p in constrained_route)
                    if pickup_done:
                        constrained_route.append(point)
                        remaining.remove(point)
                        break
            else:
                # If no valid point found, add first remaining
                if remaining:
                    constrained_route.append(remaining.pop(0))
        
        return constrained_route
    
    def _calculate_route_metrics(self, route: List[Dict]) -> Dict:
        """Calculate comprehensive route metrics"""
        total_distance = self._calculate_total_distance(route)
        total_time = self._calculate_total_time(route)
        
        # Cost calculation
        fuel_cost = total_distance * self.fuel_cost_per_km
        time_cost = total_time * self.time_cost_per_minute
        total_cost = fuel_cost + time_cost
        
        # Calculate savings vs individual deliveries
        individual_cost = len([p for p in route if p["order_id"]]) * 25.0  # Base cost per delivery
        savings = max(0, individual_cost - total_cost)
        
        # Efficiency score (0-100)
        efficiency = min(100, (savings / individual_cost * 100) if individual_cost > 0 else 0)
        
        return {
            "distance": round(total_distance, 2),
            "time": round(total_time, 1),
            "cost": round(total_cost, 2),
            "savings": round(savings, 2),
            "efficiency": round(efficiency, 1)
        }
    
    def _calculate_total_distance(self, route: List[Dict]) -> float:
        """Calculate total route distance"""
        total = 0
        for i in range(len(route) - 1):
            total += self._calculate_distance(
                route[i]["location"], 
                route[i + 1]["location"]
            )
        return total
    
    def _calculate_total_time(self, route: List[Dict]) -> float:
        """Calculate total route time including stops"""
        travel_time = self._calculate_total_distance(route) * 2  # 2 min per km
        
        stop_time = 0
        for point in route[1:]:  # Exclude start point
            if point["type"] == "pickup":
                stop_time += self.pickup_time
            elif point["type"] == "delivery":
                stop_time += self.delivery_time
        
        return travel_time + stop_time
    
    def _calculate_distance(self, loc1: Dict, loc2: Dict) -> float:
        """Calculate distance between two coordinates"""
        R = 6371  # Earth radius in km
        lat1, lng1 = math.radians(loc1["lat"]), math.radians(loc1["lng"])
        lat2, lng2 = math.radians(loc2["lat"]), math.radians(loc2["lng"])
        
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _get_coordinates(self, address: str, city: str) -> Dict:
        """Get coordinates for address"""
        city_coords = {
            "casablanca": {"lat": 33.5731, "lng": -7.5898},
            "rabat": {"lat": 34.0209, "lng": -6.8416},
            "marrakech": {"lat": 31.6295, "lng": -7.9811},
            "el jadida": {"lat": 33.2316, "lng": -8.5007},
            "salé": {"lat": 34.0531, "lng": -6.7985},
            "agadir": {"lat": 30.4278, "lng": -9.5981}
        }
        
        base_coords = city_coords.get(city.lower(), city_coords["casablanca"])
        
        # Add small random offset for different addresses
        import random
        offset = 0.01
        return {
            "lat": base_coords["lat"] + random.uniform(-offset, offset),
            "lng": base_coords["lng"] + random.uniform(-offset, offset)
        }
    
    def calculate_batch_assignment_score(self, driver: Dict, new_orders: List[Dict]) -> float:
        """Calculate score for assigning multiple orders to driver"""
        current_orders = [o for o in new_orders if o.get("assigned_driver") == driver["id"]]
        all_orders = current_orders + new_orders
        
        if len(all_orders) > self._get_max_capacity(driver["vehicle_type"]):
            return 0  # Exceeds capacity
        
        # Calculate optimized route
        route_data = self.optimize_multi_delivery_route(
            driver["current_location"], 
            all_orders
        )
        
        # Score based on efficiency and capacity utilization
        efficiency_score = route_data["efficiency_score"]
        capacity_score = (len(all_orders) / self._get_max_capacity(driver["vehicle_type"])) * 100
        distance_penalty = max(0, 100 - route_data["total_distance"] * 2)
        
        return (efficiency_score * 0.5 + capacity_score * 0.3 + distance_penalty * 0.2)
    
    def _get_max_capacity(self, vehicle_type: str) -> int:
        """Get maximum package capacity per vehicle"""
        capacities = {"bike": 4, "scooter": 6, "car": 8, "van": 12}
        return capacities.get(vehicle_type, 4)