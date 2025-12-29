import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
from core.websocket import manager
from motor.motor_asyncio import AsyncIOMotorDatabase

class PackageStatus(str, Enum):
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    SORTED = "sorted"
    LOADED = "loaded"
    DEPARTED = "departed"

class WarehouseManagementService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.warehouses = {}
        self.package_tracking = {}
        
    async def initialize_warehouses(self):
        """Initialize warehouse locations and capacities"""
        
        default_warehouses = [
            {
                "id": "WH_NYC_001",
                "name": "New York Central Hub",
                "location": {"lat": 40.7128, "lng": -74.0060},
                "capacity": 10000,
                "current_load": 0,
                "services": ["sorting", "storage", "customs"],
                "operating_hours": {"start": 6, "end": 22},
                "processing_time": 2  # hours
            },
            {
                "id": "WH_LA_001", 
                "name": "Los Angeles Distribution Center",
                "location": {"lat": 34.0522, "lng": -118.2437},
                "capacity": 8000,
                "current_load": 0,
                "services": ["sorting", "storage"],
                "operating_hours": {"start": 5, "end": 23},
                "processing_time": 1.5
            },
            {
                "id": "WH_CHI_001",
                "name": "Chicago Logistics Hub", 
                "location": {"lat": 41.8781, "lng": -87.6298},
                "capacity": 12000,
                "current_load": 0,
                "services": ["sorting", "storage", "customs", "rail_transfer"],
                "operating_hours": {"start": 24, "end": 24},  # 24/7
                "processing_time": 3
            }
        ]
        
        for warehouse in default_warehouses:
            self.warehouses[warehouse["id"]] = warehouse
            
        # Store in database
        await self.db.warehouses.delete_many({})
        await self.db.warehouses.insert_many(default_warehouses)
    
    async def route_package_to_warehouse(self, order_id: str, origin: str, destination: str) -> Dict:
        """Determine optimal warehouse route for inter-city delivery"""
        
        # Find best warehouse chain
        route_chain = await self._calculate_warehouse_chain(origin, destination)
        
        # Create package tracking entry
        package_info = {
            "order_id": order_id,
            "route_chain": route_chain,
            "current_warehouse": None,
            "status": PackageStatus.IN_TRANSIT,
            "created_at": datetime.now(),
            "estimated_delivery": self._calculate_total_eta(route_chain)
        }
        
        self.package_tracking[order_id] = package_info
        
        # Store in database
        await self.db.package_tracking.insert_one(package_info)
        
        return {
            "route_chain": route_chain,
            "estimated_delivery": package_info["estimated_delivery"],
            "total_warehouses": len(route_chain),
            "total_distance": sum(leg["distance"] for leg in route_chain)
        }
    
    async def _calculate_warehouse_chain(self, origin: str, destination: str) -> List[Dict]:
        """Calculate optimal warehouse chain for delivery"""
        
        # Simple implementation - in production, use advanced routing algorithms
        route_chain = []
        
        # Find nearest warehouse to origin
        origin_warehouse = await self._find_nearest_warehouse(origin)
        if origin_warehouse:
            route_chain.append({
                "warehouse_id": origin_warehouse["id"],
                "warehouse_name": origin_warehouse["name"],
                "location": origin_warehouse["location"],
                "services": origin_warehouse["services"],
                "processing_time": origin_warehouse["processing_time"],
                "distance": self._calculate_distance_to_warehouse(origin, origin_warehouse),
                "transport_mode": "truck"
            })
        
        # Find destination warehouse
        dest_warehouse = await self._find_nearest_warehouse(destination)
        if dest_warehouse and dest_warehouse["id"] != origin_warehouse["id"]:
            route_chain.append({
                "warehouse_id": dest_warehouse["id"],
                "warehouse_name": dest_warehouse["name"],
                "location": dest_warehouse["location"],
                "services": dest_warehouse["services"],
                "processing_time": dest_warehouse["processing_time"],
                "distance": self._calculate_warehouse_distance(origin_warehouse, dest_warehouse),
                "transport_mode": self._determine_transport_mode(origin_warehouse, dest_warehouse)
            })
            
        return route_chain
    
    async def _find_nearest_warehouse(self, location: str) -> Optional[Dict]:
        """Find nearest warehouse to a location"""
        
        # In production, use geocoding and distance calculation
        # For now, return first available warehouse
        available_warehouses = [wh for wh in self.warehouses.values() 
                              if wh["current_load"] < wh["capacity"] * 0.9]
        
        return available_warehouses[0] if available_warehouses else None
    
    def _calculate_distance_to_warehouse(self, location: str, warehouse: Dict) -> float:
        """Calculate distance from location to warehouse"""
        # Simplified - in production use actual geocoding
        return 50.0  # km
    
    def _calculate_warehouse_distance(self, wh1: Dict, wh2: Dict) -> float:
        """Calculate distance between warehouses"""
        # Simplified distance calculation
        import math
        
        lat1, lon1 = wh1["location"]["lat"], wh1["location"]["lng"]
        lat2, lon2 = wh2["location"]["lat"], wh2["location"]["lng"]
        
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _determine_transport_mode(self, origin_wh: Dict, dest_wh: Dict) -> str:
        """Determine best transport mode between warehouses"""
        
        distance = self._calculate_warehouse_distance(origin_wh, dest_wh)
        
        if distance > 1000:  # > 1000km
            if "rail_transfer" in origin_wh["services"] and "rail_transfer" in dest_wh["services"]:
                return "rail"
            else:
                return "air"
        elif distance > 500:  # 500-1000km
            return "truck_long"
        else:
            return "truck"
    
    def _calculate_total_eta(self, route_chain: List[Dict]) -> datetime:
        """Calculate total estimated delivery time"""
        
        total_hours = 0
        
        for leg in route_chain:
            # Transport time
            distance = leg["distance"]
            transport_mode = leg["transport_mode"]
            
            if transport_mode == "air":
                speed = 500  # km/h
            elif transport_mode == "rail":
                speed = 80   # km/h
            elif transport_mode == "truck_long":
                speed = 70   # km/h
            else:
                speed = 50   # km/h
                
            transport_time = distance / speed
            processing_time = leg["processing_time"]
            
            total_hours += transport_time + processing_time
        
        return datetime.now() + timedelta(hours=total_hours)
    
    async def package_arrived_at_warehouse(self, order_id: str, warehouse_id: str, 
                                         arrival_data: Dict) -> Dict:
        """Handle package arrival at warehouse"""
        
        if order_id not in self.package_tracking:
            return {"error": "Package not found in tracking system"}
            
        package = self.package_tracking[order_id]
        package["current_warehouse"] = warehouse_id
        package["status"] = PackageStatus.ARRIVED
        
        # Update warehouse load
        if warehouse_id in self.warehouses:
            self.warehouses[warehouse_id]["current_load"] += 1
        
        # Create warehouse event
        await self._create_warehouse_event(order_id, {
            "event_type": "package_arrived",
            "warehouse_id": warehouse_id,
            "timestamp": datetime.now(),
            "details": arrival_data
        })
        
        # Start processing
        await self._start_warehouse_processing(order_id, warehouse_id)
        
        # Notify customer
        await manager.broadcast({
            "type": "warehouse_arrival",
            "order_id": order_id,
            "warehouse": self.warehouses[warehouse_id]["name"],
            "status": "Package arrived at warehouse",
            "timestamp": datetime.now().isoformat()
        })
        
        return {"status": "success", "message": "Package arrived at warehouse"}
    
    async def _start_warehouse_processing(self, order_id: str, warehouse_id: str):
        """Start warehouse processing (sorting, customs, etc.)"""
        
        warehouse = self.warehouses[warehouse_id]
        processing_time = warehouse["processing_time"]
        
        # Schedule processing completion
        asyncio.create_task(
            self._complete_warehouse_processing(order_id, warehouse_id, processing_time)
        )
        
        # Update status
        package = self.package_tracking[order_id]
        package["status"] = PackageStatus.SORTED
        
        await self._create_warehouse_event(order_id, {
            "event_type": "processing_started",
            "warehouse_id": warehouse_id,
            "timestamp": datetime.now(),
            "estimated_completion": datetime.now() + timedelta(hours=processing_time)
        })
    
    async def _complete_warehouse_processing(self, order_id: str, warehouse_id: str, 
                                           processing_hours: float):
        """Complete warehouse processing after delay"""
        
        # Wait for processing time
        await asyncio.sleep(processing_hours * 3600)  # Convert to seconds
        
        if order_id not in self.package_tracking:
            return
            
        package = self.package_tracking[order_id]
        package["status"] = PackageStatus.LOADED
        
        # Update warehouse load
        if warehouse_id in self.warehouses:
            self.warehouses[warehouse_id]["current_load"] -= 1
        
        await self._create_warehouse_event(order_id, {
            "event_type": "processing_completed",
            "warehouse_id": warehouse_id,
            "timestamp": datetime.now()
        })
        
        # Check if this is the final warehouse
        route_chain = package["route_chain"]
        current_index = next((i for i, leg in enumerate(route_chain) 
                            if leg["warehouse_id"] == warehouse_id), -1)
        
        if current_index == len(route_chain) - 1:
            # Final warehouse - ready for local delivery
            await self._prepare_for_local_delivery(order_id)
        else:
            # Move to next warehouse
            await self._dispatch_to_next_warehouse(order_id, current_index)
    
    async def _prepare_for_local_delivery(self, order_id: str):
        """Prepare package for final local delivery"""
        
        package = self.package_tracking[order_id]
        package["status"] = PackageStatus.DEPARTED
        
        await self._create_warehouse_event(order_id, {
            "event_type": "ready_for_delivery",
            "timestamp": datetime.now()
        })
        
        # Notify local delivery system
        await manager.broadcast({
            "type": "ready_for_local_delivery",
            "order_id": order_id,
            "message": "Package ready for final delivery",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _dispatch_to_next_warehouse(self, order_id: str, current_index: int):
        """Dispatch package to next warehouse in chain"""
        
        package = self.package_tracking[order_id]
        route_chain = package["route_chain"]
        
        if current_index + 1 < len(route_chain):
            next_warehouse = route_chain[current_index + 1]
            
            package["status"] = PackageStatus.IN_TRANSIT
            
            await self._create_warehouse_event(order_id, {
                "event_type": "dispatched_to_next_warehouse",
                "next_warehouse_id": next_warehouse["warehouse_id"],
                "transport_mode": next_warehouse["transport_mode"],
                "timestamp": datetime.now()
            })
            
            # Notify customer
            await manager.broadcast({
                "type": "warehouse_dispatch",
                "order_id": order_id,
                "destination": next_warehouse["warehouse_name"],
                "transport_mode": next_warehouse["transport_mode"],
                "timestamp": datetime.now().isoformat()
            })
    
    async def _create_warehouse_event(self, order_id: str, event_data: Dict):
        """Create warehouse event in database"""
        
        event = {
            "order_id": order_id,
            "event_type": event_data["event_type"],
            "warehouse_id": event_data.get("warehouse_id"),
            "timestamp": event_data["timestamp"],
            "details": event_data.get("details", {}),
            "next_warehouse_id": event_data.get("next_warehouse_id"),
            "transport_mode": event_data.get("transport_mode")
        }
        
        await self.db.warehouse_events.insert_one(event)
    
    async def get_warehouse_status(self, warehouse_id: str) -> Dict:
        """Get current warehouse status"""
        
        if warehouse_id not in self.warehouses:
            return {"error": "Warehouse not found"}
            
        warehouse = self.warehouses[warehouse_id]
        
        # Get current packages
        current_packages = [
            pkg for pkg in self.package_tracking.values()
            if pkg["current_warehouse"] == warehouse_id
        ]
        
        return {
            "warehouse": warehouse,
            "current_packages": len(current_packages),
            "capacity_utilization": warehouse["current_load"] / warehouse["capacity"] * 100,
            "packages": current_packages
        }
    
    async def get_package_warehouse_history(self, order_id: str) -> List[Dict]:
        """Get warehouse history for a package"""
        
        events = await self.db.warehouse_events.find(
            {"order_id": order_id}
        ).sort("timestamp", 1).to_list(None)
        
        return events