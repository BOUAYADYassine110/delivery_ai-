import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from core.database import get_database
from api.services.real_time_routing import routing_service
from api.services.gps_tracking import GPSTrackingService
from api.services.warehouse_management import WarehouseManagementService
from api.services.notification_service import NotificationService, NotificationType
from api.services.intra_city_workflow import IntraCityWorkflow
from api.services.inter_city_workflow import InterCityWorkflow

class EnhancedDeliveryWorkflow:
    def __init__(self, db):
        self.db = db
        self.gps_service = GPSTrackingService(db)
        self.warehouse_service = WarehouseManagementService(db)
        self.notification_service = NotificationService(db)
        self.intra_city_workflow = IntraCityWorkflow()
        self.inter_city_workflow = InterCityWorkflow()
        
    async def process_enhanced_order(self, order_data: Dict) -> Dict:
        """Process order with enhanced features based on delivery type"""
        
        order_type = order_data.get("order_type", "intra_city")
        
        if order_type == "intra_city":
            return await self._process_intra_city_enhanced(order_data)
        else:
            return await self._process_inter_city_enhanced(order_data)
    
    async def _process_intra_city_enhanced(self, order_data: Dict) -> Dict:
        """Enhanced intra-city delivery processing"""
        
        try:
            # Step 1: Basic order validation and processing
            basic_result = await self.intra_city_workflow.process_new_order(order_data)
            
            if basic_result["status"] != "success":
                return basic_result
            
            order_id = order_data.get("order_id")
            
            # Step 2: Calculate optimal route with real-time data
            optimal_route = await routing_service.calculate_optimal_route(
                order_data.get("pickup_address"),
                order_data.get("delivery_address")
            )
            
            # Step 3: Find and assign best courier
            best_courier = await self._find_optimal_courier(order_data, optimal_route)
            
            if not best_courier:
                return {"status": "error", "message": "No available couriers"}
            
            # Step 4: Update order with enhanced data
            await self.db.orders.update_one(
                {"_id": order_id},
                {
                    "$set": {
                        "courier_id": best_courier["courier_id"],
                        "optimal_route": optimal_route,
                        "estimated_delivery_time": optimal_route.get("estimated_time"),
                        "route_score": optimal_route.get("score"),
                        "status": "courier_assigned",
                        "updated_at": datetime.now()
                    }
                }
            )
            
            # Step 5: Start enhanced tracking
            tracking_session = await self.gps_service.start_tracking(
                order_id,
                best_courier["courier_id"],
                optimal_route
            )
            
            # Step 6: Start route monitoring
            asyncio.create_task(
                routing_service.monitor_active_route(order_id, optimal_route)
            )
            
            # Step 7: Send notifications
            await self.notification_service.send_notification(
                str(order_data.get("customer_id")),
                NotificationType.COURIER_ASSIGNED,
                {"order_id": order_id},
                {
                    "courier_name": best_courier.get("name", "Unknown"),
                    "courier_phone": best_courier.get("phone", "N/A"),
                    "eta": optimal_route.get("estimated_time", "Unknown")
                }
            )
            
            return {
                "status": "success",
                "order_id": order_id,
                "courier": best_courier,
                "route": optimal_route,
                "tracking_session": tracking_session,
                "message": "Enhanced intra-city delivery initiated"
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Enhanced workflow error: {str(e)}"}
    
    async def _process_inter_city_enhanced(self, order_data: Dict) -> Dict:
        """Enhanced inter-city delivery processing"""
        
        try:
            # Step 1: Basic inter-city processing
            basic_result = await self.inter_city_workflow.process_new_order(order_data)
            
            if basic_result["status"] != "success":
                return basic_result
            
            order_id = order_data.get("order_id")
            
            # Step 2: Route through warehouse system
            warehouse_route = await self.warehouse_service.route_package_to_warehouse(
                order_id,
                order_data.get("pickup_address"),
                order_data.get("delivery_address")
            )
            
            # Step 3: Calculate initial local pickup route
            pickup_route = await routing_service.calculate_optimal_route(
                order_data.get("pickup_address"),
                warehouse_route["route_chain"][0]["location"] if warehouse_route["route_chain"] else order_data.get("pickup_address")
            )
            
            # Step 4: Assign local pickup courier
            pickup_courier = await self._find_optimal_courier(order_data, pickup_route)
            
            if not pickup_courier:
                return {"status": "error", "message": "No available pickup couriers"}
            
            # Step 5: Update order with warehouse routing
            await self.db.orders.update_one(
                {"_id": order_id},
                {
                    "$set": {
                        "pickup_courier_id": pickup_courier["courier_id"],
                        "warehouse_route": warehouse_route,
                        "pickup_route": pickup_route,
                        "status": "pickup_courier_assigned",
                        "estimated_delivery": warehouse_route["estimated_delivery"],
                        "updated_at": datetime.now()
                    }
                }
            )
            
            # Step 6: Start pickup tracking
            pickup_tracking = await self.gps_service.start_tracking(
                f"{order_id}_pickup",
                pickup_courier["courier_id"],
                pickup_route
            )
            
            # Step 7: Send notifications
            await self.notification_service.send_notification(
                str(order_data.get("customer_id")),
                NotificationType.COURIER_ASSIGNED,
                {"order_id": order_id},
                {
                    "courier_name": pickup_courier.get("name", "Unknown"),
                    "courier_phone": pickup_courier.get("phone", "N/A"),
                    "delivery_type": "Inter-city pickup",
                    "estimated_delivery": warehouse_route["estimated_delivery"].isoformat()
                }
            )
            
            return {
                "status": "success",
                "order_id": order_id,
                "pickup_courier": pickup_courier,
                "warehouse_route": warehouse_route,
                "pickup_tracking": pickup_tracking,
                "message": "Enhanced inter-city delivery initiated"
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Enhanced inter-city workflow error: {str(e)}"}
    
    async def _find_optimal_courier(self, order_data: Dict, route_data: Dict) -> Optional[Dict]:
        """Find optimal courier based on location, availability, and performance"""
        
        # Get available couriers
        available_couriers = await self.db.couriers.find({
            "is_active": True,
            "status": "available"
        }).to_list(None)
        
        if not available_couriers:
            return None
        
        pickup_location = order_data.get("pickup_address")
        best_courier = None
        best_score = 0
        
        for courier in available_couriers:
            # Calculate courier score based on multiple factors
            score = await self._calculate_courier_score(courier, pickup_location, route_data)
            
            if score > best_score:
                best_score = score
                best_courier = courier
        
        return best_courier
    
    async def _calculate_courier_score(self, courier: Dict, pickup_location: str, 
                                     route_data: Dict) -> float:
        """Calculate courier suitability score"""
        
        score = 0
        
        # Distance factor (closer is better)
        courier_location = courier.get("current_location", {})
        if courier_location:
            # Simplified distance calculation
            distance_score = max(0, 100 - (courier_location.get("distance_to_pickup", 50) * 2))
            score += distance_score * 0.4
        
        # Performance rating factor
        rating = courier.get("rating", 3.0)
        rating_score = (rating / 5.0) * 100
        score += rating_score * 0.3
        
        # Experience factor
        completed_deliveries = courier.get("completed_deliveries", 0)
        experience_score = min(100, completed_deliveries * 2)
        score += experience_score * 0.2
        
        # Vehicle type suitability
        vehicle_type = courier.get("vehicle_type", "bike")
        route_distance = route_data.get("distance", 0)
        
        if route_distance > 20000 and vehicle_type in ["car", "van"]:  # > 20km
            score += 10
        elif route_distance <= 5000 and vehicle_type in ["bike", "scooter"]:  # <= 5km
            score += 10
        
        return score
    
    async def handle_delivery_milestone(self, order_id: str, milestone: str, 
                                      data: Dict = None) -> Dict:
        """Handle delivery milestones with enhanced processing"""
        
        if data is None:
            data = {}
        
        # Get order details
        order = await self.db.orders.find_one({"_id": order_id})
        if not order:
            return {"error": "Order not found"}
        
        order_type = order.get("order_type", "intra_city")
        
        if milestone == "package_picked_up":
            return await self._handle_pickup_completion(order_id, order_type, data)
        elif milestone == "arrived_at_warehouse":
            return await self._handle_warehouse_arrival(order_id, data)
        elif milestone == "departed_warehouse":
            return await self._handle_warehouse_departure(order_id, data)
        elif milestone == "delivery_completed":
            return await self._handle_delivery_completion(order_id, order_type, data)
        else:
            return {"error": f"Unknown milestone: {milestone}"}
    
    async def _handle_pickup_completion(self, order_id: str, order_type: str, data: Dict) -> Dict:
        """Handle package pickup completion"""
        
        # Update order status
        await self.db.orders.update_one(
            {"_id": order_id},
            {
                "$set": {
                    "status": "picked_up",
                    "pickup_time": datetime.now(),
                    "pickup_proof": data.get("proof", {})
                }
            }
        )
        
        # Send notification
        await self.notification_service.send_notification(
            str(data.get("customer_id")),
            NotificationType.PACKAGE_PICKED_UP,
            {"order_id": order_id}
        )
        
        if order_type == "inter_city":
            # For inter-city, start warehouse routing
            return await self._initiate_warehouse_transport(order_id, data)
        else:
            # For intra-city, continue with direct delivery
            return {"status": "success", "message": "Package picked up, en route to delivery"}
    
    async def _initiate_warehouse_transport(self, order_id: str, data: Dict) -> Dict:
        """Initiate transport to warehouse for inter-city delivery"""
        
        order = await self.db.orders.find_one({"_id": order_id})
        warehouse_route = order.get("warehouse_route", {})
        
        if not warehouse_route or not warehouse_route.get("route_chain"):
            return {"error": "No warehouse route found"}
        
        first_warehouse = warehouse_route["route_chain"][0]
        
        # Simulate package arrival at warehouse (in production, this would be triggered by actual transport)
        asyncio.create_task(
            self._simulate_warehouse_arrival(order_id, first_warehouse["warehouse_id"], 2)  # 2 hours
        )
        
        return {
            "status": "success",
            "message": "Package en route to warehouse",
            "destination_warehouse": first_warehouse["warehouse_name"]
        }
    
    async def _simulate_warehouse_arrival(self, order_id: str, warehouse_id: str, hours: float):
        """Simulate package arrival at warehouse after transport time"""
        
        await asyncio.sleep(hours * 3600)  # Convert to seconds
        
        # Trigger warehouse arrival
        await self.warehouse_service.package_arrived_at_warehouse(
            order_id,
            warehouse_id,
            {
                "arrival_time": datetime.now(),
                "transport_mode": "truck",
                "condition": "good"
            }
        )
    
    async def _handle_warehouse_arrival(self, order_id: str, data: Dict) -> Dict:
        """Handle package arrival at warehouse"""
        
        warehouse_id = data.get("warehouse_id")
        
        # Process through warehouse system
        result = await self.warehouse_service.package_arrived_at_warehouse(
            order_id, warehouse_id, data
        )
        
        return result
    
    async def _handle_warehouse_departure(self, order_id: str, data: Dict) -> Dict:
        """Handle package departure from warehouse"""
        
        # Update order status
        await self.db.orders.update_one(
            {"_id": order_id},
            {
                "$set": {
                    "status": "departed_warehouse",
                    "warehouse_departure_time": datetime.now()
                }
            }
        )
        
        # Check if this is final warehouse (ready for local delivery)
        order = await self.db.orders.find_one({"_id": order_id})
        warehouse_route = order.get("warehouse_route", {})
        
        if data.get("is_final_warehouse", False):
            # Start local delivery process
            return await self._initiate_final_delivery(order_id, data)
        
        return {"status": "success", "message": "Package departed warehouse"}
    
    async def _initiate_final_delivery(self, order_id: str, data: Dict) -> Dict:
        """Initiate final local delivery from last warehouse"""
        
        order = await self.db.orders.find_one({"_id": order_id})
        
        # Calculate final delivery route
        final_route = await routing_service.calculate_optimal_route(
            data.get("warehouse_location"),
            order.get("delivery_address")
        )
        
        # Find delivery courier
        delivery_courier = await self._find_optimal_courier(order, final_route)
        
        if not delivery_courier:
            return {"error": "No available delivery couriers"}
        
        # Update order
        await self.db.orders.update_one(
            {"_id": order_id},
            {
                "$set": {
                    "delivery_courier_id": delivery_courier["courier_id"],
                    "final_delivery_route": final_route,
                    "status": "out_for_delivery"
                }
            }
        )
        
        # Start final delivery tracking
        await self.gps_service.start_tracking(
            f"{order_id}_delivery",
            delivery_courier["courier_id"],
            final_route
        )
        
        # Notify customer
        await self.notification_service.send_notification(
            str(order.get("customer_id")),
            NotificationType.IN_TRANSIT,
            {"order_id": order_id},
            {
                "courier_name": delivery_courier.get("name"),
                "eta": final_route.get("estimated_time")
            }
        )
        
        return {
            "status": "success",
            "message": "Final delivery initiated",
            "delivery_courier": delivery_courier,
            "final_route": final_route
        }
    
    async def _handle_delivery_completion(self, order_id: str, order_type: str, data: Dict) -> Dict:
        """Handle final delivery completion"""
        
        # Complete GPS tracking
        result = await self.gps_service.complete_delivery(order_id, data)
        
        # Update order status
        await self.db.orders.update_one(
            {"_id": order_id},
            {
                "$set": {
                    "status": "delivered",
                    "delivered_at": datetime.now(),
                    "proof_of_delivery": data.get("proof", {}),
                    "delivery_rating": data.get("rating")
                }
            }
        )
        
        # Send completion notification
        order = await self.db.orders.find_one({"_id": order_id})
        await self.notification_service.send_notification(
            str(order.get("customer_id")),
            NotificationType.DELIVERED,
            {"order_id": order_id},
            {"delivery_time": datetime.now().isoformat()}
        )
        
        # Stop route monitoring
        routing_service.stop_monitoring(order_id)
        
        return {
            "status": "success",
            "message": "Delivery completed successfully",
            "proof_of_delivery": data.get("proof", {})
        }