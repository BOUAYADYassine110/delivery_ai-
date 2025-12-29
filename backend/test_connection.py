import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test_mongodb():
    try:
        client = AsyncIOMotorClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        print("[OK] MongoDB connection successful!")
        
        db = client.delivery_system
        collections = await db.list_collection_names()
        print(f"[OK] Database 'delivery_system' accessible")
        print(f"     Collections: {collections if collections else 'None (empty database)'}")
        
        client.close()
        return True
    except Exception as e:
        print(f"[ERROR] MongoDB connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_mongodb())
