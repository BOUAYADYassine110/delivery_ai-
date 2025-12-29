#!/usr/bin/env python3
"""
Fix CrewAI Pydantic Version Conflict
"""

import subprocess
import sys

print("=" * 60)
print("🔧 Fixing CrewAI Dependencies")
print("=" * 60)

print("\n1️⃣ Upgrading CrewAI to latest version...")
try:
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "crewai"], check=True)
    print("   ✅ CrewAI upgraded")
except:
    print("   ❌ Failed to upgrade CrewAI")

print("\n2️⃣ Installing crewai-tools...")
try:
    subprocess.run([sys.executable, "-m", "pip", "install", "crewai-tools"], check=True)
    print("   ✅ crewai-tools installed")
except:
    print("   ⚠️  crewai-tools optional")

print("\n3️⃣ Testing import...")
try:
    from crewai import Agent, Task, Crew, LLM
    print("   ✅ CrewAI imports working")
except Exception as e:
    print(f"   ❌ Import error: {e}")

print("\n" + "=" * 60)
print("✅ Setup complete! Run: python test_agents.py")
print("=" * 60)
