"""
Inter-City Delivery Workflow Manager
Handles multi-day warehouse-based logistics
"""
from datetime import datetime, timedelta
from typing import Dict, List

class InterCityWorkflow:
    def __init__(self, orders_db, drivers_db, warehouses_db):
        self.orders_db = orders_db
        self.drivers_db = drivers_db
        self.warehouses_db = warehouses_db
    
    async def process_inter_city_order(self, order: Dict) -> Dict:
        """
        Day 1: Pickup → Origin Warehouse
        Day 2-3: Warehouse → Destination City
        Day 4: Final Delivery
        """
        workflow_stages = {
            "day1_pickup": self._schedule_pickup_to_warehouse,
            "warehouse_consolidation": self._consolidate_at_warehouse,
            "inter_city_transport": self._schedule_inter_city_truck,
            "final_delivery": self._schedule_final_delivery
        }
        
        return {
            "order_id": order["id"],
            "workflow": "inter_city",
            "stages": workflow_stages,
            "estimated_days": 3
        }
    
    def _schedule_pickup_to_warehouse(self, order: Dict) -> Dict:
        """Day 1: Assign driver to pickup and deliver to origin warehouse"""
        origin_city = order["pickup_city"]
        
        # Find available driver in origin city
        available_drivers = [
            d for d in self.drivers_db 
            if d["assigned_city"] == origin_city and d["status"] == "available"
        ]
        
        if not available_drivers:
            return {"status": "no_driver", "retry_in": 30}
        
        # Assign driver for warehouse delivery
        driver = available_drivers[0]
        warehouse = next((w for w in self.warehouses_db if w["city"] == origin_city), None)
        
        return {
            "stage": "pickup_to_warehouse",
            "driver_id": driver["id"],
            "driver_name": driver["name"],
            "warehouse_id": warehouse["id"] if warehouse else None,
            "estimated_completion": (datetime.now() + timedelta(hours=4)).isoformat(),
            "status": "scheduled"
        }
    
    def _consolidate_at_warehouse(self, order: Dict) -> Dict:
        """Day 1-2: Package waits at warehouse for consolidation"""
        origin_warehouse = next(
            (w for w in self.warehouses_db if w["city"] == order["pickup_city"]), 
            None
        )
        
        if not origin_warehouse:
            return {"status": "no_warehouse"}
        
        # Check capacity
        current_load = origin_warehouse.get("current_packages", 0)
        capacity = origin_warehouse.get("capacity", 1000)
        
        if current_load >= capacity:
            return {"status": "warehouse_full", "retry_in": 120}
        
        # Update warehouse load
        origin_warehouse["current_packages"] = current_load + 1
        
        return {
            "stage": "warehouse_consolidation",
            "warehouse_id": origin_warehouse["id"],
            "warehouse_name": origin_warehouse["name"],
            "current_load": current_load + 1,
            "capacity": capacity,
            "next_truck_departure": self._get_next_truck_schedule(
                order["pickup_city"], 
                order["delivery_city"]
            ),
            "status": "consolidating"
        }
    
    def _schedule_inter_city_truck(self, order: Dict) -> Dict:
        """Day 2-3: Schedule inter-city truck transport"""
        schedule = self._get_next_truck_schedule(
            order["pickup_city"], 
            order["delivery_city"]
        )
        
        # Find packages going to same destination
        same_destination = [
            o for o in self.orders_db
            if o.get("pickup_city") == order["pickup_city"]
            and o.get("delivery_city") == order["delivery_city"]
            and o.get("status") == "at_origin_warehouse"
        ]
        
        return {
            "stage": "inter_city_transport",
            "departure_time": schedule["departure"],
            "arrival_time": schedule["arrival"],
            "duration_hours": schedule["duration"],
            "batch_size": len(same_destination),
            "truck_capacity": 50,
            "status": "scheduled"
        }
    
    def _schedule_final_delivery(self, order: Dict) -> Dict:
        """Day 4: Assign destination city driver for final delivery"""
        dest_city = order["delivery_city"]
        
        # Find available driver in destination city
        available_drivers = [
            d for d in self.drivers_db 
            if d["assigned_city"] == dest_city and d["status"] == "available"
        ]
        
        if not available_drivers:
            return {"status": "no_driver", "retry_in": 30}
        
        # Assign driver for final delivery
        driver = available_drivers[0]
        
        return {
            "stage": "final_delivery",
            "driver_id": driver["id"],
            "driver_name": driver["name"],
            "estimated_delivery": (datetime.now() + timedelta(hours=6)).isoformat(),
            "status": "scheduled"
        }
    
    def _get_next_truck_schedule(self, origin: str, destination: str) -> Dict:
        """Get next truck departure schedule"""
        schedules = {
            ("Casablanca", "Rabat"): {"departure": "08:00", "duration": 2},
            ("Casablanca", "Marrakech"): {"departure": "09:00", "duration": 4},
            ("Casablanca", "Agadir"): {"departure": "07:00", "duration": 6},
            ("Rabat", "Marrakech"): {"departure": "08:00", "duration": 4},
        }
        
        key = (origin, destination)
        schedule = schedules.get(key, {"departure": "08:00", "duration": 4})
        
        # Calculate arrival
        departure = datetime.now().replace(
            hour=int(schedule["departure"].split(":")[0]),
            minute=0
        )
        if departure < datetime.now():
            departure += timedelta(days=1)
        
        arrival = departure + timedelta(hours=schedule["duration"])
        
        return {
            "departure": departure.isoformat(),
            "arrival": arrival.isoformat(),
            "duration": schedule["duration"]
        }
    
    def update_order_status(self, order_id: str, new_status: str) -> Dict:
        """Update order status through workflow stages"""
        order = next((o for o in self.orders_db if o["id"] == order_id), None)
        if not order:
            return {"error": "Order not found"}
        
        status_flow = {
            "pending_assignment": "assigned_pickup",
            "assigned_pickup": "picked_up",
            "picked_up": "at_origin_warehouse",
            "at_origin_warehouse": "in_transit_inter_city",
            "in_transit_inter_city": "at_destination_warehouse",
            "at_destination_warehouse": "assigned_final_delivery",
            "assigned_final_delivery": "out_for_delivery",
            "out_for_delivery": "delivered"
        }
        
        order["status"] = new_status
        order["last_updated"] = datetime.now().isoformat()
        
        # Update warehouse counts
        if new_status == "at_origin_warehouse":
            self._increment_warehouse_load(order["pickup_city"])
        elif new_status == "in_transit_inter_city":
            self._decrement_warehouse_load(order["pickup_city"])
        elif new_status == "at_destination_warehouse":
            self._increment_warehouse_load(order["delivery_city"])
        elif new_status == "out_for_delivery":
            self._decrement_warehouse_load(order["delivery_city"])
        
        return {
            "order_id": order_id,
            "new_status": new_status,
            "next_status": status_flow.get(new_status),
            "updated_at": order["last_updated"]
        }
    
    def _increment_warehouse_load(self, city: str):
        warehouse = next((w for w in self.warehouses_db if w["city"] == city), None)
        if warehouse:
            warehouse["current_packages"] = warehouse.get("current_packages", 0) + 1
    
    def _decrement_warehouse_load(self, city: str):
        warehouse = next((w for w in self.warehouses_db if w["city"] == city), None)
        if warehouse and warehouse.get("current_packages", 0) > 0:
            warehouse["current_packages"] -= 1
