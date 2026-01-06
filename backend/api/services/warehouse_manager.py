"""
Warehouse Management System
Handles package consolidation, capacity, and batch scheduling
"""
from datetime import datetime, timedelta
from typing import Dict, List

class WarehouseManager:
    def __init__(self, warehouses_db, orders_db):
        self.warehouses_db = warehouses_db
        self.orders_db = orders_db
    
    def receive_package(self, order_id: str, warehouse_city: str) -> Dict:
        """Receive package at warehouse"""
        warehouse = self._get_warehouse(warehouse_city)
        if not warehouse:
            return {"error": "Warehouse not found"}
        
        # Check capacity
        if warehouse["current_packages"] >= warehouse["capacity"]:
            return {"error": "Warehouse at capacity", "retry_in": 120}
        
        # Update warehouse
        warehouse["current_packages"] += 1
        
        # Update order
        order = next((o for o in self.orders_db if o["id"] == order_id), None)
        if order:
            order["status"] = "at_origin_warehouse"
            order["warehouse_arrival"] = datetime.now().isoformat()
            order["current_warehouse"] = warehouse_city
        
        return {
            "status": "received",
            "warehouse": warehouse["name"],
            "current_load": warehouse["current_packages"],
            "capacity": warehouse["capacity"],
            "utilization": round(warehouse["current_packages"] / warehouse["capacity"] * 100, 1)
        }
    
    def consolidate_batch(self, origin_city: str, destination_city: str) -> Dict:
        """Consolidate packages for same destination"""
        # Find all packages at origin warehouse going to destination
        packages = [
            o for o in self.orders_db
            if o.get("current_warehouse") == origin_city
            and o.get("delivery_city") == destination_city
            and o.get("status") == "at_origin_warehouse"
        ]
        
        if not packages:
            return {"batch_size": 0, "status": "no_packages"}
        
        # Calculate total weight and volume
        total_weight = sum(p.get("weight", 0) for p in packages)
        total_volume = sum(
            p.get("dimensions", {}).get("length", 0) *
            p.get("dimensions", {}).get("width", 0) *
            p.get("dimensions", {}).get("height", 0) / 1000000
            for p in packages
        )
        
        # Determine truck type needed
        truck_type = self._select_truck_type(total_weight, total_volume)
        
        return {
            "batch_size": len(packages),
            "package_ids": [p["id"] for p in packages],
            "total_weight": round(total_weight, 2),
            "total_volume": round(total_volume, 2),
            "truck_type": truck_type,
            "ready_for_dispatch": len(packages) >= 5 or total_weight >= 100,
            "status": "consolidated"
        }
    
    def schedule_dispatch(self, origin_city: str, destination_city: str) -> Dict:
        """Schedule inter-city truck dispatch"""
        batch = self.consolidate_batch(origin_city, destination_city)
        
        if batch["batch_size"] == 0:
            return {"error": "No packages to dispatch"}
        
        # Get next available truck schedule
        schedule = self._get_truck_schedule(origin_city, destination_city)
        
        # Update all packages in batch
        for package_id in batch["package_ids"]:
            order = next((o for o in self.orders_db if o["id"] == package_id), None)
            if order:
                order["status"] = "in_transit_inter_city"
                order["dispatch_time"] = datetime.now().isoformat()
                order["estimated_arrival"] = schedule["arrival"]
        
        # Update origin warehouse
        origin_wh = self._get_warehouse(origin_city)
        if origin_wh:
            origin_wh["current_packages"] -= batch["batch_size"]
        
        return {
            "status": "dispatched",
            "batch_size": batch["batch_size"],
            "departure": schedule["departure"],
            "arrival": schedule["arrival"],
            "duration_hours": schedule["duration"],
            "truck_type": batch["truck_type"]
        }
    
    def receive_at_destination(self, origin_city: str, destination_city: str) -> Dict:
        """Receive batch at destination warehouse"""
        # Find packages in transit to this destination
        packages = [
            o for o in self.orders_db
            if o.get("pickup_city") == origin_city
            and o.get("delivery_city") == destination_city
            and o.get("status") == "in_transit_inter_city"
        ]
        
        dest_wh = self._get_warehouse(destination_city)
        if not dest_wh:
            return {"error": "Destination warehouse not found"}
        
        # Update packages
        for order in packages:
            order["status"] = "at_destination_warehouse"
            order["warehouse_arrival"] = datetime.now().isoformat()
            order["current_warehouse"] = destination_city
        
        # Update warehouse
        dest_wh["current_packages"] += len(packages)
        
        return {
            "status": "received",
            "packages_received": len(packages),
            "warehouse": dest_wh["name"],
            "current_load": dest_wh["current_packages"]
        }
    
    def assign_final_delivery(self, order_id: str, drivers_db: List) -> Dict:
        """Assign driver for final delivery from destination warehouse"""
        order = next((o for o in self.orders_db if o["id"] == order_id), None)
        if not order or order["status"] != "at_destination_warehouse":
            return {"error": "Order not ready for final delivery"}
        
        # Find available driver in destination city
        dest_city = order["delivery_city"]
        available_drivers = [
            d for d in drivers_db
            if d["assigned_city"] == dest_city
            and d["status"] == "available"
            and len(d["current_orders"]) < 5
        ]
        
        if not available_drivers:
            return {"error": "No available drivers", "retry_in": 30}
        
        # Select best driver (closest, highest rating)
        driver = sorted(
            available_drivers,
            key=lambda d: (-d["rating"], len(d["current_orders"]))
        )[0]
        
        # Assign
        order["assigned_driver"] = driver["id"]
        order["status"] = "out_for_delivery"
        order["final_delivery_assigned"] = datetime.now().isoformat()
        driver["current_orders"].append(order_id)
        driver["status"] = "busy"
        
        # Update warehouse
        dest_wh = self._get_warehouse(dest_city)
        if dest_wh:
            dest_wh["current_packages"] -= 1
        
        return {
            "status": "assigned",
            "driver_id": driver["id"],
            "driver_name": driver["name"],
            "vehicle_type": driver["vehicle_type"],
            "estimated_delivery": (datetime.now() + timedelta(hours=2)).isoformat()
        }
    
    def _get_warehouse(self, city: str) -> Dict:
        """Get warehouse by city"""
        return next((w for w in self.warehouses_db if w["city"] == city), None)
    
    def _select_truck_type(self, weight: float, volume: float) -> str:
        """Select appropriate truck type"""
        if weight > 500 or volume > 20:
            return "large_truck"
        elif weight > 200 or volume > 10:
            return "medium_truck"
        else:
            return "small_truck"
    
    def _get_truck_schedule(self, origin: str, destination: str) -> Dict:
        """Get truck schedule between cities"""
        schedules = {
            ("Casablanca", "Rabat"): {"departure_hour": 8, "duration": 2},
            ("Casablanca", "Marrakech"): {"departure_hour": 9, "duration": 4},
            ("Casablanca", "Agadir"): {"departure_hour": 7, "duration": 6},
            ("Rabat", "Marrakech"): {"departure_hour": 8, "duration": 4},
        }
        
        key = (origin, destination)
        schedule = schedules.get(key, {"departure_hour": 8, "duration": 4})
        
        # Calculate next departure
        now = datetime.now()
        departure = now.replace(hour=schedule["departure_hour"], minute=0, second=0)
        if departure < now:
            departure += timedelta(days=1)
        
        arrival = departure + timedelta(hours=schedule["duration"])
        
        return {
            "departure": departure.isoformat(),
            "arrival": arrival.isoformat(),
            "duration": schedule["duration"]
        }
    
    def get_warehouse_status(self, city: str) -> Dict:
        """Get warehouse status and statistics"""
        warehouse = self._get_warehouse(city)
        if not warehouse:
            return {"error": "Warehouse not found"}
        
        # Count packages by status
        packages_at_warehouse = [
            o for o in self.orders_db
            if o.get("current_warehouse") == city
        ]
        
        by_status = {}
        for order in packages_at_warehouse:
            status = order.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "warehouse": warehouse["name"],
            "city": city,
            "capacity": warehouse["capacity"],
            "current_packages": warehouse["current_packages"],
            "utilization": round(warehouse["current_packages"] / warehouse["capacity"] * 100, 1),
            "packages_by_status": by_status,
            "operating_hours": warehouse.get("operating_hours", "24/7"),
            "facilities": warehouse.get("facilities", [])
        }
