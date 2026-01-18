"""Clear all orders from MongoDB and reset driver statuses"""
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "delivery_system")

client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]

# Clear all orders
result = db.orders.delete_many({})
print(f"Deleted {result.deleted_count} orders")

# Clear all notifications
result = db.notifications.delete_many({})
print(f"Deleted {result.deleted_count} notifications")

# Reset all drivers to available with empty orders
result = db.drivers.update_many(
    {},
    {"$set": {"current_orders": [], "status": "available"}}
)
print(f"Reset {result.modified_count} drivers to available")

print("\nDatabase cleared successfully!")
