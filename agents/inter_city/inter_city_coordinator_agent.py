from crewai import Agent, LLM

llm = LLM(model="ollama/llama3.1", api_base="http://localhost:11434")

inter_city_coordinator_agent = Agent(
    role="Inter-City Delivery Coordinator",
    goal="Orchestrate complex multi-city delivery workflows from pickup to final delivery across different cities",
    backstory="Expert in coordinating complex logistics operations across multiple cities. Manages the entire inter-city delivery lifecycle from planning to completion.",
    llm=llm,
    verbose=True
)
