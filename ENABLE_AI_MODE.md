# 🤖 Enable AI Mode for CrewAI Agents

## Quick Setup (5 minutes)

### Step 1: Install Ollama

**Windows:**
1. Download: https://ollama.ai/download/windows
2. Run the installer
3. Ollama will start automatically

**Mac:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Step 2: Pull AI Model

Open terminal/command prompt:
```bash
ollama pull llama3.1
```

This downloads the AI model (~4GB). Wait for completion.

### Step 3: Verify Ollama is Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Or visit in browser
http://localhost:11434
```

You should see: "Ollama is running"

### Step 4: Test AI Agents

```bash
cd backend
python test_agents.py
```

You should see:
```
✅ CrewAI installed
✅ Ollama running with 1 models
✅ Agent service loaded
   LLM Available: True
   
Current mode: AI
```

### Step 5: Start Backend

```bash
python backend/main.py
```

Check agent status:
```bash
curl http://localhost:8001/api/agents/status
```

## Troubleshooting

### Ollama Not Running
```bash
# Windows: Check Services, start "Ollama"
# Mac/Linux:
ollama serve
```

### Model Not Found
```bash
# List installed models
ollama list

# Pull llama3.1 if missing
ollama pull llama3.1
```

### Port Already in Use
```bash
# Check what's using port 11434
netstat -ano | findstr :11434  # Windows
lsof -i :11434                 # Mac/Linux
```

## What AI Mode Enables

✅ **Intelligent Driver Assignment**
- AI analyzes driver ratings, location, vehicle type
- Considers traffic patterns and workload
- Provides reasoning for recommendations

✅ **Smart Pricing**
- Dynamic pricing based on demand
- Market rate analysis
- Cost optimization suggestions

✅ **Route Optimization**
- Multi-stop route planning
- Traffic-aware routing
- Fuel efficiency optimization

## System Requirements

- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 5GB free space
- **CPU**: Modern processor (2015+)

## Alternative: Use Without AI

If you can't run Ollama, the system works perfectly in **Fallback Mode**:
- Uses rule-based logic
- No AI required
- Same functionality, different approach

Just start the backend normally:
```bash
python backend/main.py
```

The system automatically detects and adapts!
