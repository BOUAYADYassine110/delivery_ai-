try:
    from crewai import Agent
    from crewai.llm import LLM
    
    llm = LLM(model="ollama/llama3.1", base_url="http://localhost:11434")
    
    smart_routing_agent = Agent(
        role="Smart Routing Specialist",
        goal="Calculate optimal routes, monitor traffic and weather in real-time, and automatically reroute when conditions change",
        backstory="Navigation expert with real-time traffic analysis capabilities. Uses AI to predict best routes and adapt to changing conditions like traffic jams and weather.",
        llm=llm,
        verbose=True
    )
except ImportError:
    # Fallback agent
    class MockAgent:
        def __init__(self):
            self.role = "Smart Routing Specialist"
    smart_routing_agent = MockAgent()
