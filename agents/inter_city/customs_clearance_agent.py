from crewai import Agent, LLM

llm = LLM(model="ollama/llama3.1", api_base="http://localhost:11434")

customs_clearance_agent = Agent(
    role="Customs Clearance Specialist",
    goal="Handle customs documentation, ensure compliance, and manage international shipping requirements",
    backstory="Expert in customs regulations, documentation, and international shipping compliance. Ensures smooth border crossings and regulatory compliance.",
    llm=llm,
    verbose=True
)
