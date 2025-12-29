from crewai import Crew
from agents.inter_city.inter_city_coordinator_agent import inter_city_coordinator_agent
from agents.inter_city.inter_city_client_service_agent import inter_city_client_service_agent
from agents.inter_city.inter_city_pricing_agent import inter_city_pricing_agent
from agents.inter_city.long_distance_routing_agent import long_distance_routing_agent
from agents.inter_city.logistics_hub_agent import logistics_hub_agent
from agents.inter_city.transportation_coordinator_agent import transportation_coordinator_agent
from agents.inter_city.warehouse_coordinator_agent import warehouse_coordinator_agent
from agents.inter_city.customs_clearance_agent import customs_clearance_agent
from tasks.inter_city_tasks import *

class InterCityWorkflow:
    def __init__(self):
        self.coordinator = inter_city_coordinator_agent
        self.client_service = inter_city_client_service_agent
        self.pricing = inter_city_pricing_agent
        self.routing = long_distance_routing_agent
        self.hub_mgmt = logistics_hub_agent
        self.transportation = transportation_coordinator_agent
        self.warehouse = warehouse_coordinator_agent
        self.customs = customs_clearance_agent

    async def process_inter_city_order(self, order_data):
        """Process a new inter-city delivery order through the agent workflow"""

        try:
            # Step 1: Validate inter-city order
            validate_task = create_validate_inter_city_order_task(self.client_service, order_data)

            # Step 2: Calculate inter-city price
            price_task = create_calculate_inter_city_price_task(self.pricing, order_data)

            # Step 3: Plan inter-city route
            route_task = create_plan_inter_city_route_task(
                self.routing,
                order_data.get('origin_city'),
                order_data.get('destination_city'),
                order_data.get('waypoints')
            )

            # Step 4: Assign logistics hubs
            hub_task = create_assign_logistics_hubs_task(self.hub_mgmt, order_data)

            # Step 5: Assign transportation
            transport_task = create_assign_transportation_task(self.transportation, order_data)

            # Step 6: Handle customs if international
            tasks = [validate_task, price_task, route_task, hub_task, transport_task]
            if order_data.get('is_international', False):
                customs_task = create_handle_customs_clearance_task(self.customs, order_data)
                tasks.append(customs_task)

            # Step 7: Coordinate workflow
            coordinate_task = create_coordinate_inter_city_workflow_task(self.coordinator, order_data)
            tasks.append(coordinate_task)

            # Create crew
            crew = Crew(
                agents=[
                    self.client_service,
                    self.pricing,
                    self.routing,
                    self.hub_mgmt,
                    self.transportation,
                    self.customs if order_data.get('is_international', False) else None,
                    self.coordinator
                ],
                tasks=tasks,
                verbose=True
            )

            # Execute workflow
            result = crew.kickoff()
            return {"status": "success", "result": str(result)}

        except Exception as e:
            print(f"Inter-city workflow error: {e}")
            return {"status": "error", "message": str(e)}

    async def monitor_inter_city_delivery(self, order_id, route_data):
        """Monitor an active inter-city delivery"""

        try:
            monitor_route_task = create_monitor_inter_city_route_task(self.routing, order_id, route_data)
            monitor_transport_task = create_monitor_transportation_task(self.transportation, order_id, route_data)

            crew = Crew(
                agents=[self.routing, self.transportation],
                tasks=[monitor_route_task, monitor_transport_task],
                verbose=True
            )

            result = crew.kickoff()
            return {"status": "success", "result": str(result)}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def handle_inter_city_completion(self, order_id, completion_data):
        """Handle inter-city delivery completion"""

        try:
            verify_task = create_verify_customs_compliance_task(self.customs, order_id, completion_data)
            notify_task = create_send_inter_city_notification_task(self.client_service, "delivery_completed", order_id)

            crew = Crew(
                agents=[self.customs, self.client_service],
                tasks=[verify_task, notify_task],
                verbose=True
            )

            result = crew.kickoff()
            return {"status": "success", "result": str(result)}

        except Exception as e:
            return {"status": "error", "message": str(e)}
