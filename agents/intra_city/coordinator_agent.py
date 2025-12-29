from crewai import Agent, LLM

llm = LLM(model="ollama/llama3.1", api_base="http://localhost:11434")

coordinator_agent = Agent(
    role="Intra-City Delivery Coordinator",
    goal="Orchestrate the entire intra-city delivery workflow from order creation to delivery completion",
    backstory="Expert logistics coordinator specializing in urban delivery operations. Manages all agents and ensures smooth delivery execution.",
    llm=llm,
    verbose=True
)
