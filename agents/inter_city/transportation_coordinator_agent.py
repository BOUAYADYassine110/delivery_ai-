from crewai import Agent, LLM

llm = LLM(model="ollama/llama3.1", api_base="http://localhost:11434")

transportation_coordinator_agent = Agent(
    role="Transportation Coordinator",
    goal="Coordinate transportation between cities, manage vehicle assignments, and ensure timely package transfers",
    backstory="Specialist in coordinating various transportation modes for inter-city deliveries. Manages truck schedules, train connections, and air freight operations.",
    llm=llm,
    verbose=True
)
