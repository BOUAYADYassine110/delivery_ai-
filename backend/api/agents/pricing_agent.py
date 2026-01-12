"""Pricing Agent - AI-powered price calculation"""
try:
    from crewai import Agent, Task, Crew
    from crewai.llm import LLM
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = Task = Crew = LLM = None

class PricingAgent:
    def __init__(self):
        self.agent = None
        if CREWAI_AVAILABLE:
            try:
                llm = LLM(model="ollama/llama3.2", base_url="http://localhost:11434")
                self.agent = Agent(
                    role="Pricing Agent",
                    goal="Calculate accurate delivery prices",
                    backstory="Expert in logistics pricing",
                    llm=llm,
                    verbose=False
                )
            except Exception as e:
                print(f"Pricing agent init error: {e}")
    
    async def calculate_price(self, weight: float, distance: float, service_type: str):
        if not self.agent:
            return self._fallback_pricing(weight, distance, service_type)
        
        try:
            task = Task(
                description=f"Calculate delivery price for: weight={weight}kg, distance={distance}km, service={service_type}",
                agent=self.agent,
                expected_output="Price in dollars"
            )
            crew = Crew(agents=[self.agent], tasks=[task], verbose=False)
            result = crew.kickoff()
            return {"price": round(15.0 + weight * 2 + distance * 0.5, 2), "ai_analysis": str(result)}
        except Exception:
            return self._fallback_pricing(weight, distance, service_type)
    
    def _fallback_pricing(self, weight: float, distance: float, service_type: str):
        base_price = 15.0
        weight_cost = weight * 2.0
        distance_cost = distance * 0.5
        service_multiplier = {'standard': 1.0, 'express': 1.5, 'overnight': 2.0}.get(service_type, 1.0)
        total = (base_price + weight_cost + distance_cost) * service_multiplier
        return {"price": round(total, 2)}
