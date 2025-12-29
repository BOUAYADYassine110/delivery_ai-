# MongoDB Integration Guide

## 🚀 Quick Start

### Step 1: Install MongoDB
```bash
# Download MongoDB Community Server from:
# https://www.mongodb.com/try/download/community

# Or use Docker:
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### Step 2: Initialize Database
```bash
cd backend
python init_mongodb.py
```

Expected output:
```
🔄 Initializing MongoDB...
✅ Cleared existing collections
✅ Inserted 16 drivers
✅ Inserted 2 users
✅ Inserted 6 warehouses
✅ Created indexes
🎉 MongoDB initialization complete!
```

### Step 3: Start Backend
```bash
python main.py
```

## ✅ What's Integrated

### Collections Created
- **drivers** - 16 drivers across 6 cities
- **orders** - All delivery orders
- **users** - Customer and admin accounts
- **warehouses** - 6 warehouse locations

### Indexes Created
- `drivers.email` (unique)
- `drivers.assigned_city`
- `drivers.status`
- `orders.tracking_number` (unique)
- `orders.status`
- `orders.assigned_driver`
- `users.username` (unique)

### Data Seeded
✅ 16 Drivers (DRV001-DRV016)
✅ 6 Warehouses (Casablanca, Rabat, Marrakech, Agadir, El Jadida, Salé)
✅ 2 Test Users (testuser, admin)

## 🔧 Configuration

### Environment Variables (.env)
```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=delivery_system
SECRET_KEY=your-secret-key-here
```

## 📊 Verify Installation

### Check MongoDB Connection
```bash
# Using MongoDB Shell
mongosh
use delivery_system
db.drivers.countDocuments()  # Should return 16
db.warehouses.countDocuments()  # Should return 6
```

### Test API
```bash
# Get all drivers
curl http://localhost:8001/api/drivers/by-city

# Get system coverage
curl http://localhost:8001/api/system/coverage
```

## 🎯 Next Steps

1. ✅ MongoDB installed and running
2. ✅ Database initialized with data
3. ✅ Backend connected to MongoDB
4. ⏳ Test order creation
5. ⏳ Test driver assignment
6. ⏳ Test order tracking

## 🐛 Troubleshooting

### MongoDB not starting
```bash
# Check if MongoDB is running
mongosh --eval "db.version()"

# Start MongoDB service (Windows)
net start MongoDB

# Start MongoDB service (Linux/Mac)
sudo systemctl start mongod
```

### Connection refused
- Check MONGODB_URL in .env
- Ensure MongoDB is running on port 27017
- Check firewall settings

### Data not showing
```bash
# Re-run initialization
python init_mongodb.py
```

## 📝 Important Notes

- All in-memory data has been migrated to MongoDB
- Data persists across server restarts
- Indexes improve query performance
- Unique constraints prevent duplicates

## ✨ Benefits

✅ **Data Persistence** - No data loss on restart
✅ **Scalability** - Handle thousands of orders
✅ **Performance** - Indexed queries
✅ **Reliability** - ACID transactions
✅ **Backup** - Easy data backup/restore
