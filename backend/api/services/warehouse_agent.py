"""
Warehouse Management AI Agent
Tracks warehouse operations and communicates with other agents
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from crewai import Agent, Task, Crew
    from crewai.llm import LLM
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

class WarehouseManagementAgent:
    def __init__(self):
        self.llm = None
        if CREWAI_AVAILABLE:
            try:
                self.llm = LLM(model="ollama/llama3.2", base_url="http://localhost:11434")
            except:
                pass
        
        self.agent = self._create_agent()
    
    def _create_agent(self):
        if not CREWAI_AVAILABLE or not self.llm:
            return None
        
        return Agent(
            role="Warehouse Operations Manager",
            goal="Optimize warehouse operations, track inventory, manage package flow, and coordinate with logistics agents",
            backstory="""Expert warehouse manager with AI-powered optimization capabilities.
            Specializes in inventory management, package sorting, capacity planning, and inter-warehouse coordination.
            Works closely with transportation, routing, and assignment agents to ensure smooth operations.""",
            llm=self.llm,
            verbose=False
        )
    
    async def check_capacity(self, warehouse_id: str, warehouses: list, incoming_packages: int = 1):
        """Check if warehouse has capacity for incoming packages"""
        if not self.agent:
            return self._fallback_capacity_check(warehouse_id, warehouses, incoming_packages)
        
        try:
            warehouse = next((w for w in warehouses if w["id"] == warehouse_id), None)
            if not warehouse:
                return {"available": False, "reason": "Warehouse not found"}
            
            task = Task(
                description=f"""Analyze warehouse capacity:
                Warehouse: {warehouse['name']} in {warehouse['city']}
                Current packages: {warehouse['current_packages']}
                Total capacity: {warehouse['capacity']}
                Incoming packages: {incoming_packages}
                
                Determine if warehouse can accept packages and recommend actions.""",
                agent=self.agent,
                expected_output="Capacity analysis with recommendations"
            )
            
            crew = Crew(agents=[self.agent], tasks=[task], verbose=False)
            result = crew.kickoff()
            
            available = warehouse['current_packages'] + incoming_packages <= warehouse['capacity']
            return {
                "available": available,
                "current_load": warehouse['current_packages'],
                "capacity": warehouse['capacity'],
                "utilization": round((warehouse['current_packages'] / warehouse['capacity']) * 100, 1),
                "ai_analysis": str(result)
            }
        except:
            return self._fallback_capacity_check(warehouse_id, warehouses, incoming_packages)
    
    async def optimize_package_routing(self, order: dict, warehouses: list):
        """Determine optimal warehouse routing for inter-city orders"""
        if not self.agent:
            return self._fallback_routing(order, warehouses)
        
        try:
            task = Task(
                description=f"""Optimize warehouse routing for order:
                From: {order['pickup_city']} to {order['delivery_city']}
                Weight: {order['weight']}kg
                Service: {order.get('service_type', 'standard')}
                
                Available warehouses: {[w['city'] for w in warehouses]}
                
                Recommend optimal warehouse path considering capacity, location, and efficiency.""",
                agent=self.agent,
                expected_output="Warehouse routing recommendation"
            )
            
            crew = Crew(agents=[self.agent], tasks=[task], verbose=False)
            result = crew.kickoff()
            
            return {
                "origin_warehouse": order['pickup_city'],
                "destination_warehouse": order['delivery_city'],
                "ai_recommendation": str(result)
            }
        except:
            return self._fallback_routing(order, warehouses)
    
    async def coordinate_with_transport(self, warehouse_id: str, packages: list, transport_schedule: dict):
        """Coordinate package dispatch with transportation agent"""
        if not self.agent:
            return self._fallback_coordination(packages)
        
        try:
            task = Task(
                description=f"""Coordinate warehouse dispatch:
                Warehouse: {warehouse_id}
                Packages to dispatch: {len(packages)}
                Next transport: {transport_schedule.get('next_departure', 'Unknown')}
                
                Prioritize packages, prepare loading sequence, and coordinate with transport.""",
                agent=self.agent,
                expected_output="Dispatch coordination plan"
            )
            
            crew = Crew(agents=[self.agent], tasks=[task], verbose=False)
            result = crew.kickoff()
            
            # Sort by priority (express first)
            sorted_packages = sorted(packages, key=lambda p: 0 if p.get('service_type') == 'express' else 1)
            
            return {
                "dispatch_ready": True,
                "package_count": len(packages),
                "loading_sequence": [p['id'] for p in sorted_packages],
                "ai_coordination": str(result)
            }
        except:
            return self._fallback_coordination(packages)
    
    async def predict_capacity_needs(self, warehouse_id: str, warehouses: list, historical_data: dict):
        """Predict future capacity needs based on trends"""
        if not self.agent:
            return self._fallback_prediction(warehouse_id, warehouses)
        
        try:
            warehouse = next((w for w in warehouses if w["id"] == warehouse_id), None)
            if not warehouse:
                return {"prediction": "unavailable"}
            
            task = Task(
                description=f"""Predict warehouse capacity needs:
                Warehouse: {warehouse['name']}
                Current utilization: {(warehouse['current_packages']/warehouse['capacity'])*100:.1f}%
                Historical trends: {historical_data}
                
                Predict capacity needs for next 24 hours and recommend actions.""",
                agent=self.agent,
                expected_output="Capacity prediction and recommendations"
            )
            
            crew = Crew(agents=[self.agent], tasks=[task], verbose=False)
            result = crew.kickoff()
            
            return {
                "warehouse_id": warehouse_id,
                "current_utilization": round((warehouse['current_packages']/warehouse['capacity'])*100, 1),
                "prediction": str(result),
                "alert_level": "high" if warehouse['current_packages'] > warehouse['capacity'] * 0.8 else "normal"
            }
        except:
            return self._fallback_prediction(warehouse_id, warehouses)
    
    async def communicate_with_assignment_agent(self, order: dict, warehouses: list):
        """Communicate warehouse availability to assignment agent"""
        if not self.agent:
            return self._fallback_communication(order, warehouses)
        
        try:
            origin_wh = next((w for w in warehouses if w['city'] == order['pickup_city']), None)
            dest_wh = next((w for w in warehouses if w['city'] == order['delivery_city']), None)
            
            task = Task(
                description=f"""Communicate warehouse status to assignment agent:
                Order: {order['id']} from {order['pickup_city']} to {order['delivery_city']}
                Origin warehouse: {origin_wh['name'] if origin_wh else 'None'} - {origin_wh['current_packages']}/{origin_wh['capacity'] if origin_wh else 'N/A'}
                Destination warehouse: {dest_wh['name'] if dest_wh else 'None'} - {dest_wh['current_packages']}/{dest_wh['capacity'] if dest_wh else 'N/A'}
                
                Provide warehouse readiness status for assignment agent.""",
                agent=self.agent,
                expected_output="Warehouse status communication"
            )
            
            crew = Crew(agents=[self.agent], tasks=[task], verbose=False)
            result = crew.kickoff()
            
            return {
                "origin_ready": origin_wh['current_packages'] < origin_wh['capacity'] if origin_wh else False,
                "destination_ready": dest_wh['current_packages'] < dest_wh['capacity'] if dest_wh else False,
                "communication": str(result)
            }
        except:
            return self._fallback_communication(order, warehouses)
    
    # Fallback methods
    def _fallback_capacity_check(self, warehouse_id, warehouses, incoming_packages):
        warehouse = next((w for w in warehouses if w["id"] == warehouse_id), None)
        if not warehouse:
            return {"available": False}
        
        available = warehouse['current_packages'] + incoming_packages <= warehouse['capacity']
        return {
            "available": available,
            "current_load": warehouse['current_packages'],
            "capacity": warehouse['capacity'],
            "utilization": round((warehouse['current_packages'] / warehouse['capacity']) * 100, 1)
        }
    
    def _fallback_routing(self, order, warehouses):
        return {
            "origin_warehouse": order['pickup_city'],
            "destination_warehouse": order['delivery_city']
        }
    
    def _fallback_coordination(self, packages):
        sorted_packages = sorted(packages, key=lambda p: 0 if p.get('service_type') == 'express' else 1)
        return {
            "dispatch_ready": True,
            "package_count": len(packages),
            "loading_sequence": [p['id'] for p in sorted_packages]
        }
    
    def _fallback_prediction(self, warehouse_id, warehouses):
        warehouse = next((w for w in warehouses if w["id"] == warehouse_id), None)
        if not warehouse:
            return {"prediction": "unavailable"}
        
        utilization = round((warehouse['current_packages']/warehouse['capacity'])*100, 1)
        return {
            "warehouse_id": warehouse_id,
            "current_utilization": utilization,
            "alert_level": "high" if utilization > 80 else "normal"
        }
    
    def _fallback_communication(self, order, warehouses):
        origin_wh = next((w for w in warehouses if w['city'] == order['pickup_city']), None)
        dest_wh = next((w for w in warehouses if w['city'] == order['delivery_city']), None)
        
        return {
            "origin_ready": origin_wh['current_packages'] < origin_wh['capacity'] if origin_wh else False,
            "destination_ready": dest_wh['current_packages'] < dest_wh['capacity'] if dest_wh else False
        }

# Global instance
warehouse_agent = WarehouseManagementAgent()

# Export functions
async def check_warehouse_capacity(warehouse_id: str, warehouses: list, incoming_packages: int = 1):
    return await warehouse_agent.check_capacity(warehouse_id, warehouses, incoming_packages)

async def optimize_warehouse_routing(order: dict, warehouses: list):
    return await warehouse_agent.optimize_package_routing(order, warehouses)

async def coordinate_warehouse_transport(warehouse_id: str, packages: list, transport_schedule: dict):
    return await warehouse_agent.coordinate_with_transport(warehouse_id, packages, transport_schedule)

async def predict_warehouse_capacity(warehouse_id: str, warehouses: list, historical_data: dict = {}):
    return await warehouse_agent.predict_capacity_needs(warehouse_id, warehouses, historical_data)

async def communicate_warehouse_status(order: dict, warehouses: list):
    return await warehouse_agent.communicate_with_assignment_agent(order, warehouses)

def get_warehouse_agent_status():
    return {
        "agent_available": warehouse_agent.agent is not None,
        "llm_available": warehouse_agent.llm is not None,
        "status": "active" if warehouse_agent.agent else "fallback"
    }
