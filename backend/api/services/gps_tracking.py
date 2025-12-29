import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from core.websocket import manager
from api.models.tracking import TrackingEvent
from motor.motor_asyncio import AsyncIOMotorDatabase

class GPSTrackingService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.active_trackings = {}
        self.geofences = {}
        
    async def start_tracking(self, order_id: str, courier_id: str, route_data: Dict):
        """Start GPS tracking for an order"""
        
        tracking_session = {
            "order_id": order_id,
            "courier_id": courier_id,
            "route": route_data,
            "start_time": datetime.now(),
            "current_location": None,
            "last_update": None,
            "status": "active",
            "geofences": self._create_geofences(route_data)
        }
        
        self.active_trackings[order_id] = tracking_session
        
        # Create initial tracking event
        await self._create_tracking_event(order_id, {
            "event_type": "tracking_started",
            "location": route_data.get("origin"),
            "timestamp": datetime.now(),
            "details": {"courier_id": courier_id}
        })
        
        return tracking_session
    
    async def update_location(self, order_id: str, location_data: Dict):
        """Update courier location and trigger events"""
        
        if order_id not in self.active_trackings:
            return {"error": "Tracking session not found"}
            
        tracking = self.active_trackings[order_id]
        
        # Update location
        tracking["current_location"] = location_data
        tracking["last_update"] = datetime.now()
        
        # Check geofences
        geofence_events = await self._check_geofences(order_id, location_data)
        
        # Calculate ETA
        eta = await self._calculate_eta(tracking, location_data)
        
        # Create tracking event
        await self._create_tracking_event(order_id, {
            "event_type": "location_update",
            "location": location_data,
            "timestamp": datetime.now(),
            "eta": eta,
            "speed": location_data.get("speed", 0),
            "accuracy": location_data.get("accuracy", 0)
        })
        
        # Broadcast to customers and admin
        await self._broadcast_location_update(order_id, location_data, eta)
        
        # Handle geofence events
        for event in geofence_events:
            await self._handle_geofence_event(order_id, event)
            
        return {
            "status": "success",
            "current_location": location_data,
            "eta": eta,
            "geofence_events": geofence_events
        }
    
    def _create_geofences(self, route_data: Dict) -> List[Dict]:
        """Create geofences for pickup and delivery locations"""
        geofences = []
        
        # Pickup geofence
        if "origin" in route_data:
            geofences.append({
                "id": "pickup",
                "type": "pickup",
                "center": route_data["origin"],
                "radius": 100,  # 100 meters
                "triggered": False
            })
            
        # Delivery geofence
        if "destination" in route_data:
            geofences.append({
                "id": "delivery",
                "type": "delivery", 
                "center": route_data["destination"],
                "radius": 100,
                "triggered": False
            })
            
        return geofences
    
    async def _check_geofences(self, order_id: str, location: Dict) -> List[Dict]:
        """Check if courier entered any geofences"""
        events = []
        tracking = self.active_trackings[order_id]
        
        for geofence in tracking["geofences"]:
            if not geofence["triggered"]:
                distance = self._calculate_distance(
                    location, 
                    geofence["center"]
                )
                
                if distance <= geofence["radius"]:
                    geofence["triggered"] = True
                    events.append({
                        "type": f"{geofence['type']}_arrived",
                        "geofence_id": geofence["id"],
                        "location": location,
                        "timestamp": datetime.now()
                    })
                    
        return events
    
    def _calculate_distance(self, loc1: Dict, loc2: Dict) -> float:
        """Calculate distance between two GPS coordinates (Haversine formula)"""
        import math
        
        lat1, lon1 = loc1.get("lat", 0), loc1.get("lng", 0)
        lat2, lon2 = loc2.get("lat", 0), loc2.get("lng", 0)
        
        R = 6371000  # Earth radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    async def _calculate_eta(self, tracking: Dict, current_location: Dict) -> Dict:
        """Calculate estimated time of arrival"""
        route = tracking["route"]
        destination = route.get("destination", {})
        
        if not destination:
            return {"eta": None, "distance_remaining": 0}
            
        distance_remaining = self._calculate_distance(current_location, destination)
        
        # Estimate based on average speed and traffic
        avg_speed = 30  # km/h default
        current_speed = current_location.get("speed", 0)
        
        if current_speed > 5:  # Use current speed if moving
            estimated_speed = min(current_speed, 60)  # Cap at 60 km/h
        else:
            estimated_speed = avg_speed
            
        # Convert to hours
        time_remaining = (distance_remaining / 1000) / estimated_speed
        eta_datetime = datetime.now() + timedelta(hours=time_remaining)
        
        return {
            "eta": eta_datetime.isoformat(),
            "distance_remaining": distance_remaining,
            "estimated_speed": estimated_speed,
            "time_remaining_minutes": int(time_remaining * 60)
        }
    
    async def _create_tracking_event(self, order_id: str, event_data: Dict):
        """Create tracking event in database"""
        
        event = TrackingEvent(
            order_id=order_id,
            event_type=event_data["event_type"],
            location=event_data.get("location"),
            timestamp=event_data["timestamp"],
            details=event_data.get("details", {}),
            eta=event_data.get("eta"),
            speed=event_data.get("speed"),
            accuracy=event_data.get("accuracy")
        )
        
        await self.db.tracking_events.insert_one(event.dict())
    
    async def _broadcast_location_update(self, order_id: str, location: Dict, eta: Dict):
        """Broadcast location update to connected clients"""
        
        await manager.broadcast({
            "type": "location_update",
            "order_id": order_id,
            "location": location,
            "eta": eta,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _handle_geofence_event(self, order_id: str, event: Dict):
        """Handle geofence entry events"""
        
        if event["type"] == "pickup_arrived":
            await self._handle_pickup_arrival(order_id, event)
        elif event["type"] == "delivery_arrived":
            await self._handle_delivery_arrival(order_id, event)
    
    async def _handle_pickup_arrival(self, order_id: str, event: Dict):
        """Handle courier arrival at pickup location"""
        
        # Update order status
        await self.db.orders.update_one(
            {"_id": order_id},
            {"$set": {"status": "pickup_arrived"}}
        )
        
        # Notify customer
        await manager.broadcast({
            "type": "pickup_arrived",
            "order_id": order_id,
            "location": event["location"],
            "timestamp": event["timestamp"].isoformat(),
            "message": "Courier has arrived at pickup location"
        })
    
    async def _handle_delivery_arrival(self, order_id: str, event: Dict):
        """Handle courier arrival at delivery location"""
        
        # Update order status
        await self.db.orders.update_one(
            {"_id": order_id},
            {"$set": {"status": "delivery_arrived"}}
        )
        
        # Notify customer
        await manager.broadcast({
            "type": "delivery_arrived", 
            "order_id": order_id,
            "location": event["location"],
            "timestamp": event["timestamp"].isoformat(),
            "message": "Courier has arrived at delivery location"
        })
    
    async def complete_delivery(self, order_id: str, proof_data: Dict):
        """Complete delivery with proof"""
        
        if order_id not in self.active_trackings:
            return {"error": "Tracking session not found"}
            
        tracking = self.active_trackings[order_id]
        tracking["status"] = "completed"
        tracking["end_time"] = datetime.now()
        
        # Create completion event
        await self._create_tracking_event(order_id, {
            "event_type": "delivery_completed",
            "location": tracking["current_location"],
            "timestamp": datetime.now(),
            "details": proof_data
        })
        
        # Update order status
        await self.db.orders.update_one(
            {"_id": order_id},
            {
                "$set": {
                    "status": "delivered",
                    "delivered_at": datetime.now(),
                    "proof_of_delivery": proof_data
                }
            }
        )
        
        # Notify customer
        await manager.broadcast({
            "type": "delivery_completed",
            "order_id": order_id,
            "proof": proof_data,
            "timestamp": datetime.now().isoformat(),
            "message": "Package delivered successfully!"
        })
        
        # Stop tracking
        del self.active_trackings[order_id]
        
        return {"status": "success", "message": "Delivery completed"}
    
    async def get_tracking_history(self, order_id: str) -> List[Dict]:
        """Get tracking history for an order"""
        
        events = await self.db.tracking_events.find(
            {"order_id": order_id}
        ).sort("timestamp", 1).to_list(None)
        
        return events
    
    def stop_tracking(self, order_id: str):
        """Stop tracking for an order"""
        if order_id in self.active_trackings:
            self.active_trackings[order_id]["status"] = "stopped"
            del self.active_trackings[order_id]