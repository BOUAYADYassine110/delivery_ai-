import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def reset_orders():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.delivery_system
    
    # Drop orders collection to remove old schema validation
    await db.orders.drop()
    print("[OK] Orders collection dropped")
    
    # Recreate without validation
    await db.create_collection("orders")
    print("[OK] Orders collection recreated")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(reset_orders())
