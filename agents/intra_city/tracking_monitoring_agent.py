from crewai import Agent, LLM

llm = LLM(model="ollama/llama3.1", api_base="http://localhost:11434")

tracking_monitoring_agent = Agent(
    role="Tracking & Monitoring Specialist",
    goal="Provide real-time location tracking, broadcast updates to customers, monitor system performance, and generate analytics",
    backstory="Operations analyst with real-time tracking expertise. Ensures customers always know where their package is and monitors system health.",
    llm=llm,
    verbose=True
)
