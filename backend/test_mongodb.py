"""
Test MongoDB Integration
Run this to verify MongoDB is working
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("TESTING MONGODB INTEGRATION")
print("="*60)

# Check environment variable
use_mongodb = os.getenv("USE_MONGODB", "false").lower() == "true"
print(f"\n1. USE_MONGODB setting: {use_mongodb}")

if not use_mongodb:
    print("\nMongoDB is DISABLED")
    print("Set USE_MONGODB=true in .env to enable")
    exit(1)

print("\nMongoDB is ENABLED")

# Test MongoDB connection
print("\n2. Testing MongoDB connection...")
try:
    from pymongo import MongoClient
    
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = MongoClient(mongodb_url, serverSelectionTimeoutMS=2000)
    client.admin.command('ping')
    print(f"Connected to MongoDB at {mongodb_url}")
    
    # Check database
    db_name = os.getenv("DATABASE_NAME", "delivery_system")
    db = client[db_name]
    
    # Check collections
    collections = db.list_collection_names()
    print(f"\n3. Database: {db_name}")
    print(f"   Collections: {collections if collections else 'None (will be created on first use)'}")
    
    # Check data
    drivers_count = db.drivers.count_documents({})
    orders_count = db.orders.count_documents({})
    users_count = db.users.count_documents({})
    
    print(f"\n4. Current data:")
    print(f"   Drivers: {drivers_count}")
    print(f"   Orders: {orders_count}")
    print(f"   Users: {users_count}")
    
    if drivers_count == 0:
        print("\nDatabase is empty - will be seeded on first backend start")
    
    print("\n" + "="*60)
    print("MONGODB IS WORKING!")
    print("="*60)
    print("\nStart backend with: python main.py")
    print("Data will now persist between restarts!")
    
except Exception as e:
    print(f"\nMongoDB connection failed: {e}")
    print("\nSolutions:")
    print("   1. Install MongoDB locally")
    print("   2. OR use MongoDB Atlas (free): https://www.mongodb.com/cloud/atlas")
    print("   3. Update MONGODB_URL in .env with your connection string")
    exit(1)
