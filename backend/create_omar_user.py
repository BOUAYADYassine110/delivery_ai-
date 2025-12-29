import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

async def create_omar_user():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.delivery_system
    
    # Check if user exists
    existing = await db.users.find_one({"username": "omar.tazi"})
    if existing:
        print("Omar Tazi user already exists")
        print(f"Username: omar.tazi")
        print(f"Password: omar123")
        return
    
    # Create Omar Tazi user
    user = {
        "email": "omar.tazi@example.com",
        "username": "omar.tazi",
        "hashed_password": pwd_context.hash("omar123"),
        "full_name": "Omar Tazi",
        "role": "admin",
        "is_active": True,
        "created_at": None
    }
    
    from datetime import datetime
    user["created_at"] = datetime.utcnow()
    
    result = await db.users.insert_one(user)
    print(f"[OK] Omar Tazi user created!")
    print(f"Username: omar.tazi")
    print(f"Password: omar123")
    print(f"Role: admin")
    print(f"User ID: {result.inserted_id}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_omar_user())