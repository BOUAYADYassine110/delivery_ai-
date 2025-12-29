from crewai import Crew
from agents.intra_city.coordinator_agent import coordinator_agent
from agents.intra_city.client_service_agent import client_service_agent
from agents.intra_city.pricing_agent import pricing_agent
from agents.intra_city.smart_routing_agent import smart_routing_agent
from agents.intra_city.courier_management_agent import courier_management_agent
from agents.intra_city.tracking_monitoring_agent import tracking_monitoring_agent
from tasks.intra_city_tasks import *

class IntraCityWorkflow:
    def __init__(self):
        self.coordinator = coordinator_agent
        self.client_service = client_service_agent
        self.pricing = pricing_agent
        self.routing = smart_routing_agent
        self.courier_mgmt = courier_management_agent
        self.tracking = tracking_monitoring_agent
    
    async def process_new_order(self, order_data):
        """Process a new intra-city delivery order through the agent workflow"""
        
        try:
            # Step 1: Validate order
            validate_task = create_validate_order_task(self.client_service, order_data)
            
            # Step 2: Calculate price
            price_task = create_calculate_price_task(self.pricing, order_data)
            
            # Step 3: Calculate optimal route
            route_task = create_calculate_route_task(
                self.routing,
                order_data.get('sender_address'),
                order_data.get('receiver_address')
            )
            
            # Step 4: Assign courier
            assign_task = create_assign_courier_task(self.courier_mgmt, order_data)
            
            # Step 5: Coordinate workflow
            coordinate_task = create_coordinate_workflow_task(self.coordinator, order_data)
            
            # Create crew
            crew = Crew(
                agents=[
                    self.client_service,
                    self.pricing,
                    self.routing,
                    self.courier_mgmt,
                    self.coordinator
                ],
                tasks=[
                    validate_task,
                    price_task,
                    route_task,
                    assign_task,
                    coordinate_task
                ],
                verbose=True
            )
            
            # Execute workflow
            result = crew.kickoff()
            return {"status": "success", "result": str(result)}
            
        except Exception as e:
            print(f"Workflow error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def monitor_active_delivery(self, order_id, route_data):
        """Monitor an active delivery for traffic/weather changes"""
        
        try:
            monitor_task = create_monitor_route_task(self.routing, order_id, route_data)
            
            crew = Crew(
                agents=[self.routing],
                tasks=[monitor_task],
                verbose=True
            )
            
            result = crew.kickoff()
            return {"status": "success", "result": str(result)}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def handle_delivery_completion(self, order_id, proof_data):
        """Handle delivery completion and verification"""
        
        try:
            verify_task = create_verify_delivery_task(self.courier_mgmt, order_id, proof_data)
            notify_task = create_send_notification_task(self.client_service, "delivery_completed", order_id)
            
            crew = Crew(
                agents=[self.courier_mgmt, self.client_service],
                tasks=[verify_task, notify_task],
                verbose=True
            )
            
            result = crew.kickoff()
            return {"status": "success", "result": str(result)}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
