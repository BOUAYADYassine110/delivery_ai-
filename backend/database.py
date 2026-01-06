"""
MongoDB Database Configuration
Handles all database connections and collections
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from datetime import datetime

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "delivery_system")

# Async client for FastAPI
async_client = AsyncIOMotorClient(MONGODB_URL)
async_db = async_client[DATABASE_NAME]

# Sync client for initialization
sync_client = MongoClient(MONGODB_URL)
sync_db = sync_client[DATABASE_NAME]

# Collections
users_collection = async_db.users
orders_collection = async_db.orders
drivers_collection = async_db.drivers
warehouses_collection = async_db.warehouses
admins_collection = async_db.admins

async def init_database():
    """Initialize database with indexes and default data"""
    
    # Create indexes
    await users_collection.create_index("username", unique=True)
    await users_collection.create_index("email", unique=True)
    await orders_collection.create_index("tracking_number", unique=True)
    await orders_collection.create_index("user_id")
    await orders_collection.create_index("status")
    await drivers_collection.create_index("email", unique=True)
    await admins_collection.create_index("username", unique=True)
    
    print("✅ Database indexes created")

async def seed_default_data():
    """Seed database with default drivers, warehouses, and admin"""
    
    # Check if already seeded
    if await drivers_collection.count_documents({}) > 0:
        print("ℹ️  Database already seeded")
        return
    
    print("🌱 Seeding database with default data...")
    
    # Import default data
    from .seed_data import get_default_drivers, get_default_warehouses, get_default_admin
    
    # Insert drivers
    drivers = get_default_drivers()
    await drivers_collection.insert_many(drivers)
    print(f"✅ Inserted {len(drivers)} drivers")
    
    # Insert warehouses
    warehouses = get_default_warehouses()
    await warehouses_collection.insert_many(warehouses)
    print(f"✅ Inserted {len(warehouses)} warehouses")
    
    # Insert default admin
    admin = get_default_admin()
    await admins_collection.insert_one(admin)
    print("✅ Inserted default admin")
    
    print("✅ Database seeding complete")

async def close_database():
    """Close database connections"""
    async_client.close()
    sync_client.close()
