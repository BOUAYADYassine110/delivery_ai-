from crewai import Agent, LLM

llm = LLM(model="ollama/llama3.1", api_base="http://localhost:11434")

client_service_agent = Agent(
    role="Client Service Specialist",
    goal="Handle customer interactions, validate orders, and send notifications throughout the delivery process",
    backstory="Customer service expert with deep knowledge of delivery operations. Ensures customers are informed and satisfied at every step.",
    llm=llm,
    verbose=True
)
