# MongoDB Integration Guide

## Quick Start (5 minutes)

### 1. Install MongoDB
**Windows:**
```bash
# Download from https://www.mongodb.com/try/download/community
# Or use chocolatey:
choco install mongodb
```

**Mac:**
```bash
brew tap mongodb/brew
brew install mongodb-community
```

**Linux:**
```bash
sudo apt-get install mongodb
```

### 2. Start MongoDB
```bash
# Windows
net start MongoDB

# Mac/Linux
sudo systemctl start mongod
```

### 3. Initialize Database
```bash
cd backend
python init_db.py
```

### 4. Enable MongoDB in main.py

**Option A: Use environment variable**
```bash
# In .env file
USE_MONGODB=true
```

**Option B: Code change (1 line)**
In `backend/main.py`, change line ~60:
```python
USE_MONGODB = os.getenv("USE_MONGODB", "false").lower() == "true"
```

### 5. Restart Backend
```bash
python main.py
```

## What You Get

✅ **Data Persistence** - Orders and users survive server restarts
✅ **Better Performance** - Indexed queries for faster lookups
✅ **Scalability** - Ready for production deployment
✅ **Backup Support** - Easy data backup and recovery

## Verify It's Working

Visit: http://localhost:8001/api/health/mongodb

Should show:
```json
{
  "status": "connected",
  "collections": ["users", "orders", "drivers", "warehouses"],
  "message": "✅ MongoDB is working!"
}
```

## Rollback to In-Memory

Set in `.env`:
```
USE_MONGODB=false
```

Or remove the environment variable entirely.
