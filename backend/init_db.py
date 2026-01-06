"""
Database Initialization Script
Run this once to set up MongoDB with default data
"""
import asyncio
from database import init_database, seed_default_data, async_client
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def setup_database():
    """Initialize and seed database"""
    print("="*60)
    print("🗄️  DATABASE INITIALIZATION")
    print("="*60)
    
    try:
        # Test connection
        print("\n1️⃣  Testing MongoDB connection...")
        await async_client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Initialize indexes
        print("\n2️⃣  Creating database indexes...")
        await init_database()
        
        # Seed default data
        print("\n3️⃣  Seeding default data...")
        await seed_default_data()
        
        print("\n" + "="*60)
        print("✅ DATABASE SETUP COMPLETE!")
        print("="*60)
        print("\n📊 Default Data Loaded:")
        print("   - 16 Drivers across 6 cities")
        print("   - 6 Warehouses")
        print("   - 1 Admin user (admin/admin123)")
        print("\n🚀 You can now start the backend server")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Database setup failed: {e}")
        print("\n💡 Make sure MongoDB is running:")
        print("   - Windows: Start MongoDB service")
        print("   - Mac/Linux: sudo systemctl start mongod")
        print("   - Or use MongoDB Atlas cloud database")
        return False
    
    finally:
        async_client.close()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(setup_database())
    exit(0 if success else 1)
