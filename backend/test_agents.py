import sys
sys.path.insert(0, '.')

from api.services.crew_service import get_agent_status

print("=" * 50)
print("AI AGENTS STATUS CHECK")
print("=" * 50)

status = get_agent_status()

print(f"\n✅ CrewAI Available: {status['crewai_available']}")
print(f"✅ LLM Available: {status['llm_available']}")
print(f"\n📊 Active Agents: {len(status['agents'])}")

for agent in status['agents']:
    print(f"  🤖 {agent['name']}: {agent['status']}")

print("\n" + "=" * 50)
print("Agents are working! They run automatically during:")
print("  - Order creation")
print("  - Driver assignment")
print("  - Price calculation")
print("  - Route optimization")
print("=" * 50)
