import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from core.websocket import manager
from motor.motor_asyncio import AsyncIOMotorDatabase

class NotificationType(str, Enum):
    ORDER_CONFIRMED = "order_confirmed"
    COURIER_ASSIGNED = "courier_assigned"
    PICKUP_ARRIVED = "pickup_arrived"
    PACKAGE_PICKED_UP = "package_picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERY_ARRIVED = "delivery_arrived"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    REROUTED = "rerouted"
    WAREHOUSE_ARRIVAL = "warehouse_arrival"
    WAREHOUSE_DEPARTURE = "warehouse_departure"
    CUSTOMS_CLEARANCE = "customs_clearance"

class NotificationService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.notification_templates = self._load_templates()
        self.user_preferences = {}
        
    def _load_templates(self) -> Dict:
        """Load notification message templates"""
        return {
            NotificationType.ORDER_CONFIRMED: {
                "title": "Order Confirmed",
                "message": "Your delivery order #{order_id} has been confirmed. Estimated delivery: {eta}",
                "priority": "normal"
            },
            NotificationType.COURIER_ASSIGNED: {
                "title": "Courier Assigned",
                "message": "Courier {courier_name} has been assigned to your order #{order_id}. Phone: {courier_phone}",
                "priority": "normal"
            },
            NotificationType.PICKUP_ARRIVED: {
                "title": "Courier Arrived for Pickup",
                "message": "Your courier has arrived at the pickup location for order #{order_id}",
                "priority": "high"
            },
            NotificationType.PACKAGE_PICKED_UP: {
                "title": "Package Picked Up",
                "message": "Your package #{order_id} has been picked up and is now on its way!",
                "priority": "normal"
            },
            NotificationType.IN_TRANSIT: {
                "title": "Package in Transit",
                "message": "Your package #{order_id} is on its way. Current location: {location}. ETA: {eta}",
                "priority": "normal"
            },
            NotificationType.DELIVERY_ARRIVED: {
                "title": "Courier Arrived for Delivery",
                "message": "Your courier has arrived at the delivery location for order #{order_id}",
                "priority": "high"
            },
            NotificationType.DELIVERED: {
                "title": "Package Delivered!",
                "message": "Your package #{order_id} has been successfully delivered at {delivery_time}",
                "priority": "high"
            },
            NotificationType.DELAYED: {
                "title": "Delivery Delayed",
                "message": "Your delivery #{order_id} is delayed due to {reason}. New ETA: {new_eta}",
                "priority": "high"
            },
            NotificationType.REROUTED: {
                "title": "Route Updated",
                "message": "Your delivery #{order_id} route has been optimized for faster delivery. New ETA: {eta}",
                "priority": "normal"
            },
            NotificationType.WAREHOUSE_ARRIVAL: {
                "title": "Package at Warehouse",
                "message": "Your package #{order_id} has arrived at {warehouse_name} and is being processed",
                "priority": "normal"
            },
            NotificationType.WAREHOUSE_DEPARTURE: {
                "title": "Package Departed Warehouse",
                "message": "Your package #{order_id} has left {warehouse_name} and is continuing its journey",
                "priority": "normal"
            },
            NotificationType.CUSTOMS_CLEARANCE: {
                "title": "Customs Clearance",
                "message": "Your international package #{order_id} has cleared customs and is proceeding to delivery",
                "priority": "normal"
            }
        }
    
    async def send_notification(self, user_id: str, notification_type: NotificationType, 
                              order_data: Dict, additional_data: Dict = None) -> Dict:
        """Send notification to user through multiple channels"""
        
        if additional_data is None:
            additional_data = {}
            
        # Get user preferences
        preferences = await self._get_user_preferences(user_id)
        
        # Generate notification content
        notification = await self._generate_notification(
            notification_type, order_data, additional_data
        )
        
        # Store notification in database
        notification_record = {
            "user_id": user_id,
            "order_id": order_data.get("order_id"),
            "type": notification_type,
            "title": notification["title"],
            "message": notification["message"],
            "priority": notification["priority"],
            "created_at": datetime.now(),
            "read": False,
            "channels_sent": []
        }
        
        # Send through enabled channels
        sent_channels = []
        
        # Real-time WebSocket notification
        if preferences.get("websocket", True):
            await self._send_websocket_notification(user_id, notification, order_data)
            sent_channels.append("websocket")
        
        # Email notification
        if preferences.get("email", True) and notification["priority"] in ["high", "critical"]:
            await self._send_email_notification(user_id, notification, order_data)
            sent_channels.append("email")
        
        # SMS notification for critical updates
        if preferences.get("sms", False) and notification["priority"] == "critical":
            await self._send_sms_notification(user_id, notification, order_data)
            sent_channels.append("sms")
        
        # Push notification (mobile app)
        if preferences.get("push", True):
            await self._send_push_notification(user_id, notification, order_data)
            sent_channels.append("push")
        
        notification_record["channels_sent"] = sent_channels
        
        # Store in database
        result = await self.db.notifications.insert_one(notification_record)
        notification_record["_id"] = result.inserted_id
        
        return {
            "status": "success",
            "notification_id": str(result.inserted_id),
            "channels_sent": sent_channels,
            "message": "Notification sent successfully"
        }
    
    async def _generate_notification(self, notification_type: NotificationType, 
                                   order_data: Dict, additional_data: Dict) -> Dict:
        """Generate notification content from template"""
        
        template = self.notification_templates[notification_type]
        
        # Merge order data and additional data for template formatting
        format_data = {**order_data, **additional_data}
        
        # Format message
        try:
            formatted_message = template["message"].format(**format_data)
        except KeyError as e:
            # Fallback if template variable is missing
            formatted_message = template["message"]
            
        return {
            "title": template["title"],
            "message": formatted_message,
            "priority": template["priority"],
            "type": notification_type
        }
    
    async def _get_user_preferences(self, user_id: str) -> Dict:
        """Get user notification preferences"""
        
        if user_id in self.user_preferences:
            return self.user_preferences[user_id]
            
        # Load from database
        user_prefs = await self.db.user_preferences.find_one({"user_id": user_id})
        
        if user_prefs:
            preferences = user_prefs.get("notifications", {})
        else:
            # Default preferences
            preferences = {
                "websocket": True,
                "email": True,
                "sms": False,
                "push": True
            }
            
        self.user_preferences[user_id] = preferences
        return preferences
    
    async def _send_websocket_notification(self, user_id: str, notification: Dict, 
                                         order_data: Dict):
        """Send real-time WebSocket notification"""
        
        await manager.broadcast({
            "type": "notification",
            "user_id": user_id,
            "notification": notification,
            "order_data": order_data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _send_email_notification(self, user_id: str, notification: Dict, 
                                     order_data: Dict):
        """Send email notification"""
        
        # Get user email
        user = await self.db.users.find_one({"_id": user_id})
        if not user or not user.get("email"):
            return
            
        # In production, integrate with email service (SendGrid, AWS SES, etc.)
        email_data = {
            "to": user["email"],
            "subject": notification["title"],
            "body": notification["message"],
            "order_id": order_data.get("order_id"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Store email in queue for processing
        await self.db.email_queue.insert_one(email_data)
        
        print(f"Email queued for {user['email']}: {notification['title']}")
    
    async def _send_sms_notification(self, user_id: str, notification: Dict, 
                                   order_data: Dict):
        """Send SMS notification"""
        
        # Get user phone
        user = await self.db.users.find_one({"_id": user_id})
        if not user or not user.get("phone"):
            return
            
        # In production, integrate with SMS service (Twilio, AWS SNS, etc.)
        sms_data = {
            "to": user["phone"],
            "message": f"{notification['title']}: {notification['message']}",
            "order_id": order_data.get("order_id"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Store SMS in queue for processing
        await self.db.sms_queue.insert_one(sms_data)
        
        print(f"SMS queued for {user['phone']}: {notification['title']}")
    
    async def _send_push_notification(self, user_id: str, notification: Dict, 
                                    order_data: Dict):
        """Send push notification to mobile app"""
        
        # Get user device tokens
        devices = await self.db.user_devices.find({"user_id": user_id}).to_list(None)
        
        for device in devices:
            push_data = {
                "device_token": device["token"],
                "title": notification["title"],
                "body": notification["message"],
                "data": {
                    "order_id": order_data.get("order_id"),
                    "type": notification["type"],
                    "priority": notification["priority"]
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Store push notification in queue
            await self.db.push_queue.insert_one(push_data)
        
        print(f"Push notifications queued for {len(devices)} devices")
    
    async def send_bulk_notification(self, user_ids: List[str], 
                                   notification_type: NotificationType,
                                   order_data: Dict, additional_data: Dict = None):
        """Send notification to multiple users"""
        
        results = []
        
        for user_id in user_ids:
            result = await self.send_notification(
                user_id, notification_type, order_data, additional_data
            )
            results.append({"user_id": user_id, "result": result})
            
        return results
    
    async def mark_notification_read(self, notification_id: str, user_id: str) -> Dict:
        """Mark notification as read"""
        
        result = await self.db.notifications.update_one(
            {"_id": notification_id, "user_id": user_id},
            {"$set": {"read": True, "read_at": datetime.now()}}
        )
        
        if result.modified_count > 0:
            return {"status": "success", "message": "Notification marked as read"}
        else:
            return {"status": "error", "message": "Notification not found"}
    
    async def get_user_notifications(self, user_id: str, limit: int = 50, 
                                   unread_only: bool = False) -> List[Dict]:
        """Get user notifications"""
        
        query = {"user_id": user_id}
        if unread_only:
            query["read"] = False
            
        notifications = await self.db.notifications.find(query)\
            .sort("created_at", -1)\
            .limit(limit)\
            .to_list(None)
            
        return notifications
    
    async def update_user_preferences(self, user_id: str, preferences: Dict) -> Dict:
        """Update user notification preferences"""
        
        await self.db.user_preferences.update_one(
            {"user_id": user_id},
            {"$set": {"notifications": preferences, "updated_at": datetime.now()}},
            upsert=True
        )
        
        # Update cache
        self.user_preferences[user_id] = preferences
        
        return {"status": "success", "message": "Preferences updated"}
    
    async def send_delivery_status_update(self, order_id: str, status: str, 
                                        location_data: Dict = None, eta_data: Dict = None):
        """Send delivery status update notification"""
        
        # Get order details
        order = await self.db.orders.find_one({"_id": order_id})
        if not order:
            return {"error": "Order not found"}
            
        user_id = str(order["customer_id"])
        
        # Determine notification type based on status
        notification_type_map = {
            "confirmed": NotificationType.ORDER_CONFIRMED,
            "courier_assigned": NotificationType.COURIER_ASSIGNED,
            "pickup_arrived": NotificationType.PICKUP_ARRIVED,
            "picked_up": NotificationType.PACKAGE_PICKED_UP,
            "in_transit": NotificationType.IN_TRANSIT,
            "delivery_arrived": NotificationType.DELIVERY_ARRIVED,
            "delivered": NotificationType.DELIVERED,
            "delayed": NotificationType.DELAYED
        }
        
        notification_type = notification_type_map.get(status, NotificationType.IN_TRANSIT)
        
        # Prepare additional data
        additional_data = {}
        if location_data:
            additional_data["location"] = location_data.get("address", "Unknown location")
        if eta_data:
            additional_data["eta"] = eta_data.get("eta", "Unknown")
            
        # Send notification
        return await self.send_notification(
            user_id, notification_type, 
            {"order_id": order_id}, additional_data
        )