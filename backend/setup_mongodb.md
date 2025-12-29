# MongoDB Setup Guide for Windows

## Quick Start

### 1. Install MongoDB

**Option A: Using Chocolatey (Recommended)**
```bash
choco install mongodb
```

**Option B: Manual Download**
1. Download from: https://www.mongodb.com/try/download/community
2. Run the installer
3. Choose "Complete" installation
4. Install as Windows Service (recommended)

### 2. Create Data Directory
```bash
mkdir C:\data\db
```

### 3. Start MongoDB

**If installed as service:**
```bash
net start MongoDB
```

**If manual start:**
```bash
mongod --dbpath C:\data\db
```

### 4. Verify MongoDB is Running
```bash
mongosh
# Should connect to MongoDB shell
# Type: exit
```

## Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Update Environment Variables

Create `.env` file in backend folder:
```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=delivery_system
SECRET_KEY=your-secret-key-change-in-production
OLLAMA_HOST=http://localhost:11434
```

## Run the Application

```bash
python main.py
```

## MongoDB Commands

### Check if MongoDB is running:
```bash
mongosh --eval "db.version()"
```

### View databases:
```bash
mongosh
show dbs
use delivery_system
show collections
```

### View data:
```bash
mongosh
use delivery_system
db.orders.find().pretty()
db.users.find().pretty()
```

### Clear all data (for testing):
```bash
mongosh
use delivery_system
db.dropDatabase()
```

## Troubleshooting

### MongoDB won't start:
1. Check if port 27017 is available
2. Ensure data directory exists: `C:\data\db`
3. Check Windows Services for MongoDB service

### Connection errors:
1. Verify MongoDB is running: `mongosh`
2. Check MONGODB_URL in .env file
3. Ensure no firewall blocking port 27017

### Import errors:
```bash
pip install --upgrade motor beanie
```

## MongoDB Compass (GUI Tool)

Download MongoDB Compass for visual database management:
https://www.mongodb.com/try/download/compass

Connection string: `mongodb://localhost:27017`
