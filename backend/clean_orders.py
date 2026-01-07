"""
Clean all orders from MongoDB
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "delivery_system")

client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]

print("Cleaning orders from MongoDB...")
result = db.orders.delete_many({})
print(f"Deleted {result.deleted_count} orders")

print("\nCleaning notifications...")
result = db.notifications.delete_many({})
print(f"Deleted {result.deleted_count} notifications")

print("\nDatabase cleaned! Orders and notifications removed.")
print("Drivers, warehouses, and users are preserved.")
