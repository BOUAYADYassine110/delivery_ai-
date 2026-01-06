"""
Unified Agent Workflow System
Routes orders to appropriate agent teams (intra-city or inter-city)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from crewai import Agent, Task, Crew, LLM
    CREWAI_AVAILABLE = True
except:
    CREWAI_AVAILABLE = False

# Create agent instances directly
if CREWAI_AVAILABLE:
    try:
        llm_instance = LLM(model="ollama/llama3.2", base_url="http://localhost:11434")
        
        # Intra-city agents
        coordinator_agent = Agent(
            role="Intra-City Delivery Coordinator",
            goal="Orchestrate intra-city delivery workflow",
            backstory="Expert logistics coordinator for urban deliveries",
            llm=llm_instance,
            verbose=True
        )
        
        courier_management_agent = Agent(
            role="Courier Management Specialist",
            goal="Assign and manage drivers for deliveries",
            backstory="Fleet manager optimizing driver assignments",
            llm=llm_instance,
            verbose=True
        )
        
        intra_pricing_agent = Agent(
            role="Intra-City Pricing Agent",
            goal="Calculate accurate delivery prices",
            backstory="Pricing expert for local deliveries",
            llm=llm_instance,
            verbose=True
        )
        
        smart_routing_agent = Agent(
            role="Smart Routing Agent",
            goal="Plan optimal routes within city",
            backstory="Navigation expert for urban routing",
            llm=llm_instance,
            verbose=True
        )
        
        client_service_agent = Agent(
            role="Client Service Agent",
            goal="Process and validate customer orders",
            backstory="Customer service specialist",
            llm=llm_instance,
            verbose=True
        )
        
        # Inter-city agents
        inter_city_coordinator_agent = Agent(
            role="Inter-City Coordinator",
            goal="Coordinate cross-city deliveries",
            backstory="Expert in long-distance logistics",
            llm=llm_instance,
            verbose=True
        )
        
        warehouse_coordinator_agent = Agent(
            role="Warehouse Coordinator",
            goal="Manage warehouse operations",
            backstory="Warehouse logistics specialist",
            llm=llm_instance,
            verbose=True
        )
        
        transportation_coordinator_agent = Agent(
            role="Transportation Coordinator",
            goal="Schedule inter-city transport",
            backstory="Transport scheduling expert",
            llm=llm_instance,
            verbose=True
        )
        
        inter_city_pricing_agent = Agent(
            role="Inter-City Pricing Agent",
            goal="Calculate inter-city delivery prices",
            backstory="Long-distance pricing specialist",
            llm=llm_instance,
            verbose=True
        )
        
        long_distance_routing_agent = Agent(
            role="Long Distance Routing Agent",
            goal="Plan inter-city routes",
            backstory="Expert in long-distance route planning",
            llm=llm_instance,
            verbose=True
        )
        
        AGENTS_LOADED = True
        print("[SUCCESS] All agents created successfully")
    except Exception as e:
        print("WARNING: Could not create agents: {}".format(str(e)))
        AGENTS_LOADED = False
else:
    AGENTS_LOADED = False

class DeliveryWorkflow:
    def __init__(self):
        self.llm = None
        if CREWAI_AVAILABLE:
            try:
                self.llm = LLM(model="ollama/llama3.2", base_url="http://localhost:11434")
            except:
                pass
    
    async def process_order(self, order: dict, drivers: list):
        """Main workflow - routes to appropriate agent team"""
        is_inter_city = order['pickup_city'].lower() != order['delivery_city'].lower()
        
        print("\n" + "="*60)
        print(f"PROCESSING ORDER: {order['pickup_city']} -> {order['delivery_city']}")
        print(f"Type: {'INTER-CITY' if is_inter_city else 'INTRA-CITY'}")
        print(f"Agents Loaded: {AGENTS_LOADED}")
        print(f"LLM Available: {self.llm is not None}")
        print("="*60 + "\n")
        
        if is_inter_city:
            return await self._inter_city_workflow(order, drivers)
        else:
            return await self._intra_city_workflow(order, drivers)
    
    async def _intra_city_workflow(self, order: dict, drivers: list):
        """Intra-city delivery workflow"""
        print("[WORKFLOW] Starting INTRA-CITY workflow...")
        
        if not AGENTS_LOADED or not self.llm:
            print("[WORKFLOW] Using FALLBACK mode (agents not loaded or LLM unavailable)")
            return self._fallback_intra_city(order, drivers)
        
        print("[WORKFLOW] Using AI MODE with CrewAI agents")
        print("[WORKFLOW] Agents will now collaborate...\n")
        
        try:
            # 1. Client Service Agent - Process order
            client_task = Task(
                description=f"Process intra-city order from {order['pickup_city']}",
                agent=client_service_agent,
                expected_output="Order validation and customer confirmation"
            )
            
            # 2. Pricing Agent - Calculate price
            pricing_task = Task(
                description=f"Calculate price for {order['weight']}kg, {order['service_type']} service",
                agent=intra_pricing_agent,
                expected_output="Price calculation"
            )
            
            # 3. Courier Management - Assign driver
            courier_task = Task(
                description=f"Assign best driver from {len(drivers)} available drivers",
                agent=courier_management_agent,
                expected_output="Driver assignment"
            )
            
            # 4. Smart Routing - Plan route
            routing_task = Task(
                description=f"Plan optimal route in {order['pickup_city']}",
                agent=smart_routing_agent,
                expected_output="Route plan"
            )
            
            # 5. Coordinator - Orchestrate
            coord_task = Task(
                description="Coordinate intra-city delivery workflow",
                agent=coordinator_agent,
                expected_output="Workflow coordination"
            )
            
            crew = Crew(
                agents=[client_service_agent, intra_pricing_agent, courier_management_agent, 
                       smart_routing_agent, coordinator_agent],
                tasks=[client_task, pricing_task, courier_task, routing_task, coord_task],
                verbose=True  # Enable verbose to see agent thinking
            )
            
            result = crew.kickoff()
            
            return {
                "workflow": "intra_city",
                "ai_result": str(result),
                "best_driver": drivers[0] if drivers else None,
                "agents_used": ["client_service", "pricing", "courier_management", "routing", "coordinator"]
            }
        except:
            return self._fallback_intra_city(order, drivers)
    
    async def _inter_city_workflow(self, order: dict, drivers: list):
        """Inter-city delivery workflow"""
        if not AGENTS_LOADED or not self.llm:
            return self._fallback_inter_city(order, drivers)
        
        try:
            # 1. Inter-City Coordinator - Orchestrate
            coord_task = Task(
                description=f"Coordinate inter-city delivery from {order['pickup_city']} to {order['delivery_city']}",
                agent=inter_city_coordinator_agent,
                expected_output="Workflow coordination"
            )
            
            # 2. Warehouse Coordinator - Plan warehouse handling
            warehouse_task = Task(
                description=f"Coordinate warehouse operations for inter-city delivery",
                agent=warehouse_coordinator_agent,
                expected_output="Warehouse plan"
            )
            
            # 3. Transportation Coordinator - Plan transport
            transport_task = Task(
                description=f"Coordinate transportation between cities",
                agent=transportation_coordinator_agent,
                expected_output="Transport schedule"
            )
            
            # 4. Inter-City Pricing - Calculate price
            pricing_task = Task(
                description=f"Calculate inter-city price for {order['weight']}kg",
                agent=inter_city_pricing_agent,
                expected_output="Price calculation"
            )
            
            # 5. Long Distance Routing - Plan route
            routing_task = Task(
                description=f"Plan long-distance route",
                agent=long_distance_routing_agent,
                expected_output="Route plan"
            )
            
            crew = Crew(
                agents=[inter_city_coordinator_agent, warehouse_coordinator_agent, 
                       transportation_coordinator_agent, inter_city_pricing_agent, 
                       long_distance_routing_agent],
                tasks=[coord_task, warehouse_task, transport_task, pricing_task, routing_task],
                verbose=True  # Enable verbose to see agent thinking
            )
            
            result = crew.kickoff()
            
            return {
                "workflow": "inter_city",
                "ai_result": str(result),
                "best_driver": drivers[0] if drivers else None,
                "agents_used": ["inter_city_coordinator", "warehouse_coordinator", 
                               "transportation_coordinator", "inter_city_pricing", "long_distance_routing"]
            }
        except:
            return self._fallback_inter_city(order, drivers)
    
    def _fallback_intra_city(self, order, drivers):
        """Fallback for intra-city when AI unavailable"""
        return {
            "workflow": "intra_city",
            "best_driver": sorted(drivers, key=lambda d: d.get("rating", 0), reverse=True)[0] if drivers else None,
            "agents_used": ["fallback"],
            "mode": "rule_based"
        }
    
    def _fallback_inter_city(self, order, drivers):
        """Fallback for inter-city when AI unavailable"""
        # Prefer van/truck for inter-city
        suitable_drivers = [d for d in drivers if d.get("vehicle_type") in ["van", "car"]]
        if not suitable_drivers:
            suitable_drivers = drivers
        
        return {
            "workflow": "inter_city",
            "best_driver": sorted(suitable_drivers, key=lambda d: d.get("rating", 0), reverse=True)[0] if suitable_drivers else None,
            "agents_used": ["fallback"],
            "mode": "rule_based"
        }

# Global workflow instance
workflow = DeliveryWorkflow()

async def process_delivery_order(order: dict, drivers: list):
    """Main entry point for order processing"""
    return await workflow.process_order(order, drivers)

def get_workflow_status():
    """Get status of workflow system"""
    return {
        "crewai_available": CREWAI_AVAILABLE,
        "agents_loaded": AGENTS_LOADED,
        "llm_available": workflow.llm is not None,
        "workflows": {
            "intra_city": {
                "agents": ["client_service", "pricing", "courier_management", "routing", "coordinator", "tracking_monitoring"],
                "description": "Same-city deliveries with local driver assignment"
            },
            "inter_city": {
                "agents": ["inter_city_coordinator", "warehouse_coordinator", "transportation_coordinator", 
                          "inter_city_pricing", "long_distance_routing", "logistics_hub"],
                "description": "Cross-city deliveries with warehouse coordination"
            }
        }
    }
