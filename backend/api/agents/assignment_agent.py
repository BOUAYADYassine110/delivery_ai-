"""Assignment Agent - AI-powered driver selection"""
try:
    from crewai import Agent, Task, Crew
    from crewai.llm import LLM
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = Task = Crew = LLM = None

class AssignmentAgent:
    def __init__(self):
        self.agent = None
        if CREWAI_AVAILABLE:
            try:
                llm = LLM(model="ollama/llama3.2", base_url="http://localhost:11434")
                self.agent = Agent(
                    role="Driver Assignment Specialist",
                    goal="Select the optimal driver for delivery orders based on multiple factors",
                    backstory="Expert logistics coordinator with years of experience in driver assignment and route optimization",
                    llm=llm,
                    verbose=True
                )
            except Exception as e:
                print(f"Assignment agent init error: {e}")
    
    async def recommend_driver(self, order: dict, drivers: list):
        if not self.agent or not drivers:
            return None
        
        try:
            driver_info = "\n".join([
                f"- {d['name']}: {d['vehicle_type']}, rating {d['rating']}/5, status {d['status']}, "
                f"city {d.get('assigned_city', 'Unknown')}, current orders: {len(d.get('current_orders', []))}"
                for d in drivers[:10]
            ])
            
            task = Task(
                description=f"""Analyze and select the best driver for this delivery:

Order Details:
- Pickup City: {order['pickup_city']}
- Delivery City: {order['delivery_city']}
- Weight: {order['weight']}kg
- Service Type: {order.get('service_type', 'standard')}
- Is Inter-City: {order.get('is_inter_city', False)}

Available Drivers:
{driver_info}

Consider:
1. Driver must be in pickup city
2. Vehicle capacity for package weight
3. Driver availability and current workload
4. Driver rating and performance
5. Service type requirements (express needs fast vehicle)

Respond with ONLY the driver name, nothing else.""",
                agent=self.agent,
                expected_output="Driver name only"
            )
            
            crew = Crew(agents=[self.agent], tasks=[task], verbose=True)
            result = str(crew.kickoff()).strip()
            
            selected_driver = None
            for driver in drivers:
                if driver['name'].lower() in result.lower():
                    selected_driver = driver
                    break
            
            return {"driver": selected_driver, "ai_reasoning": result}
        except Exception as e:
            print(f"Assignment agent error: {e}")
            return None
