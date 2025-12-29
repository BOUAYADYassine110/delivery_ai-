"""
MongoDB Initialization Script
Run this once to populate the database with initial data
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "delivery_system"

async def init_database():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    print("🔄 Initializing MongoDB...")
    
    # Clear existing data
    await db.drivers.delete_many({})
    await db.orders.delete_many({})
    await db.users.delete_many({})
    await db.warehouses.delete_many({})
    
    print("✅ Cleared existing collections")
    
    # Insert 16 Drivers
    drivers = [
        # Casablanca (4 drivers)
        {"_id": "DRV001", "name": "Ahmed Benali", "email": "ahmed@delivery.ma", "phone": "+212661234567", "vehicle_type": "bike", "vehicle_capacity": 20.0, "assigned_city": "Casablanca", "current_location": {"lat": 33.5731, "lng": -7.5898, "city": "Casablanca"}, "status": "available", "current_orders": [], "rating": 4.8, "total_deliveries": 156, "working_hours": {"start": "08:00", "end": "20:00"}, "specialties": ["express_delivery", "documents"]},
        {"_id": "DRV002", "name": "Youssef Alami", "email": "youssef@delivery.ma", "phone": "+212662345678", "vehicle_type": "car", "vehicle_capacity": 100.0, "assigned_city": "Casablanca", "current_location": {"lat": 33.5850, "lng": -7.6000, "city": "Casablanca"}, "status": "available", "current_orders": [], "rating": 4.9, "total_deliveries": 203, "working_hours": {"start": "07:00", "end": "19:00"}, "specialties": ["bulk_delivery", "fragile_items"]},
        {"_id": "DRV003", "name": "Fatima Zahra", "email": "fatima@delivery.ma", "phone": "+212663456789", "vehicle_type": "scooter", "vehicle_capacity": 30.0, "assigned_city": "Casablanca", "current_location": {"lat": 33.5600, "lng": -7.5700, "city": "Casablanca"}, "status": "available", "current_orders": [], "rating": 4.7, "total_deliveries": 89, "working_hours": {"start": "09:00", "end": "21:00"}, "specialties": ["fast_delivery", "city_center"]},
        {"_id": "DRV004", "name": "Karim Bennani", "email": "karim@delivery.ma", "phone": "+212664567890", "vehicle_type": "van", "vehicle_capacity": 200.0, "assigned_city": "Casablanca", "current_location": {"lat": 33.5900, "lng": -7.6100, "city": "Casablanca"}, "status": "available", "current_orders": [], "rating": 4.6, "total_deliveries": 312, "working_hours": {"start": "06:00", "end": "18:00"}, "specialties": ["heavy_cargo", "warehouse", "inter_city"]},
        
        # Rabat (3 drivers)
        {"_id": "DRV005", "name": "Laila Alaoui", "email": "laila@delivery.ma", "phone": "+212665678901", "vehicle_type": "car", "vehicle_capacity": 80.0, "assigned_city": "Rabat", "current_location": {"lat": 34.0209, "lng": -6.8416, "city": "Rabat"}, "status": "available", "current_orders": [], "rating": 4.9, "total_deliveries": 145, "working_hours": {"start": "07:30", "end": "20:30"}, "specialties": ["residential", "same_day"]},
        {"_id": "DRV006", "name": "Omar Tazi", "email": "omar@delivery.ma", "phone": "+212666789012", "vehicle_type": "bike", "vehicle_capacity": 25.0, "assigned_city": "Rabat", "current_location": {"lat": 34.0300, "lng": -6.8500, "city": "Rabat"}, "status": "available", "current_orders": [], "rating": 4.8, "total_deliveries": 67, "working_hours": {"start": "08:30", "end": "19:30"}, "specialties": ["express_delivery", "documents"]},
        {"_id": "DRV007", "name": "Nadia Benali", "email": "nadia@delivery.ma", "phone": "+212667890123", "vehicle_type": "scooter", "vehicle_capacity": 35.0, "assigned_city": "Rabat", "current_location": {"lat": 34.0100, "lng": -6.8300, "city": "Rabat"}, "status": "available", "current_orders": [], "rating": 4.7, "total_deliveries": 98, "working_hours": {"start": "08:00", "end": "20:00"}, "specialties": ["fast_delivery", "fragile_items"]},
        
        # Marrakech (3 drivers)
        {"_id": "DRV008", "name": "Hassan Alami", "email": "hassan@delivery.ma", "phone": "+212668901234", "vehicle_type": "car", "vehicle_capacity": 90.0, "assigned_city": "Marrakech", "current_location": {"lat": 31.6295, "lng": -7.9811, "city": "Marrakech"}, "status": "available", "current_orders": [], "rating": 4.8, "total_deliveries": 134, "working_hours": {"start": "07:00", "end": "19:00"}, "specialties": ["bulk_delivery", "residential"]},
        {"_id": "DRV009", "name": "Aicha Bennani", "email": "aicha@delivery.ma", "phone": "+212669012345", "vehicle_type": "bike", "vehicle_capacity": 22.0, "assigned_city": "Marrakech", "current_location": {"lat": 31.6400, "lng": -7.9900, "city": "Marrakech"}, "status": "available", "current_orders": [], "rating": 4.6, "total_deliveries": 76, "working_hours": {"start": "09:00", "end": "21:00"}, "specialties": ["express_delivery", "city_center"]},
        {"_id": "DRV010", "name": "Rachid Tazi", "email": "rachid@delivery.ma", "phone": "+212660123456", "vehicle_type": "van", "vehicle_capacity": 180.0, "assigned_city": "Marrakech", "current_location": {"lat": 31.6200, "lng": -7.9700, "city": "Marrakech"}, "status": "available", "current_orders": [], "rating": 4.9, "total_deliveries": 201, "working_hours": {"start": "06:00", "end": "18:00"}, "specialties": ["heavy_cargo", "warehouse", "inter_city"]},
        
        # Agadir (2 drivers)
        {"_id": "DRV011", "name": "Khadija Alaoui", "email": "khadija@delivery.ma", "phone": "+212661234567", "vehicle_type": "van", "vehicle_capacity": 200.0, "assigned_city": "Agadir", "current_location": {"lat": 30.4278, "lng": -9.5981, "city": "Agadir"}, "status": "available", "current_orders": [], "rating": 4.9, "total_deliveries": 312, "working_hours": {"start": "06:00", "end": "18:00"}, "specialties": ["heavy_cargo", "long_distance", "warehouse"]},
        {"_id": "DRV012", "name": "Mehdi Benali", "email": "mehdi@delivery.ma", "phone": "+212662345678", "vehicle_type": "car", "vehicle_capacity": 85.0, "assigned_city": "Agadir", "current_location": {"lat": 30.4400, "lng": -9.6100, "city": "Agadir"}, "status": "available", "current_orders": [], "rating": 4.7, "total_deliveries": 89, "working_hours": {"start": "08:00", "end": "20:00"}, "specialties": ["coastal_delivery", "same_day"]},
        
        # El Jadida (2 drivers)
        {"_id": "DRV013", "name": "Zineb Alami", "email": "zineb@delivery.ma", "phone": "+212663456789", "vehicle_type": "bike", "vehicle_capacity": 25.0, "assigned_city": "El Jadida", "current_location": {"lat": 33.2316, "lng": -8.5007, "city": "El Jadida"}, "status": "available", "current_orders": [], "rating": 4.6, "total_deliveries": 67, "working_hours": {"start": "08:30", "end": "19:30"}, "specialties": ["coastal_delivery", "documents"]},
        {"_id": "DRV014", "name": "Samir Bennani", "email": "samir@delivery.ma", "phone": "+212664567890", "vehicle_type": "scooter", "vehicle_capacity": 40.0, "assigned_city": "El Jadida", "current_location": {"lat": 33.2400, "lng": -8.5100, "city": "El Jadida"}, "status": "available", "current_orders": [], "rating": 4.8, "total_deliveries": 123, "working_hours": {"start": "07:00", "end": "19:00"}, "specialties": ["fast_delivery", "express_delivery"]},
        
        # Salé (2 drivers)
        {"_id": "DRV015", "name": "Amina Tazi", "email": "amina@delivery.ma", "phone": "+212665678901", "vehicle_type": "car", "vehicle_capacity": 80.0, "assigned_city": "Salé", "current_location": {"lat": 34.0531, "lng": -6.7985, "city": "Salé"}, "status": "available", "current_orders": [], "rating": 4.8, "total_deliveries": 145, "working_hours": {"start": "07:30", "end": "20:30"}, "specialties": ["residential", "same_day"]},
        {"_id": "DRV016", "name": "Khalid Alaoui", "email": "khalid@delivery.ma", "phone": "+212666789012", "vehicle_type": "bike", "vehicle_capacity": 28.0, "assigned_city": "Salé", "current_location": {"lat": 34.0600, "lng": -6.8100, "city": "Salé"}, "status": "available", "current_orders": [], "rating": 4.7, "total_deliveries": 92, "working_hours": {"start": "08:00", "end": "20:00"}, "specialties": ["express_delivery", "documents"]}
    ]
    
    await db.drivers.insert_many(drivers)
    print(f"✅ Inserted {len(drivers)} drivers")
    
    # Insert Test Users
    users = [
        {"_id": "USER001", "username": "testuser", "password": "test123", "email": "test@example.com", "full_name": "Test User", "role": "client", "created_at": datetime.now().isoformat()},
        {"_id": "ADMIN001", "username": "admin", "password": "admin123", "email": "admin@delivery.ma", "full_name": "Admin User", "role": "admin", "created_at": datetime.now().isoformat()}
    ]
    
    await db.users.insert_many(users)
    print(f"✅ Inserted {len(users)} users")
    
    # Insert Warehouses
    warehouses = [
        {"_id": "WH_CASA", "city": "Casablanca", "lat": 33.5731, "lng": -7.5898, "capacity": 1000, "current_load": 0},
        {"_id": "WH_RABAT", "city": "Rabat", "lat": 34.0209, "lng": -6.8416, "capacity": 800, "current_load": 0},
        {"_id": "WH_MARR", "city": "Marrakech", "lat": 31.6295, "lng": -7.9811, "capacity": 600, "current_load": 0},
        {"_id": "WH_AGAD", "city": "Agadir", "lat": 30.4278, "lng": -9.5981, "capacity": 500, "current_load": 0},
        {"_id": "WH_JADI", "city": "El Jadida", "lat": 33.2316, "lng": -8.5007, "capacity": 400, "current_load": 0},
        {"_id": "WH_SALE", "city": "Salé", "lat": 34.0531, "lng": -6.7985, "capacity": 300, "current_load": 0}
    ]
    
    await db.warehouses.insert_many(warehouses)
    print(f"✅ Inserted {len(warehouses)} warehouses")
    
    # Create indexes
    await db.drivers.create_index("email", unique=True)
    await db.drivers.create_index("assigned_city")
    await db.drivers.create_index("status")
    await db.orders.create_index("tracking_number", unique=True)
    await db.orders.create_index("status")
    await db.orders.create_index("assigned_driver")
    await db.users.create_index("username", unique=True)
    
    print("✅ Created indexes")
    print("\n🎉 MongoDB initialization complete!")
    print(f"📊 Database: {DATABASE_NAME}")
    print(f"👥 Drivers: {len(drivers)}")
    print(f"🏢 Warehouses: {len(warehouses)}")
    print(f"👤 Users: {len(users)}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(init_database())
