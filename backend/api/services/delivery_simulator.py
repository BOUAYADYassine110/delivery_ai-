"""
Delivery Simulator - Simulates delivery progress
"""
from datetime import datetime
from typing import Dict

class DeliverySimulator:
    def __init__(self):
        self.active_simulations = {}
    
    def start_simulation(self, order_id: str, order: Dict, orders_db: list):
        """Start delivery simulation (placeholder)"""
        # Simulation is handled by frontend
        # This is just a placeholder to prevent errors
        pass
    
    def stop_simulation(self, order_id: str):
        """Stop delivery simulation"""
        if order_id in self.active_simulations:
            del self.active_simulations[order_id]

# Global instance
simulator = DeliverySimulator()
