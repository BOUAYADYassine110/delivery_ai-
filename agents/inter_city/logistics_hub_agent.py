from crewai import Agent, LLM

llm = LLM(model="ollama/llama3.1", api_base="http://localhost:11434")

logistics_hub_agent = Agent(
    role="Logistics Hub Manager",
    goal="Manage inter-city logistics hubs, coordinate package transfers between cities, and optimize hub operations",
    backstory="Specialist in logistics hub operations and inter-city package routing. Manages sorting facilities, cross-docking operations, and hub-to-hub coordination.",
    llm=llm,
    verbose=True
)
