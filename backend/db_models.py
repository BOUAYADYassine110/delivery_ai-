"""
Database Models and Helper Functions
Provides clean interface to MongoDB collections
"""
from database import (
    users_collection, orders_collection, drivers_collection,
    warehouses_collection, admins_collection
)
from bson import ObjectId
from datetime import datetime

# Helper to convert MongoDB _id to string
def serialize_doc(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

# USER OPERATIONS
async def create_user(user_data):
    """Create new user"""
    user_data["created_at"] = datetime.now()
    result = await users_collection.insert_one(user_data)
    user_data["_id"] = str(result.inserted_id)
    return user_data

async def get_user_by_username(username):
    """Get user by username"""
    user = await users_collection.find_one({"username": username})
    return serialize_doc(user)

async def get_user_by_id(user_id):
    """Get user by ID"""
    user = await users_collection.find_one({"id": user_id})
    return serialize_doc(user)

# ORDER OPERATIONS
async def create_order(order_data):
    """Create new order"""
    order_data["created_at"] = datetime.now()
    result = await orders_collection.insert_one(order_data)
    order_data["_id"] = str(result.inserted_id)
    return order_data

async def get_order_by_id(order_id):
    """Get order by ID"""
    order = await orders_collection.find_one({"id": order_id})
    return serialize_doc(order)

async def get_orders_by_user(user_id):
    """Get all orders for a user"""
    cursor = orders_collection.find({"user_id": user_id})
    orders = await cursor.to_list(length=100)
    return [serialize_doc(o) for o in orders]

async def get_all_orders():
    """Get all orders"""
    cursor = orders_collection.find({})
    orders = await cursor.to_list(length=1000)
    return [serialize_doc(o) for o in orders]

async def update_order(order_id, update_data):
    """Update order"""
    update_data["updated_at"] = datetime.now()
    await orders_collection.update_one(
        {"id": order_id},
        {"$set": update_data}
    )
    return await get_order_by_id(order_id)

# DRIVER OPERATIONS
async def get_all_drivers():
    """Get all drivers"""
    cursor = drivers_collection.find({})
    drivers = await cursor.to_list(length=100)
    return [serialize_doc(d) for d in drivers]

async def get_driver_by_id(driver_id):
    """Get driver by ID"""
    driver = await drivers_collection.find_one({"id": driver_id})
    return serialize_doc(driver)

async def get_driver_by_email(email):
    """Get driver by email"""
    driver = await drivers_collection.find_one({"email": email})
    return serialize_doc(driver)

async def update_driver(driver_id, update_data):
    """Update driver"""
    await drivers_collection.update_one(
        {"id": driver_id},
        {"$set": update_data}
    )
    return await get_driver_by_id(driver_id)

async def get_drivers_by_city(city):
    """Get drivers in a specific city"""
    cursor = drivers_collection.find({"assigned_city": city})
    drivers = await cursor.to_list(length=50)
    return [serialize_doc(d) for d in drivers]

# WAREHOUSE OPERATIONS
async def get_all_warehouses():
    """Get all warehouses"""
    cursor = warehouses_collection.find({})
    warehouses = await cursor.to_list(length=20)
    return [serialize_doc(w) for w in warehouses]

async def get_warehouse_by_city(city):
    """Get warehouse by city"""
    warehouse = await warehouses_collection.find_one({"city": city})
    return serialize_doc(warehouse)

async def update_warehouse(warehouse_id, update_data):
    """Update warehouse"""
    await warehouses_collection.update_one(
        {"id": warehouse_id},
        {"$set": update_data}
    )

# ADMIN OPERATIONS
async def get_admin_by_username(username):
    """Get admin by username"""
    admin = await admins_collection.find_one({"username": username})
    return serialize_doc(admin)

async def check_admin_permission(username, permission):
    """Check if admin has specific permission"""
    admin = await get_admin_by_username(username)
    if admin and "permissions" in admin:
        return permission in admin["permissions"]
    return False
