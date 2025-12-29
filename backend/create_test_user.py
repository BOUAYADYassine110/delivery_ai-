import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

async def create_test_user():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.delivery_system
    
    # Check if user exists
    existing = await db.users.find_one({"username": "testuser"})
    if existing:
        print("Test user already exists")
        print(f"Username: testuser")
        print(f"Password: test123")
        return
    
    # Create test user
    user = {
        "email": "test@example.com",
        "username": "testuser",
        "hashed_password": pwd_context.hash("test123"),
        "full_name": "Test User",
        "role": "client",
        "is_active": True,
        "created_at": None
    }
    
    from datetime import datetime
    user["created_at"] = datetime.utcnow()
    
    result = await db.users.insert_one(user)
    print(f"[OK] Test user created!")
    print(f"Username: testuser")
    print(f"Password: test123")
    print(f"User ID: {result.inserted_id}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_test_user())
