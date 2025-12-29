from crewai import Agent, LLM

llm = LLM(model="ollama/llama3.1", api_base="http://localhost:11434")

inter_city_client_service_agent = Agent(
    role="Inter-City Client Service Specialist",
    goal="Handle customer interactions for long-distance deliveries, manage expectations, and provide updates",
    backstory="Specialist in managing customer expectations for long-distance deliveries. Provides clear communication and handles complex delivery scenarios.",
    llm=llm,
    verbose=True
)
