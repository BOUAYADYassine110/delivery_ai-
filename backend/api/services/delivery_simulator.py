import asyncio
from datetime import datetime
from typing import Dict
import random

class DeliverySimulator:
    def __init__(self):
        self.active_simulations = {}
    
    async def simulate_delivery(self, order_id: str, order_data: dict, orders_db: list):
        """Simulate complete delivery lifecycle"""
        try:
            print(f"\n🎬 SIMULATION STARTED for order {order_id}")
            
            # Stage 1: Assigned -> Picked Up (30 seconds)
            await asyncio.sleep(30)
            await self._update_status(order_id, "picked_up", orders_db)
            print(f"📦 Order {order_id}: PICKED UP")
            
            # Stage 2: Picked Up -> In Transit (20 seconds)
            await asyncio.sleep(20)
            await self._update_status(order_id, "in_transit", orders_db)
            print(f"🚚 Order {order_id}: IN TRANSIT")
            
            # Stage 3: In Transit -> Out for Delivery (40 seconds)
            await asyncio.sleep(40)
            await self._update_status(order_id, "out_for_delivery", orders_db)
            print(f"🏃 Order {order_id}: OUT FOR DELIVERY")
            
            # Stage 4: Out for Delivery -> Delivered (30 seconds)
            await asyncio.sleep(30)
            await self._update_status(order_id, "delivered", orders_db)
            print(f"✅ Order {order_id}: DELIVERED - Notification sent!")
            
        except Exception as e:
            print(f"❌ Simulation error for {order_id}: {e}")
        finally:
            if order_id in self.active_simulations:
                del self.active_simulations[order_id]
    
    async def _update_status(self, order_id: str, status: str, orders_db: list):
        """Update order status in in-memory database"""
        try:
            order = next((o for o in orders_db if o["id"] == order_id), None)
            if order:
                order["status"] = status
                order["updated_at"] = datetime.now().isoformat()
                if "status_history" not in order:
                    order["status_history"] = []
                order["status_history"].append({
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                })
                return True
            return False
        except Exception as e:
            print(f"Error updating status: {e}")
            return False
    
    def start_simulation(self, order_id: str, order_data: dict, orders_db: list):
        """Start simulation in background"""
        if order_id not in self.active_simulations:
            task = asyncio.create_task(self.simulate_delivery(order_id, order_data, orders_db))
            self.active_simulations[order_id] = task
            print(f"🎬 Simulation queued for order {order_id}")
            return True
        return False

# Global simulator instance
simulator = DeliverySimulator()
