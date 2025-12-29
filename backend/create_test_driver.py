import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

async def create_test_driver():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.delivery_system
    
    # Check if driver exists
    existing = await db.couriers.find_one({"email": "driver@example.com"})
    if existing:
        print("Test driver already exists")
        print(f"Email: driver@example.com")
        print(f"Password: driver123")
        return
    
    # Create test driver
    driver = {
        "email": "driver@example.com",
        "password_hash": pwd_context.hash("driver123"),
        "name": "Test Driver",
        "phone": "+1234567890",
        "vehicle_type": "bike",
        "vehicle_number": "ABC123",
        "status": "available",
        "rating": 4.5,
        "total_deliveries": 10
    }
    
    from datetime import datetime
    driver["created_at"] = datetime.utcnow()
    
    result = await db.couriers.insert_one(driver)
    print(f"[OK] Test driver created!")
    print(f"Email: driver@example.com")
    print(f"Password: driver123")
    print(f"Driver ID: {result.inserted_id}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_test_driver())
