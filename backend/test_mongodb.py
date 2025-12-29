#!/usr/bin/env python3
"""
Quick MongoDB Connection Test
Run this to check if MongoDB is working
"""

import sys

def test_mongodb():
    print("=" * 60)
    print("🔍 Testing MongoDB Connection...")
    print("=" * 60)
    
    try:
        from pymongo import MongoClient
        
        # Try to connect
        print("\n1️⃣ Attempting to connect to MongoDB...")
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        
        # Ping the database
        print("2️⃣ Pinging MongoDB server...")
        client.admin.command('ping')
        print("   ✅ MongoDB is responding!")
        
        # Check database
        print("\n3️⃣ Checking delivery_system database...")
        db = client.delivery_system
        collections = db.list_collection_names()
        
        if collections:
            print(f"   ✅ Found {len(collections)} collections:")
            for col in collections:
                count = db[col].count_documents({})
                print(f"      • {col}: {count} documents")
        else:
            print("   ⚠️  No collections found (database is empty)")
            print("   💡 Run 'python init_mongodb.py' to seed the database")
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ SUCCESS: MongoDB is working!")
        print("=" * 60)
        print("\n📍 Next steps:")
        if not collections:
            print("   1. Run: python backend/init_mongodb.py")
            print("   2. Start backend: python backend/main.py")
        else:
            print("   • MongoDB is ready to use")
            print("   • Start backend: python backend/main.py")
        
        return True
        
    except ImportError:
        print("\n❌ ERROR: pymongo not installed")
        print("   Fix: pip install pymongo")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("   1. Is MongoDB installed?")
        print("      • Windows: Download from mongodb.com")
        print("      • Mac: brew install mongodb-community")
        print("      • Linux: sudo apt install mongodb")
        print("\n   2. Is MongoDB running?")
        print("      • Windows: Check Services for 'MongoDB'")
        print("      • Mac/Linux: sudo systemctl status mongod")
        print("\n   3. Start MongoDB:")
        print("      • Windows: net start MongoDB")
        print("      • Mac: brew services start mongodb-community")
        print("      • Linux: sudo systemctl start mongod")
        return False

if __name__ == "__main__":
    success = test_mongodb()
    sys.exit(0 if success else 1)
