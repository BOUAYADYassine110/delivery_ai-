"""
Storage Layer - Switches between in-memory and MongoDB
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix encoding for Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

USE_MONGODB = os.getenv("USE_MONGODB", "false").lower() == "true"

if USE_MONGODB:
    print("[MongoDB] Using MongoDB for data persistence")
    from pymongo import MongoClient
    from bson import ObjectId
    
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "delivery_system")
    
    client = MongoClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    # MongoDB collections
    users_col = db.users
    orders_col = db.orders
    drivers_col = db.drivers
    warehouses_col = db.warehouses
    notifications_col = db.notifications
    
    def clean_mongo_doc(doc):
        """Recursively remove ObjectId from documents"""
        if isinstance(doc, dict):
            return {k: clean_mongo_doc(v) for k, v in doc.items() if k != '_id'}
        elif isinstance(doc, list):
            return [clean_mongo_doc(item) for item in doc]
        elif isinstance(doc, ObjectId):
            return str(doc)
        return doc
    
    # Initialize with default data if empty
    if drivers_col.count_documents({}) == 0:
        print("[MongoDB] Seeding with default data...")
        from seed_data import get_default_drivers, get_default_warehouses, get_default_admin, get_default_test_user
        
        drivers_col.insert_many(get_default_drivers())
        warehouses_col.insert_many(get_default_warehouses())
        users_col.insert_one(get_default_test_user())
        print("[MongoDB] Seeded with 16 drivers, 6 warehouses, 1 test user")
    
    class MongoDBStorage:
        @staticmethod
        def get_users():
            return [clean_mongo_doc(u) for u in users_col.find({})]
        
        @staticmethod
        def add_user(user):
            users_col.insert_one(user)
        
        @staticmethod
        def get_orders():
            return [clean_mongo_doc(o) for o in orders_col.find({})]
        
        @staticmethod
        def add_order(order):
            orders_col.insert_one(order)
        
        @staticmethod
        def update_order(order_id, updates):
            orders_col.update_one({'id': order_id}, {'$set': updates})
        
        @staticmethod
        def get_drivers():
            return [clean_mongo_doc(d) for d in drivers_col.find({})]
        
        @staticmethod
        def update_driver(driver_id, updates):
            drivers_col.update_one({'id': driver_id}, {'$set': updates})
        
        @staticmethod
        def get_warehouses():
            return [clean_mongo_doc(w) for w in warehouses_col.find({})]
        
        @staticmethod
        def update_warehouse(warehouse_id, updates):
            warehouses_col.update_one({'id': warehouse_id}, {'$set': updates})
        
        @staticmethod
        def get_notifications():
            return [clean_mongo_doc(n) for n in notifications_col.find({})]
        
        @staticmethod
        def add_notification(notification):
            notifications_col.insert_one(notification)
        
        @staticmethod
        def update_notification(notification_id, updates):
            notifications_col.update_one({'id': notification_id}, {'$set': updates})
    
    storage = MongoDBStorage()
    
else:
    print("[In-Memory] Using in-memory storage (data will be lost on restart)")
    
    class InMemoryStorage:
        def __init__(self):
            self.users = []
            self.orders = []
            self.drivers = []
            self.warehouses = []
            self.notifications = []
        
        def get_users(self):
            return self.users
        
        def add_user(self, user):
            self.users.append(user)
        
        def get_orders(self):
            return self.orders
        
        def add_order(self, order):
            self.orders.append(order)
        
        def update_order(self, order_id, updates):
            for order in self.orders:
                if order['id'] == order_id:
                    order.update(updates)
                    break
        
        def get_drivers(self):
            return self.drivers
        
        def update_driver(self, driver_id, updates):
            for driver in self.drivers:
                if driver['id'] == driver_id:
                    driver.update(updates)
                    break
        
        def get_warehouses(self):
            return self.warehouses
        
        def update_warehouse(self, warehouse_id, updates):
            for warehouse in self.warehouses:
                if warehouse['id'] == warehouse_id:
                    warehouse.update(updates)
                    break
        
        def get_notifications(self):
            return self.notifications
        
        def add_notification(self, notification):
            self.notifications.append(notification)
        
        def update_notification(self, notification_id, updates):
            for notification in self.notifications:
                if notification['id'] == notification_id:
                    notification.update(updates)
                    break
    
    storage = InMemoryStorage()
