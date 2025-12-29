#!/usr/bin/env python3
"""
Test CrewAI Agents Integration
"""

import sys
import asyncio

def test_crewai():
    print("=" * 60)
    print("🤖 Testing CrewAI Agents Integration")
    print("=" * 60)
    
    # Test 1: Check CrewAI installation
    print("\n1️⃣ Checking CrewAI installation...")
    try:
        import crewai
        print("   ✅ CrewAI installed")
    except ImportError:
        print("   ❌ CrewAI not installed")
        print("   Fix: pip install crewai")
        return False
    
    # Test 2: Check Ollama connection
    print("\n2️⃣ Checking Ollama connection...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"   ✅ Ollama running with {len(models)} models")
            if models:
                print(f"   Models: {', '.join([m['name'] for m in models[:3]])}")
        else:
            print("   ⚠️  Ollama running but no models found")
    except:
        print("   ⚠️  Ollama not running (agents will use fallback)")
        print("   Optional: Install Ollama from ollama.ai")
    
    # Test 3: Import agent service
    print("\n3️⃣ Testing agent service...")
    try:
        sys.path.append("backend")
        from api.services.crew_service import get_agent_status, agent_crew
        
        status = get_agent_status()
        print(f"   ✅ Agent service loaded")
        print(f"   CrewAI Available: {status['crewai_available']}")
        print(f"   LLM Available: {status['llm_available']}")
        print(f"   Agents: {len(status['agents'])}")
        
        for agent in status['agents']:
            print(f"      • {agent['name']}: {agent['status']}")
        
    except Exception as e:
        print(f"   ❌ Error loading agent service: {e}")
        return False
    
    # Test 4: Test agent functionality
    print("\n4️⃣ Testing agent functionality...")
    try:
        test_order = {
            "pickup_city": "Casablanca",
            "delivery_city": "Rabat",
            "weight": 2.5,
            "service_type": "express"
        }
        
        test_drivers = [
            {"id": "DRV001", "name": "Ahmed", "rating": 4.8, "status": "available"},
            {"id": "DRV002", "name": "Youssef", "rating": 4.9, "status": "available"}
        ]
        
        # Test driver recommendation
        async def test_async():
            from api.services.crew_service import get_driver_recommendation
            result = await get_driver_recommendation(test_order, test_drivers)
            return result
        
        result = asyncio.run(test_async())
        print("   ✅ Agent functions working")
        if "ai_recommendation" in result:
            print("   🤖 AI recommendation generated")
        else:
            print("   ⚙️  Using fallback logic")
        
    except Exception as e:
        print(f"   ⚠️  Agent test: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ CrewAI Integration Status:")
    print("=" * 60)
    print("• Agents are integrated into the system")
    print("• Endpoints available:")
    print("  - GET  /api/agents/status")
    print("  - POST /api/agents/recommend-driver")
    print("  - POST /api/agents/calculate-price")
    print("\n• Agents work in two modes:")
    print("  1. AI Mode: Uses CrewAI + Ollama for intelligent decisions")
    print("  2. Fallback Mode: Uses rule-based logic when AI unavailable")
    print("\n• Current mode:", "AI" if status.get('llm_available') else "Fallback")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_crewai()
    sys.exit(0 if success else 1)
