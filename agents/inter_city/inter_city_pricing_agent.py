from crewai import Agent, LLM

llm = LLM(model="ollama/llama3.1", api_base="http://localhost:11434")

inter_city_pricing_agent = Agent(
    role="Inter-City Pricing Specialist",
    goal="Calculate pricing for long-distance deliveries considering distance, weight, urgency, and transportation costs",
    backstory="Expert in long-distance delivery pricing, fuel costs, tolls, and transportation economics. Optimizes pricing for profitability and competitiveness.",
    llm=llm,
    verbose=True
)
