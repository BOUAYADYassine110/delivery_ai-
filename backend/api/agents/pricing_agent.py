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
                    role="Pricing Agent - Morocco",
                    goal="Calculate accurate delivery prices in Moroccan Dirhams (MAD) for the Moroccan market",
                    backstory="""Expert in Moroccan logistics pricing with deep understanding of local market rates. 
                    You always calculate prices in Moroccan Dirhams (MAD), never in dollars. You know that reasonable 
                    delivery prices in Morocco are: 15-30 MAD for intra-city, 50-150 MAD for inter-city depending on 
                    distance. You use rates of 0.3 MAD per km and 2 MAD per kg.""",
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
                description=f"""Calculate delivery price in Moroccan Dirhams (MAD) for: 
                weight={weight}kg, distance={distance}km, service={service_type}.
                Use reasonable Moroccan market rates: base 15-30 MAD, 0.3 MAD/km, 2 MAD/kg.""",
                agent=self.agent,
                expected_output="Price in Moroccan Dirhams (MAD)"
            )
            crew = Crew(agents=[self.agent], tasks=[task], verbose=False)
            result = crew.kickoff()
            # Use reasonable Moroccan rates
            calculated_price = round(15.0 + weight * 2.0 + distance * 0.3, 2)
            return {"price": calculated_price, "ai_analysis": str(result)}
        except Exception:
            return self._fallback_pricing(weight, distance, service_type)
    
    def _fallback_pricing(self, weight: float, distance: float, service_type: str):
        """Fallback pricing in Moroccan Dirhams (MAD)"""
        base_price = 15.0  # MAD
        weight_cost = weight * 2.0  # 2 MAD per kg
        distance_cost = distance * 0.3  # 0.3 MAD per km
        service_multiplier = {'standard': 1.0, 'express': 1.3, 'overnight': 1.5}.get(service_type, 1.0)
        total = (base_price + weight_cost + distance_cost) * service_multiplier
        return {"price": round(total, 2)}
