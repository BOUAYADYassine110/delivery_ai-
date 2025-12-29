from crewai import Agent, LLM

llm = LLM(model="ollama/llama3.1", api_base="http://localhost:11434")

long_distance_routing_agent = Agent(
    role="Long Distance Routing Specialist",
    goal="Plan optimal routes between cities, considering highways, tolls, weather, and transportation modes",
    backstory="Expert in long-distance route optimization, highway systems, and multi-modal transportation planning. Minimizes costs and maximizes efficiency.",
    llm=llm,
    verbose=True
)
