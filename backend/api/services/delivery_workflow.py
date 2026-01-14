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

# Import agent creators
if CREWAI_AVAILABLE:
    from api.agents.intra_city import (
        create_coordinator_agent,
        create_courier_management_agent,
        create_intra_pricing_agent,
        create_smart_routing_agent,
        create_client_service_agent
    )
    from api.agents.inter_city import (
        create_inter_city_coordinator_agent,
        create_warehouse_coordinator_agent,
        create_transportation_coordinator_agent,
        create_inter_city_pricing_agent,
        create_long_distance_routing_agent
    )

# Create agent instances
if CREWAI_AVAILABLE:
    try:
        llm_instance = LLM(model="ollama/llama3.2", base_url="http://localhost:11434")
        
        # Intra-city agents
        coordinator_agent = create_coordinator_agent(llm_instance)
        courier_management_agent = create_courier_management_agent(llm_instance)
        intra_pricing_agent = create_intra_pricing_agent(llm_instance)
        smart_routing_agent = create_smart_routing_agent(llm_instance)
        client_service_agent = create_client_service_agent(llm_instance)
        
        # Inter-city agents
        inter_city_coordinator_agent = create_inter_city_coordinator_agent(llm_instance)
        warehouse_coordinator_agent = create_warehouse_coordinator_agent(llm_instance)
        transportation_coordinator_agent = create_transportation_coordinator_agent(llm_instance)
        inter_city_pricing_agent = create_inter_city_pricing_agent(llm_instance)
        long_distance_routing_agent = create_long_distance_routing_agent(llm_instance)
        
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
        """Intra-city delivery workflow - SEQUENTIAL PIPELINE"""
        print("[WORKFLOW] Starting INTRA-CITY workflow...")
        
        if not AGENTS_LOADED or not self.llm:
            print("[WORKFLOW] Using FALLBACK mode")
            return self._fallback_intra_city(order, drivers)
        
        print("[WORKFLOW] Using AI MODE - Sequential pipeline with 5 agents\n")
        
        try:
            # Task 1: Client Service validates order
            task1 = Task(
                description=f"Validate intra-city order from {order['pickup_city']} (weight: {order['weight']}kg). Confirm order is valid.",
                agent=client_service_agent,
                expected_output="Order validation status"
            )
            
            # Task 2: Pricing calculates cost (depends on task1)
            task2 = Task(
                description=f"Calculate price for {order['weight']}kg, {order['service_type']} service in {order['pickup_city']}.",
                agent=intra_pricing_agent,
                expected_output="Price calculation",
                context=[task1]  # Depends on task1
            )
            
            # Task 3: Courier Management assigns driver (depends on task2)
            task3 = Task(
                description=f"Assign best driver from {len(drivers)} available drivers. Return driver ID.",
                agent=courier_management_agent,
                expected_output="Driver assignment",
                context=[task2]  # Depends on task2
            )
            
            # Task 4: Smart Routing plans route (depends on task3)
            task4 = Task(
                description=f"Plan optimal route in {order['pickup_city']} for assigned driver.",
                agent=smart_routing_agent,
                expected_output="Route plan",
                context=[task3]  # Depends on task3
            )
            
            # Task 5: Coordinator finalizes (depends on task4)
            task5 = Task(
                description="Finalize intra-city delivery workflow and confirm all steps completed.",
                agent=coordinator_agent,
                expected_output="Workflow completion confirmation",
                context=[task4]  # Depends on task4
            )
            
            crew = Crew(
                agents=[client_service_agent, intra_pricing_agent, courier_management_agent, 
                       smart_routing_agent, coordinator_agent],
                tasks=[task1, task2, task3, task4, task5],
                verbose=True,
                process="sequential"  # Sequential execution
            )
            
            result = crew.kickoff()
            
            return {
                "workflow": "intra_city",
                "ai_result": str(result),
                "best_driver": drivers[0] if drivers else None,
                "agents_used": ["client_service", "pricing", "courier_management", "routing", "coordinator"]
            }
        except Exception as e:
            print(f"[WORKFLOW] Error: {e}")
            return self._fallback_intra_city(order, drivers)
    
    async def _inter_city_workflow(self, order: dict, drivers: list):
        """Inter-city delivery workflow - SEQUENTIAL PIPELINE"""
        if not AGENTS_LOADED or not self.llm:
            return self._fallback_inter_city(order, drivers)
        
        print("[WORKFLOW] Using AI MODE - Sequential pipeline with 5 agents\n")
        
        try:
            # Task 1: Coordinator plans workflow
            task1 = Task(
                description=f"Coordinate inter-city delivery from {order['pickup_city']} to {order['delivery_city']}. Plan workflow stages.",
                agent=inter_city_coordinator_agent,
                expected_output="Workflow plan"
            )
            
            # Task 2: Warehouse Coordinator plans warehouse operations (depends on task1)
            task2 = Task(
                description=f"Plan warehouse operations for inter-city delivery. Coordinate origin and destination warehouses.",
                agent=warehouse_coordinator_agent,
                expected_output="Warehouse coordination plan",
                context=[task1]  # Depends on task1
            )
            
            # Task 3: Transportation Coordinator schedules transport (depends on task2)
            task3 = Task(
                description=f"Schedule inter-city transportation between {order['pickup_city']} and {order['delivery_city']}.",
                agent=transportation_coordinator_agent,
                expected_output="Transport schedule",
                context=[task2]  # Depends on task2
            )
            
            # Task 4: Pricing calculates cost (depends on task3)
            task4 = Task(
                description=f"Calculate inter-city price for {order['weight']}kg delivery.",
                agent=inter_city_pricing_agent,
                expected_output="Price calculation",
                context=[task3]  # Depends on task3
            )
            
            # Task 5: Routing plans long-distance route (depends on task4)
            task5 = Task(
                description=f"Plan long-distance route and assign driver from {len(drivers)} available drivers.",
                agent=long_distance_routing_agent,
                expected_output="Route plan and driver assignment",
                context=[task4]  # Depends on task4
            )
            
            crew = Crew(
                agents=[inter_city_coordinator_agent, warehouse_coordinator_agent, 
                       transportation_coordinator_agent, inter_city_pricing_agent, 
                       long_distance_routing_agent],
                tasks=[task1, task2, task3, task4, task5],
                verbose=True,
                process="sequential"  # Sequential execution
            )
            
            result = crew.kickoff()
            
            return {
                "workflow": "inter_city",
                "ai_result": str(result),
                "best_driver": drivers[0] if drivers else None,
                "agents_used": ["inter_city_coordinator", "warehouse_coordinator", 
                               "transportation_coordinator", "inter_city_pricing", "long_distance_routing"]
            }
        except Exception as e:
            print(f"[WORKFLOW] Error: {e}")
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
