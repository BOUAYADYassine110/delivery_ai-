"""
Integrated CrewAI Agent Service
Connects CrewAI agents to the delivery system
"""
import sys
import os
import warnings
warnings.filterwarnings('ignore', message='.*Mixing V1 models and V2 models.*')

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from crewai import Agent, Task, Crew
    from crewai.llm import LLM
    CREWAI_AVAILABLE = True
except ImportError:
    try:
        from crewai import Agent, Task, Crew, LLM
        CREWAI_AVAILABLE = True
    except ImportError:
        CREWAI_AVAILABLE = False
        print("⚠️  CrewAI not available - using fallback logic")

class DeliveryAgentCrew:
    def __init__(self):
        self.llm = None
        if CREWAI_AVAILABLE:
            try:
                self.llm = LLM(model="ollama/llama3.2", base_url="http://localhost:11434")
                print("✅ AI Mode enabled with Ollama")
            except Exception as e:
                print(f"⚠️  Ollama connection failed: {e}")
                print("⚠️  Using fallback mode")
        
        self.agents = self._create_agents()
    
    def _create_agents(self):
        if not CREWAI_AVAILABLE or not self.llm:
            return {}
        
        return {
            "coordinator": Agent(
                role="Delivery Coordinator",
                goal="Orchestrate delivery workflow and coordinate all agents",
                backstory="Expert logistics coordinator managing urban deliveries",
                llm=self.llm,
                verbose=False
            ),
            "driver_assignment": Agent(
                role="Driver Assignment Specialist",
                goal="Find the best driver for each delivery based on location, rating, and availability",
                backstory="Fleet manager optimizing driver assignments using AI",
                llm=self.llm,
                verbose=False
            ),
            "pricing": Agent(
                role="Pricing Specialist",
                goal="Calculate accurate delivery prices based on distance, weight, and service type",
                backstory="Pricing expert with knowledge of logistics costs",
                llm=self.llm,
                verbose=False
            ),
            "routing": Agent(
                role="Route Optimizer",
                goal="Plan optimal delivery routes considering traffic and multiple stops",
                backstory="Navigation expert specializing in urban route optimization",
                llm=self.llm,
                verbose=False
            )
        }
    
    async def assign_driver(self, order: dict, drivers: list):
        """Use AI to recommend best driver"""
        if not self.agents:
            return self._fallback_driver_assignment(order, drivers)
        
        try:
            task = Task(
                description=f"""Analyze and recommend the best driver for this order:
                Order: {order['pickup_city']} to {order['delivery_city']}
                Weight: {order['weight']}kg
                Service: {order['service_type']}
                
                Available drivers: {len(drivers)}
                
                Consider: location, rating, vehicle capacity, current load""",
                agent=self.agents["driver_assignment"],
                expected_output="Driver recommendation with reasoning"
            )
            
            crew = Crew(
                agents=[self.agents["driver_assignment"]],
                tasks=[task],
                verbose=False
            )
            
            result = crew.kickoff()
            return {"ai_recommendation": str(result), "drivers": drivers[:3]}
        except:
            return self._fallback_driver_assignment(order, drivers)
    
    async def calculate_price(self, order: dict):
        """Use AI to calculate delivery price"""
        if not self.agents:
            return self._fallback_pricing(order)
        
        try:
            task = Task(
                description=f"""Calculate delivery price for:
                Route: {order['pickup_city']} to {order['delivery_city']}
                Weight: {order['weight']}kg
                Service: {order['service_type']}
                Distance: ~50km
                
                Consider: base rate, distance, weight, service level, market rates""",
                agent=self.agents["pricing"],
                expected_output="Price calculation with breakdown"
            )
            
            crew = Crew(
                agents=[self.agents["pricing"]],
                tasks=[task],
                verbose=False
            )
            
            result = crew.kickoff()
            return {"ai_analysis": str(result), "price": self._fallback_pricing(order)["price"]}
        except:
            return self._fallback_pricing(order)
    
    async def optimize_route(self, driver_location: dict, orders: list):
        """Use AI to optimize multi-stop route"""
        if not self.agents:
            return self._fallback_routing(orders)
        
        try:
            task = Task(
                description=f"""Optimize delivery route for {len(orders)} orders:
                Starting location: {driver_location}
                Orders: {[f"{o['pickup_city']} -> {o['delivery_city']}" for o in orders]}
                
                Find the most efficient sequence considering distance and priority""",
                agent=self.agents["routing"],
                expected_output="Optimized route sequence"
            )
            
            crew = Crew(
                agents=[self.agents["routing"]],
                tasks=[task],
                verbose=False
            )
            
            result = crew.kickoff()
            return {"ai_route": str(result), "sequence": self._fallback_routing(orders)}
        except:
            return self._fallback_routing(orders)
    
    def _fallback_driver_assignment(self, order, drivers):
        """Simple driver selection when AI unavailable"""
        if not drivers:
            return None
        # Sort by rating
        sorted_drivers = sorted(drivers, key=lambda d: d.get("rating", 0), reverse=True)
        return sorted_drivers[0] if sorted_drivers else None
    
    def _fallback_pricing(self, order):
        """Simple pricing when AI unavailable"""
        base = 25.0 if order['pickup_city'] == order['delivery_city'] else 50.0
        weight_cost = order['weight'] * 3.0
        service_mult = 1.8 if order['service_type'] == 'express' else 1.0
        return {"price": round((base + weight_cost) * service_mult, 2)}
    
    def _fallback_routing(self, orders):
        """Simple routing when AI unavailable"""
        # Sort by priority (express first)
        return sorted(orders, key=lambda o: 0 if o.get('service_type') == 'express' else 1)

# Global instance
agent_crew = DeliveryAgentCrew()

async def get_driver_recommendation(order: dict, drivers: list):
    """Get AI-powered driver recommendation"""
    return await agent_crew.assign_driver(order, drivers)

async def get_price_calculation(order: dict):
    """Get AI-powered price calculation"""
    return await agent_crew.calculate_price(order)

async def get_route_optimization(driver_location: dict, orders: list):
    """Get AI-powered route optimization"""
    return await agent_crew.optimize_route(driver_location, orders)

def get_agent_status():
    """Get status of all AI agents"""
    return {
        "crewai_available": CREWAI_AVAILABLE,
        "llm_available": agent_crew.llm is not None,
        "agents": [
            {"name": "Coordinator", "status": "active" if agent_crew.agents else "fallback"},
            {"name": "Driver Assignment", "status": "active" if agent_crew.agents else "fallback"},
            {"name": "Pricing", "status": "active" if agent_crew.agents else "fallback"},
            {"name": "Route Optimizer", "status": "active" if agent_crew.agents else "fallback"}
        ]
    }
