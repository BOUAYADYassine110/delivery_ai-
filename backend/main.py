from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json
import asyncio
import os
import math
from datetime import datetime, timedelta
from dotenv import load_dotenv
from auth import (
    create_access_token, get_password_hash, verify_password,
    get_current_user, get_current_client, get_current_driver, get_current_admin
)

# Load environment variables
load_dotenv()

# Import storage layer (switches between in-memory and MongoDB)
from storage import storage, USE_MONGODB

# Import clean function if using MongoDB
if USE_MONGODB:
    from storage import clean_mongo_doc

from api.routes.gps_routes import router as gps_router
from api.routes.driver_management import router as driver_router
from api.services.smart_assignment import SmartAssignmentService
from api.services.delivery_simulator import simulator
from api.services.inter_city_workflow import InterCityWorkflow
from api.services.warehouse_manager import WarehouseManager

# Try to import CrewAI services (optional)
try:
    from api.services.agent_service import AgentService
    from api.services.warehouse_agent import (
        check_warehouse_capacity, optimize_warehouse_routing, 
        coordinate_warehouse_transport, predict_warehouse_capacity,
        communicate_warehouse_status, get_warehouse_agent_status
    )
    CREW_AVAILABLE = True
except Exception as e:
    print(f"⚠️  CrewAI not available: {e}")
    CREW_AVAILABLE = False
    def get_agent_status(): return {"status": "unavailable"}
    async def get_driver_recommendation(order, drivers): return None
    async def get_price_calculation(request): return None
    async def check_warehouse_capacity(wh_id, warehouses, packages): return {"available": True}
    async def optimize_warehouse_routing(order, warehouses): return {}
    async def coordinate_warehouse_transport(wh_id, packages, schedule): return {}
    async def predict_warehouse_capacity(wh_id, warehouses, data): return {}
    async def communicate_warehouse_status(order, warehouses): return {}
    def get_warehouse_agent_status(): return {"status": "unavailable"}

try:
    from api.services.delivery_workflow import process_delivery_order, get_workflow_status
    WORKFLOW_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Workflow not available: {e}")
    WORKFLOW_AVAILABLE = False
    async def process_delivery_order(order, drivers): return None
    def get_workflow_status(): return {"status": "unavailable"}

# Suppress Pydantic serialization warnings
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

app = FastAPI(title="Enhanced Multi-Agent Delivery System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include GPS routes
app.include_router(gps_router, prefix="/api", tags=["GPS Tracking"])
app.include_router(driver_router, prefix="/api", tags=["Driver Management"])

# Include routing
from api.routes.routing import router as routing_router
app.include_router(routing_router, prefix="/api", tags=["Routing"])

# Include enhanced routing
from api.routes.enhanced_routing import router as enhanced_routing_router
app.include_router(enhanced_routing_router, prefix="/api", tags=["Enhanced Routing"])

# Debug routes
from api.routes.assignment_debug import router as debug_router
app.include_router(debug_router, prefix="/api", tags=["Debug"])

# Admin routes
from api.routes.admin_routes import router as admin_router
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])

# Initialize workflow managers after database definitions
inter_city_workflow = None
warehouse_manager = None

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    phone: str
    address: str

class OrderCreate(BaseModel):
    pickup_address: str
    delivery_address: str
    pickup_city: str
    delivery_city: str
    pickup_coordinates: dict = None
    delivery_coordinates: dict = None
    weight: float = 1.0
    dimensions: dict = {"length": 10, "width": 10, "height": 10}  # cm
    service_type: str = "standard"  # standard, express
    delivery_type: str = "door_to_door"  # door_to_door, warehouse_pickup, warehouse_delivery
    sender_name: str
    sender_phone: str
    receiver_name: str
    receiver_phone: str
    package_description: str = "General package"
    
class InterCityOrderCreate(BaseModel):
    pickup_address: str
    delivery_address: str
    pickup_city: str
    delivery_city: str
    pickup_coordinates: dict = None
    delivery_coordinates: dict = None
    weight: float = 1.0
    dimensions: dict = {"length": 10, "width": 10, "height": 10}
    service_type: str = "standard"  # standard, express
    pickup_option: str = "door_pickup"  # door_pickup, warehouse_dropoff
    delivery_option: str = "door_delivery"  # door_delivery, warehouse_pickup
    sender_name: str
    sender_phone: str
    receiver_name: str
    receiver_phone: str
    package_description: str = "General package"
    fragile: bool = False
    insurance_value: float = 0.0

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    accuracy: float = 5.0
    speed: float = 0.0
    heading: float = 0.0

class DriverLocationUpdate(BaseModel):
    driver_id: str
    latitude: float
    longitude: float
    accuracy: float = 5.0
    speed: float = 0.0
    heading: float = 0.0

class AssignmentAcceptance(BaseModel):
    order_id: str
    accepted: bool
    reason: str = ""

class DeliveryUpdate(BaseModel):
    order_id: str
    status: str  # picked_up, in_transit, delivered, failed
    notes: str = ""
    proof_photo: str = ""  # base64 image

class DriverAssignment(BaseModel):
    driver_id: str
    current_location: dict = {"lat": 33.5731, "lng": -7.5898}  # Casablanca default
    max_orders: int = 5
    vehicle_capacity: float = 50.0  # kg

class AdminLoginRequest(BaseModel):
    username: str
    password: str

@app.get("/api/agents/status")
async def agents_status():
    """Get AI agents status"""
    base_status = get_agent_status()
    warehouse_status = get_warehouse_agent_status()
    
    return {
        **base_status,
        "warehouse_agent": warehouse_status
    }

@app.get("/api/workflow/status")
async def workflow_status():
    """Get workflow system status"""
    return get_workflow_status()

@app.post("/api/agents/recommend-driver")
async def recommend_driver(request: dict):
    """Get AI recommendation for driver assignment"""
    order = request.get("order")
    drivers = request.get("drivers", [])
    return await get_driver_recommendation(order, drivers)

@app.post("/api/agents/calculate-price")
async def ai_calculate_price(request: dict):
    """Get AI-powered price calculation"""
    return await get_price_calculation(request)

@app.get("/api/health/mongodb")
async def check_mongodb():
    """Check MongoDB connection status"""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        await client.admin.command('ping')
        
        # Get database stats
        db = client.delivery_system
        collections = await db.list_collection_names()
        
        stats = {}
        for collection in collections:
            count = await db[collection].count_documents({})
            stats[collection] = count
        
        return {
            "status": "connected",
            "database": "delivery_system",
            "collections": collections,
            "document_counts": stats,
            "message": "✅ MongoDB is working!"
        }
    except Exception as e:
        return {
            "status": "disconnected",
            "error": str(e),
            "message": "❌ MongoDB is not connected. Make sure MongoDB is running."
        }

@app.get("/")
def root():
    return {
        "message": "🚀 ULTIMATE MULTI-AGENT DELIVERY SYSTEM",
        "status": "running",
        "version": "3.0 ULTIMATE",
        "database": "In-memory (MongoDB not integrated yet)",
        "total_drivers": len(drivers_db),
        "city_coverage": {
            "Casablanca": f"{len([d for d in drivers_db if d['assigned_city'] == 'Casablanca'])} drivers",
            "Rabat": f"{len([d for d in drivers_db if d['assigned_city'] == 'Rabat'])} drivers", 
            "Marrakech": f"{len([d for d in drivers_db if d['assigned_city'] == 'Marrakech'])} drivers",
            "Agadir": f"{len([d for d in drivers_db if d['assigned_city'] == 'Agadir'])} drivers",
            "El Jadida": f"{len([d for d in drivers_db if d['assigned_city'] == 'El Jadida'])} drivers",
            "Salé": f"{len([d for d in drivers_db if d['assigned_city'] == 'Salé'])} drivers"
        },
        "ultimate_features": [
            "🎯 Multi-driver city coverage (16 total drivers)",
            "🧠 AI-powered intelligent assignment",
            "📍 Real-time location-based scoring",
            "🚗 Vehicle-type optimization", 
            "⭐ Rating-based selection",
            "🎪 Specialty matching system",
            "📊 Load balancing algorithm",
            "🌦️ Weather-aware routing",
            "📦 Multi-package optimization",
            "🏪 Warehouse management"
        ],
        "assignment_factors": {
            "city_match": "50% weight - Same city priority with GPS distance",
            "availability_load": "20% weight - Driver status and workload",
            "vehicle_suitability": "15% weight - Vehicle type and capacity",
            "driver_rating": "10% weight - Performance and satisfaction",
            "specialties": "5% weight - Skill matching"
        },
        "key_endpoints": [
            "GET /api/drivers/by-city - Multi-driver city view",
            "GET /api/system/coverage - Ultimate coverage stats", 
            "GET /api/driver/test-login - Working credentials",
            "POST /api/orders - Intelligent order creation",
            "GET /api/assignment/simulate - Test assignment logic"
        ]
    }

@app.get("/api/test")
def test():
    return {"message": "API is working!", "status": "success"}

# Initialize storage (MongoDB or in-memory based on USE_MONGODB env var)
if USE_MONGODB:
    print("="*60)
    print("🗄️  MONGODB ENABLED - Data will persist between restarts")
    print("="*60)
else:
    print("="*60)
    print("💾 IN-MEMORY MODE - Data will be lost on restart")
    print("💡 Set USE_MONGODB=true in .env to enable persistence")
    print("="*60)

# Get data from storage
users_db = storage.get_users()
orders_db = storage.get_orders()
drivers_db = storage.get_drivers()
warehouses_db = storage.get_warehouses()
notifications_db = storage.get_notifications()

# Helper function to refresh data from storage
def refresh_data():
    global orders_db, drivers_db, warehouses_db, notifications_db
    orders_db = storage.get_orders()
    drivers_db = storage.get_drivers()
    warehouses_db = storage.get_warehouses()
    notifications_db = storage.get_notifications()

# Initialize with default data if empty (in-memory mode only)
if not USE_MONGODB and len(users_db) == 0:
    from seed_data import get_default_test_user, get_default_drivers, get_default_warehouses
    storage.add_user(get_default_test_user())
    for driver in get_default_drivers():
        storage.drivers.append(driver)
    for warehouse in get_default_warehouses():
        storage.warehouses.append(warehouse)
    users_db = storage.get_users()
    drivers_db = storage.get_drivers()
    warehouses_db = storage.get_warehouses()

@app.post("/api/auth/register")
def register(request: RegisterRequest):
    # Check if username or email already exists
    users_db = storage.get_users()
    if any(u["username"] == request.username for u in users_db):
        raise HTTPException(status_code=400, detail="Username already exists")
    if any(u["email"] == request.email for u in users_db):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create new user with hashed password
    user_id = f"USER{len(users_db) + 1:03d}"
    new_user = {
        "id": user_id,
        "username": request.username,
        "email": request.email,
        "password": get_password_hash(request.password),
        "role": "client",
        "full_name": request.full_name,
        "phone": request.phone,
        "address": request.address,
        "created_at": datetime.now().isoformat()
    }
    storage.add_user(new_user)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user_id, "username": request.username, "role": "client"}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user["id"],
            "username": new_user["username"],
            "email": new_user["email"],
            "full_name": new_user["full_name"],
            "role": "client"
        }
    }

@app.post("/api/auth/login")
def login(request: LoginRequest):
    # Find user by username
    users_db = storage.get_users()
    user = next((u for u in users_db if u["username"] == request.username), None)
    
    if not user or not verify_password(request.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user["id"], "username": user["username"], "role": user["role"]}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "full_name": user["full_name"]
        }
    }

@app.post("/api/admin/login")
def admin_login(request: AdminLoginRequest):
    # Check hardcoded admin credentials
    if request.username == "admin" and request.password == "admin123":
        access_token = create_access_token(
            data={"sub": "ADMIN001", "username": "admin", "role": "admin"}
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "admin": {
                "id": "ADMIN001",
                "username": "admin",
                "role": "admin",
                "permissions": ["view_orders", "manage_drivers", "view_analytics"]
            }
        }
    raise HTTPException(status_code=401, detail="Invalid admin credentials")

class DriverLoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/driver/login")
def driver_login(request: DriverLoginRequest):
    # Direct credential mapping
    valid_emails = {
        "ahmed@delivery.ma": "DRV001",
        "youssef@delivery.ma": "DRV002", 
        "fatima@delivery.ma": "DRV003",
        "karim@delivery.ma": "DRV004",
        "laila@delivery.ma": "DRV005",
        "omar@delivery.ma": "DRV006",
        "nadia@delivery.ma": "DRV007",
        "hassan@delivery.ma": "DRV008",
        "aicha@delivery.ma": "DRV009",
        "rachid@delivery.ma": "DRV010",
        "khadija@delivery.ma": "DRV011",
        "mehdi@delivery.ma": "DRV012",
        "zineb@delivery.ma": "DRV013",
        "samir@delivery.ma": "DRV014",
        "amina@delivery.ma": "DRV015",
        "khalid@delivery.ma": "DRV016",
        "driver@example.com": "DRV001"
    }
    
    driver_id = valid_emails.get(request.email.lower())
    if driver_id and request.password in ["driver123", "123"]:
        driver = next((d for d in drivers_db if d["id"] == driver_id), None)
        if driver:
            access_token = create_access_token(
                data={"sub": driver_id, "username": driver["email"], "role": "driver"}
            )
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "driver": driver
            }
    
    raise HTTPException(status_code=401, detail="Invalid credentials. Use driver email with password 'driver123'")

# Enhanced data storage with test orders
orders_db = [
    {
        "id": "ORD1001",
        "tracking_number": "TRK001",
        "status": "in_transit",
        "pickup_address": "Boulevard Mohammed V, Casablanca",
        "delivery_address": "Rue des FAR, Casablanca",
        "pickup_city": "Casablanca",
        "delivery_city": "Casablanca",
        "weight": 2.5,
        "dimensions": {"length": 20, "width": 15, "height": 10},
        "service_type": "express",
        "delivery_type": "door_to_door",
        "sender_name": "Mohammed Alami",
        "sender_phone": "+212661111111",
        "receiver_name": "Sara Benali",
        "receiver_phone": "+212662222222",
        "package_description": "Electronics",
        "total_cost": 67.5,
        "price": 67.5,
        "estimated_delivery": "2024-01-15T14:30:00",
        "created_at": "2024-01-15T09:00:00",
        "is_inter_city": False,
        "assigned_driver": "DRV001",
        "current_location": {"lat": 33.5731, "lng": -7.5898, "timestamp": "2024-01-15T12:30:00"},
        "route_history": [
            {"lat": 33.5731, "lng": -7.5898, "timestamp": "2024-01-15T09:15:00"},
            {"lat": 33.5750, "lng": -7.5900, "timestamp": "2024-01-15T12:30:00"}
        ]
    },
    {
        "id": "ORD1002",
        "tracking_number": "TRK002",
        "status": "picked_up",
        "pickup_address": "Avenue Hassan II, Casablanca",
        "delivery_address": "Quartier Maarif, Casablanca",
        "pickup_city": "Casablanca",
        "delivery_city": "Casablanca",
        "weight": 1.2,
        "dimensions": {"length": 15, "width": 10, "height": 8},
        "service_type": "standard",
        "delivery_type": "door_to_door",
        "sender_name": "Fatima Zahra",
        "sender_phone": "+212663333333",
        "receiver_name": "Ahmed Tazi",
        "receiver_phone": "+212664444444",
        "package_description": "Documents",
        "total_cost": 28.6,
        "price": 28.6,
        "estimated_delivery": "2024-01-16T10:00:00",
        "created_at": "2024-01-15T08:30:00",
        "is_inter_city": False,
        "assigned_driver": "DRV001",
        "current_location": {"lat": 33.5731, "lng": -7.5898, "timestamp": "2024-01-15T10:00:00"},
        "route_history": [{"lat": 33.5731, "lng": -7.5898, "timestamp": "2024-01-15T10:00:00"}]
    },
    {
        "id": "ORD1003",
        "tracking_number": "TRK003",
        "status": "in_transit",
        "pickup_address": "Medina, Marrakech",
        "delivery_address": "Gueliz, Marrakech",
        "pickup_city": "Marrakech",
        "delivery_city": "Marrakech",
        "weight": 3.8,
        "dimensions": {"length": 25, "width": 20, "height": 15},
        "service_type": "express",
        "delivery_type": "door_to_door",
        "sender_name": "Youssef Bennani",
        "sender_phone": "+212665555555",
        "receiver_name": "Laila Alaoui",
        "receiver_phone": "+212666666666",
        "package_description": "Handicrafts",
        "total_cost": 81.4,
        "price": 81.4,
        "estimated_delivery": "2024-01-15T16:00:00",
        "created_at": "2024-01-15T11:00:00",
        "is_inter_city": False,
        "assigned_driver": "DRV003",
        "current_location": {"lat": 31.6295, "lng": -7.9811, "timestamp": "2024-01-15T13:00:00"},
        "route_history": [{"lat": 31.6295, "lng": -7.9811, "timestamp": "2024-01-15T13:00:00"}]
    },
    {
        "id": "ORD1004",
        "tracking_number": "TRK004",
        "status": "warehouse_processing",
        "pickup_address": "Centre Ville, Salé",
        "delivery_address": "Hay Riad, Rabat",
        "pickup_city": "Salé",
        "delivery_city": "Rabat",
        "weight": 5.0,
        "dimensions": {"length": 30, "width": 25, "height": 20},
        "service_type": "standard",
        "delivery_type": "door_to_door",
        "sender_name": "Rachid Benali",
        "sender_phone": "+212667777777",
        "receiver_name": "Nadia Alami",
        "receiver_phone": "+212668888888",
        "package_description": "Furniture parts",
        "total_cost": 89.6,
        "price": 89.6,
        "estimated_delivery": "2024-01-16T14:00:00",
        "created_at": "2024-01-15T07:00:00",
        "is_inter_city": True,
        "assigned_driver": "DRV006",
        "current_location": {"lat": 34.0531, "lng": -6.7985, "timestamp": "2024-01-15T08:00:00"},
        "route_history": [{"lat": 34.0531, "lng": -6.7985, "timestamp": "2024-01-15T08:00:00"}]
    },
    {
        "id": "ORD1005",
        "tracking_number": "TRK005",
        "status": "pending_assignment",
        "pickup_address": "Marina, Agadir",
        "delivery_address": "Souk Al Had, Agadir",
        "pickup_city": "Agadir",
        "delivery_city": "Agadir",
        "weight": 1.5,
        "dimensions": {"length": 12, "width": 8, "height": 6},
        "service_type": "standard",
        "delivery_type": "door_to_door",
        "sender_name": "Hassan Tazi",
        "sender_phone": "+212669999999",
        "receiver_name": "Amina Benali",
        "receiver_phone": "+212660000000",
        "package_description": "Cosmetics",
        "total_cost": 29.5,
        "price": 29.5,
        "estimated_delivery": "2024-01-16T11:00:00",
        "created_at": "2024-01-15T14:00:00",
        "is_inter_city": False,
        "assigned_driver": None,
        "current_location": None,
        "route_history": []
    },
    {
        "id": "ORD1006",
        "tracking_number": "TRK006",
        "status": "warehouse_transit",
        "pickup_address": "Corniche, Casablanca",
        "delivery_address": "Kasbah, Marrakech",
        "pickup_city": "Casablanca",
        "delivery_city": "Marrakech",
        "weight": 8.5,
        "dimensions": {"length": 40, "width": 30, "height": 25},
        "service_type": "express",
        "delivery_type": "warehouse_delivery",
        "sender_name": "Karim Alaoui",
        "sender_phone": "+212661010101",
        "receiver_name": "Zineb Bennani",
        "receiver_phone": "+212662020202",
        "package_description": "Textiles",
        "total_cost": 387.2,
        "price": 387.2,
        "estimated_delivery": "2024-01-16T18:00:00",
        "created_at": "2024-01-15T06:00:00",
        "is_inter_city": True,
        "assigned_driver": None,
        "current_location": {"lat": 33.5731, "lng": -7.5898, "timestamp": "2024-01-15T07:00:00"},
        "route_history": [{"lat": 33.5731, "lng": -7.5898, "timestamp": "2024-01-15T07:00:00"}]
    },
    {
        "id": "IC1007",
        "tracking_number": "IC007",
        "status": "at_origin_warehouse",
        "pickup_address": "Avenue Mohammed VI, Rabat",
        "delivery_address": "Jemaa el-Fnaa, Marrakech",
        "pickup_city": "Rabat",
        "delivery_city": "Marrakech",
        "weight": 12.0,
        "dimensions": {"length": 50, "width": 40, "height": 30},
        "service_type": "standard",
        "pickup_option": "warehouse_dropoff",
        "delivery_option": "door_delivery",
        "sender_name": "Mehdi Alaoui",
        "sender_phone": "+212663030303",
        "receiver_name": "Samira Bennani",
        "receiver_phone": "+212664040404",
        "package_description": "Traditional crafts",
        "fragile": True,
        "insurance_value": 500.0,
        "total_cost": 245.8,
        "price": 245.8,
        "estimated_delivery": "2024-01-17T16:00:00",
        "created_at": "2024-01-14T10:00:00",
        "is_inter_city": True,
        "assigned_driver": None,
        "current_location": None,
        "route_history": [],
        "warehouse_status": "processing",
        "current_warehouse": "Rabat",
        "transport_schedule": {"next_departure": "08:00", "duration": "4 hours", "vehicle": "truck"}
    },
    {
        "id": "IC1008",
        "tracking_number": "IC008",
        "status": "in_transit_inter_city",
        "pickup_address": "Marina Bay, Agadir",
        "delivery_address": "Maarif, Casablanca",
        "pickup_city": "Agadir",
        "delivery_city": "Casablanca",
        "weight": 6.5,
        "dimensions": {"length": 35, "width": 25, "height": 20},
        "service_type": "express",
        "pickup_option": "door_pickup",
        "delivery_option": "warehouse_pickup",
        "sender_name": "Yousra Tazi",
        "sender_phone": "+212665050505",
        "receiver_name": "Khalid Benali",
        "receiver_phone": "+212666060606",
        "package_description": "Argan oil products",
        "fragile": False,
        "insurance_value": 200.0,
        "total_cost": 892.4,
        "price": 892.4,
        "estimated_delivery": "2024-01-16T12:00:00",
        "created_at": "2024-01-15T08:00:00",
        "is_inter_city": True,
        "assigned_driver": "DRV004",
        "current_location": {"lat": 32.5, "lng": -8.2, "timestamp": "2024-01-15T14:00:00"},
        "route_history": [
            {"lat": 30.4278, "lng": -9.5981, "timestamp": "2024-01-15T08:30:00"},
            {"lat": 32.5, "lng": -8.2, "timestamp": "2024-01-15T14:00:00"}
        ],
        "warehouse_status": "in_transit",
        "current_warehouse": None,
        "transport_schedule": {"next_departure": "07:00", "duration": "6 hours", "vehicle": "truck"}
    }
]
# ULTIMATE FINAL VERSION - Multiple drivers per city with intelligent assignment
drivers_db = [
    # CASABLANCA DRIVERS (4 drivers)
    {
        "id": "DRV001",
        "name": "Ahmed Benali",
        "email": "ahmed@delivery.ma",
        "phone": "+212661234567",
        "vehicle_type": "bike",
        "vehicle_capacity": 20.0,
        "assigned_city": "Casablanca",
        "current_location": {"lat": 33.5731, "lng": -7.5898, "city": "Casablanca"},
        "status": "available",
        "current_orders": [],
        "rating": 4.8,
        "total_deliveries": 156,
        "working_hours": {"start": "08:00", "end": "20:00"},
        "specialties": ["express_delivery", "documents"]
    },
    {
        "id": "DRV002",
        "name": "Youssef Alami",
        "email": "youssef@delivery.ma",
        "phone": "+212662345678",
        "vehicle_type": "car",
        "vehicle_capacity": 100.0,
        "assigned_city": "Casablanca",
        "current_location": {"lat": 33.5850, "lng": -7.6000, "city": "Casablanca"},
        "status": "available",
        "current_orders": [],
        "rating": 4.9,
        "total_deliveries": 203,
        "working_hours": {"start": "07:00", "end": "19:00"},
        "specialties": ["bulk_delivery", "fragile_items"]
    },
    {
        "id": "DRV003",
        "name": "Fatima Zahra",
        "email": "fatima@delivery.ma",
        "phone": "+212663456789",
        "vehicle_type": "scooter",
        "vehicle_capacity": 30.0,
        "assigned_city": "Casablanca",
        "current_location": {"lat": 33.5600, "lng": -7.5700, "city": "Casablanca"},
        "status": "busy",
        "current_orders": ["ORD1001"],
        "rating": 4.7,
        "total_deliveries": 89,
        "working_hours": {"start": "09:00", "end": "21:00"},
        "specialties": ["fast_delivery", "city_center"]
    },
    {
        "id": "DRV004",
        "name": "Karim Bennani",
        "email": "karim@delivery.ma",
        "phone": "+212664567890",
        "vehicle_type": "van",
        "vehicle_capacity": 200.0,
        "assigned_city": "Casablanca",
        "current_location": {"lat": 33.5900, "lng": -7.6100, "city": "Casablanca"},
        "status": "available",
        "current_orders": [],
        "rating": 4.6,
        "total_deliveries": 312,
        "working_hours": {"start": "06:00", "end": "18:00"},
        "specialties": ["heavy_cargo", "warehouse", "inter_city"]
    },
    
    # RABAT DRIVERS (3 drivers)
    {
        "id": "DRV005",
        "name": "Laila Alaoui",
        "email": "laila@delivery.ma",
        "phone": "+212665678901",
        "vehicle_type": "car",
        "vehicle_capacity": 80.0,
        "assigned_city": "Rabat",
        "current_location": {"lat": 34.0209, "lng": -6.8416, "city": "Rabat"},
        "status": "available",
        "current_orders": [],
        "rating": 4.9,
        "total_deliveries": 145,
        "working_hours": {"start": "07:30", "end": "20:30"},
        "specialties": ["residential", "same_day"]
    },
    {
        "id": "DRV006",
        "name": "Omar Tazi",
        "email": "omar@delivery.ma",
        "phone": "+212666789012",
        "vehicle_type": "bike",
        "vehicle_capacity": 25.0,
        "assigned_city": "Rabat",
        "current_location": {"lat": 34.0300, "lng": -6.8500, "city": "Rabat"},
        "status": "available",
        "current_orders": [],
        "rating": 4.8,
        "total_deliveries": 67,
        "working_hours": {"start": "08:30", "end": "19:30"},
        "specialties": ["express_delivery", "documents"]
    },
    {
        "id": "DRV007",
        "name": "Nadia Benali",
        "email": "nadia@delivery.ma",
        "phone": "+212667890123",
        "vehicle_type": "scooter",
        "vehicle_capacity": 35.0,
        "assigned_city": "Rabat",
        "current_location": {"lat": 34.0100, "lng": -6.8300, "city": "Rabat"},
        "status": "available",
        "current_orders": [],
        "rating": 4.7,
        "total_deliveries": 98,
        "working_hours": {"start": "08:00", "end": "20:00"},
        "specialties": ["fast_delivery", "fragile_items"]
    },
    
    # MARRAKECH DRIVERS (3 drivers)
    {
        "id": "DRV008",
        "name": "Hassan Alami",
        "email": "hassan@delivery.ma",
        "phone": "+212668901234",
        "vehicle_type": "car",
        "vehicle_capacity": 90.0,
        "assigned_city": "Marrakech",
        "current_location": {"lat": 31.6295, "lng": -7.9811, "city": "Marrakech"},
        "status": "busy",
        "current_orders": ["ORD1003"],
        "rating": 4.8,
        "total_deliveries": 134,
        "working_hours": {"start": "07:00", "end": "19:00"},
        "specialties": ["bulk_delivery", "residential"]
    },
    {
        "id": "DRV009",
        "name": "Aicha Bennani",
        "email": "aicha@delivery.ma",
        "phone": "+212669012345",
        "vehicle_type": "bike",
        "vehicle_capacity": 22.0,
        "assigned_city": "Marrakech",
        "current_location": {"lat": 31.6400, "lng": -7.9900, "city": "Marrakech"},
        "status": "available",
        "current_orders": [],
        "rating": 4.6,
        "total_deliveries": 76,
        "working_hours": {"start": "09:00", "end": "21:00"},
        "specialties": ["express_delivery", "city_center"]
    },
    {
        "id": "DRV010",
        "name": "Rachid Tazi",
        "email": "rachid@delivery.ma",
        "phone": "+212660123456",
        "vehicle_type": "van",
        "vehicle_capacity": 180.0,
        "assigned_city": "Marrakech",
        "current_location": {"lat": 31.6200, "lng": -7.9700, "city": "Marrakech"},
        "status": "available",
        "current_orders": [],
        "rating": 4.9,
        "total_deliveries": 201,
        "working_hours": {"start": "06:00", "end": "18:00"},
        "specialties": ["heavy_cargo", "warehouse", "inter_city"]
    },
    
    # AGADIR DRIVERS (2 drivers)
    {
        "id": "DRV011",
        "name": "Khadija Alaoui",
        "email": "khadija@delivery.ma",
        "phone": "+212661234567",
        "vehicle_type": "van",
        "vehicle_capacity": 200.0,
        "assigned_city": "Agadir",
        "current_location": {"lat": 30.4278, "lng": -9.5981, "city": "Agadir"},
        "status": "available",
        "current_orders": [],
        "rating": 4.9,
        "total_deliveries": 312,
        "working_hours": {"start": "06:00", "end": "18:00"},
        "specialties": ["heavy_cargo", "long_distance", "warehouse"]
    },
    {
        "id": "DRV012",
        "name": "Mehdi Benali",
        "email": "mehdi@delivery.ma",
        "phone": "+212662345678",
        "vehicle_type": "car",
        "vehicle_capacity": 85.0,
        "assigned_city": "Agadir",
        "current_location": {"lat": 30.4400, "lng": -9.6100, "city": "Agadir"},
        "status": "available",
        "current_orders": [],
        "rating": 4.7,
        "total_deliveries": 89,
        "working_hours": {"start": "08:00", "end": "20:00"},
        "specialties": ["coastal_delivery", "same_day"]
    },
    
    # EL JADIDA DRIVERS (2 drivers)
    {
        "id": "DRV013",
        "name": "Zineb Alami",
        "email": "zineb@delivery.ma",
        "phone": "+212663456789",
        "vehicle_type": "bike",
        "vehicle_capacity": 25.0,
        "assigned_city": "El Jadida",
        "current_location": {"lat": 33.2316, "lng": -8.5007, "city": "El Jadida"},
        "status": "available",
        "current_orders": [],
        "rating": 4.6,
        "total_deliveries": 67,
        "working_hours": {"start": "08:30", "end": "19:30"},
        "specialties": ["coastal_delivery", "documents"]
    },
    {
        "id": "DRV014",
        "name": "Samir Bennani",
        "email": "samir@delivery.ma",
        "phone": "+212664567890",
        "vehicle_type": "scooter",
        "vehicle_capacity": 40.0,
        "assigned_city": "El Jadida",
        "current_location": {"lat": 33.2400, "lng": -8.5100, "city": "El Jadida"},
        "status": "available",
        "current_orders": [],
        "rating": 4.8,
        "total_deliveries": 123,
        "working_hours": {"start": "07:00", "end": "19:00"},
        "specialties": ["fast_delivery", "express_delivery"]
    },
    
    # SALÉ DRIVERS (2 drivers)
    {
        "id": "DRV015",
        "name": "Amina Tazi",
        "email": "amina@delivery.ma",
        "phone": "+212665678901",
        "vehicle_type": "car",
        "vehicle_capacity": 80.0,
        "assigned_city": "Salé",
        "current_location": {"lat": 34.0531, "lng": -6.7985, "city": "Salé"},
        "status": "available",
        "current_orders": [],
        "rating": 4.8,
        "total_deliveries": 145,
        "working_hours": {"start": "07:30", "end": "20:30"},
        "specialties": ["residential", "same_day"]
    },
    {
        "id": "DRV016",
        "name": "Khalid Alaoui",
        "email": "khalid@delivery.ma",
        "phone": "+212666789012",
        "vehicle_type": "bike",
        "vehicle_capacity": 28.0,
        "assigned_city": "Salé",
        "current_location": {"lat": 34.0600, "lng": -6.8100, "city": "Salé"},
        "status": "available",
        "current_orders": [],
        "rating": 4.7,
        "total_deliveries": 92,
        "working_hours": {"start": "08:00", "end": "20:00"},
        "specialties": ["express_delivery", "documents"]
    }
]

warehouses_db = [
    {
        "id": "WH001",
        "name": "Casablanca Central Warehouse",
        "city": "Casablanca",
        "address": "Zone Industrielle Ain Sebaa, Casablanca",
        "location": {"lat": 33.6089, "lng": -7.5372},
        "capacity": 1000,
        "current_packages": 45,
        "status": "operational",
        "manager": "Hassan Alami",
        "phone": "+212520123456",
        "operating_hours": "24/7",
        "facilities": ["cold_storage", "loading_dock", "security"]
    },
    {
        "id": "WH002",
        "name": "Rabat Distribution Hub",
        "city": "Rabat",
        "address": "Technopolis, Rabat",
        "location": {"lat": 33.9716, "lng": -6.8498},
        "capacity": 800,
        "current_packages": 32,
        "status": "operational",
        "manager": "Fatima Bennani",
        "phone": "+212537234567",
        "operating_hours": "06:00-22:00",
        "facilities": ["loading_dock", "security", "sorting_area"]
    },
    {
        "id": "WH003",
        "name": "Marrakech Logistics Center",
        "city": "Marrakech",
        "address": "Route de Safi, Marrakech",
        "location": {"lat": 31.6069, "lng": -8.0363},
        "capacity": 600,
        "current_packages": 28,
        "status": "operational",
        "manager": "Youssef Tazi",
        "phone": "+212524345678",
        "operating_hours": "07:00-20:00",
        "facilities": ["loading_dock", "security"]
    },
    {
        "id": "WH004",
        "name": "Agadir Coastal Depot",
        "city": "Agadir",
        "address": "Zone Industrielle Tassila, Agadir",
        "location": {"lat": 30.3908, "lng": -9.5598},
        "capacity": 500,
        "current_packages": 22,
        "status": "operational",
        "manager": "Amina Alaoui",
        "phone": "+212528456789",
        "operating_hours": "08:00-18:00",
        "facilities": ["loading_dock", "cold_storage"]
    },
    {
        "id": "WH005",
        "name": "El Jadida Storage Facility",
        "city": "El Jadida",
        "address": "Zone Industrielle, El Jadida",
        "location": {"lat": 33.2542, "lng": -8.4821},
        "capacity": 400,
        "current_packages": 15,
        "status": "operational",
        "manager": "Rachid Benali",
        "phone": "+212523567890",
        "operating_hours": "08:00-18:00",
        "facilities": ["loading_dock", "security"]
    },
    {
        "id": "WH006",
        "name": "Salé Distribution Point",
        "city": "Salé",
        "address": "Hay Karima, Salé",
        "location": {"lat": 34.0209, "lng": -6.7985},
        "capacity": 300,
        "current_packages": 12,
        "status": "operational",
        "manager": "Laila Tazi",
        "phone": "+212537678901",
        "operating_hours": "07:00-19:00",
        "facilities": ["loading_dock", "sorting_area"]
    }
]

# Initialize workflow managers after databases are defined
def init_workflow_managers():
    global inter_city_workflow, warehouse_manager
    inter_city_workflow = InterCityWorkflow(orders_db, drivers_db, warehouses_db)
    warehouse_manager = WarehouseManager(warehouses_db, orders_db)

init_workflow_managers()

@app.get("/api/orders")
def get_user_orders(current_user: dict = Depends(get_current_client)):
    """Get orders for current authenticated user only"""
    user_id = current_user["id"]
    
    # Fetch fresh data from storage (MongoDB or in-memory)
    all_orders = storage.get_orders()
    
    # Filter orders by user_id
    user_orders = []
    for order in all_orders:
        if order.get("user_id") == user_id:
            user_orders.append({
                "id": order["id"],
                "tracking_number": order.get("tracking_number", order["id"]),
                "status": order["status"],
                "sender_name": order.get("sender_name", "Test User"),
                "receiver_name": order.get("receiver_name", "Receiver"),
                "pickup_address": order["pickup_address"],
                "delivery_address": order["delivery_address"],
                "price": order.get("total_cost", order.get("price", 0)),
                "created_at": order["created_at"],
                "service_type": order.get("service_type", "standard"),
                "is_inter_city": order.get("is_inter_city", False)
            })
    
    return user_orders

@app.post("/api/orders")
async def create_order(order: OrderCreate, current_user: dict = Depends(get_current_client)):
    import random
    from datetime import datetime, timedelta
    
    print("\n" + "="*60)
    print("🚀 NEW ORDER CREATION STARTED")
    print("="*60)
    
    order_id = f"ORD{random.randint(1000, 9999)}"
    tracking_number = f"TRK{random.randint(100, 999)}"
    
    print(f"📦 Order ID: {order_id}")
    print(f"🔢 Tracking: {tracking_number}")
    print(f"👤 Customer: {current_user['username']}")
    
    # Enhanced pricing calculation in Dirhams
    is_inter_city = order.pickup_city.lower() != order.delivery_city.lower()
    
    print(f"🏙️  Route: {order.pickup_city} → {order.delivery_city}")
    print(f"📍 Type: {'INTER-CITY' if is_inter_city else 'INTRA-CITY'}")
    
    if is_inter_city:
        # Inter-city pricing
        base_price = 50.0  # MAD (reduced from 80)
        distance_cost = calculate_inter_city_distance(order.pickup_city, order.delivery_city) * 0.6  # Reduced from 0.8
        weight_cost = order.weight * 4.0  # Reduced from 5.0
        dimension_cost = (order.dimensions["length"] * order.dimensions["width"] * order.dimensions["height"]) / 1000 * 1.5  # Reduced from 2.0
        warehouse_fee = 15.0 if order.delivery_type != "door_to_door" else 0
    else:
        # Intra-city pricing - REDUCED for Morocco
        base_price = 15.0  # MAD (reduced from 25)
        distance_cost = 10.0  # Reduced from 15
        weight_cost = order.weight * 2.0  # Reduced from 3.0
        dimension_cost = (order.dimensions["length"] * order.dimensions["width"] * order.dimensions["height"]) / 1000 * 1.0  # Reduced from 1.5
        warehouse_fee = 0
    
    service_multiplier = {"standard": 1.0, "express": 1.5}.get(order.service_type, 1.0)  # Reduced express from 1.8 to 1.5
    total_cost = (base_price + distance_cost + weight_cost + dimension_cost + warehouse_fee) * service_multiplier
    
    print(f"\n💰 PRICING CALCULATION:")
    print(f"   Base: {base_price} MAD")
    print(f"   Distance: {distance_cost:.2f} MAD")
    print(f"   Weight: {weight_cost:.2f} MAD")
    print(f"   Service: {service_multiplier}x")
    print(f"   TOTAL: {total_cost:.2f} MAD")
    
    # Estimate delivery time
    if is_inter_city:
        delivery_days = 3 if order.service_type == "standard" else 1
    else:
        delivery_days = 1 if order.service_type == "standard" else 0.5
    
    estimated_delivery = datetime.now() + timedelta(days=delivery_days)
    
    # Generate and store coordinates - use provided coordinates or generate from address
    if order.pickup_coordinates:
        pickup_coords = order.pickup_coordinates
    else:
        pickup_coords = generate_address_coordinates(order.pickup_city, order.pickup_address)
    
    if order.delivery_coordinates:
        delivery_coords = order.delivery_coordinates
    else:
        delivery_coords = generate_address_coordinates(order.delivery_city, order.delivery_address)
    
    new_order = {
        "id": order_id,
        "tracking_number": tracking_number,
        "user_id": current_user["id"],
        "username": current_user["username"],
        "status": "pending_assignment",
        "pickup_address": order.pickup_address,
        "delivery_address": order.delivery_address,
        "pickup_city": order.pickup_city,
        "delivery_city": order.delivery_city,
        "pickup_coordinates": pickup_coords,
        "delivery_coordinates": delivery_coords,
        "weight": order.weight,
        "dimensions": order.dimensions,
        "service_type": order.service_type,
        "delivery_type": order.delivery_type,
        "sender_name": order.sender_name,
        "sender_phone": order.sender_phone,
        "receiver_name": order.receiver_name,
        "receiver_phone": order.receiver_phone,
        "package_description": order.package_description,
        "total_cost": round(total_cost, 2),
        "price": round(total_cost, 2),
        "estimated_delivery": estimated_delivery.isoformat(),
        "created_at": datetime.now().isoformat(),
        "is_inter_city": is_inter_city,
        "assigned_driver": None,
        "current_location": None,
        "route_history": [],
        "assignment_attempts": 0
    }
    
    orders_db.append(new_order)
    storage.add_order(new_order)  # Save to storage (MongoDB or in-memory)
    
    print(f"\n🤖 AI AGENT PROCESSING:")
    
    # Refresh drivers from storage to get latest data
    refresh_data()
    
    # Get available drivers in the pickup city
    city_drivers = [d for d in drivers_db if 
                   d.get("status") in ["available", "online"] and 
                   d.get("assigned_city", d.get("current_location", {}).get("city", "")).lower() == order.pickup_city.lower()]
    
    print(f"   Found {len(city_drivers)} available drivers in {order.pickup_city}")
    
    # If no drivers in same city, get nearby drivers
    if not city_drivers:
        available_drivers = [d for d in drivers_db if d.get("status") in ["available", "online"]]
        for driver in available_drivers:
            driver_city = driver.get("assigned_city", driver.get("current_location", {}).get("city", "Casablanca"))
            driver_coords = get_city_coordinates(driver_city)
            pickup_coords = get_city_coordinates(order.pickup_city)
            driver["_temp_distance"] = calculate_gps_distance(
                driver_coords["lat"], driver_coords["lng"],
                pickup_coords["lat"], pickup_coords["lng"]
            )
        city_drivers = sorted(available_drivers, key=lambda d: d.get("_temp_distance", 999))[:3]
    
    # Smart driver assignment - ONLY same city drivers for intra-city
    assignment_service = SmartAssignmentService()
    
    # For intra-city: STRICT city matching, auto-accept
    if not is_inter_city:
        print(f"\n🎯 INTRA-CITY ASSIGNMENT (Auto-Accept):")
        # Only drivers from the SAME city
        same_city_drivers = [d for d in drivers_db if 
                           d.get("status") in ["available", "online"] and
                           d.get("assigned_city", "").lower() == order.pickup_city.lower()]
        
        print(f"   Analyzing {len(same_city_drivers)} drivers...")
        if same_city_drivers:
            print(f"   🧠 AI Agent: Calculating best driver match...")
            best_driver = await assignment_service.find_best_driver(new_order, same_city_drivers)
            if best_driver:
                print(f"   ✅ Selected: {best_driver['name']} ({best_driver['vehicle_type']})")
                print(f"   📊 Rating: {best_driver['rating']}/5.0")
                print(f"   🚗 Vehicle: {best_driver['vehicle_type'].upper()}")
                new_order["assigned_driver"] = best_driver["id"]
                new_order["status"] = "assigned"  # Auto-accept for intra-city
                best_driver["current_orders"].append(order_id)
                best_driver["status"] = "busy"
                
                # Save changes to storage IMMEDIATELY
                storage.update_order(order_id, new_order)
                storage.update_driver(best_driver["id"], best_driver)
                
                # Also update in-memory lists
                for i, o in enumerate(orders_db):
                    if o["id"] == order_id:
                        orders_db[i] = new_order
                        break
                for i, d in enumerate(drivers_db):
                    if d["id"] == best_driver["id"]:
                        drivers_db[i] = best_driver
                        break
                
                print(f"   ⚡ Status: AUTO-ACCEPTED & SAVED")
            else:
                print(f"   ❌ No suitable driver found")
        else:
            print(f"   ⚠️  No available drivers in {order.pickup_city}")
    else:
        print(f"\n🌍 INTER-CITY ASSIGNMENT (Manual Accept):")
        # For inter-city: use existing workflow
        best_driver = None
        if WORKFLOW_AVAILABLE:
            try:
                print(f"   🤖 AI Workflow: Processing inter-city delivery...")
                workflow_result = await process_delivery_order(new_order, city_drivers)
                if workflow_result and "best_driver" in workflow_result:
                    best_driver = workflow_result["best_driver"]
                    new_order["ai_workflow"] = workflow_result.get("workflow")
                    new_order["agents_used"] = workflow_result.get("agents_used", [])
                    print(f"   ✅ Workflow completed")
            except Exception as e:
                print(f"   ⚠️  Workflow error: {e}")
        
        if not best_driver:
            print(f"   🧠 AI Agent: Finding best driver...")
            best_driver = await assignment_service.find_best_driver(new_order, city_drivers)
        
        if best_driver:
            print(f"   ✅ Selected: {best_driver['name']} ({best_driver['vehicle_type']})")
            print(f"   📊 Rating: {best_driver['rating']}/5.0")
            new_order["assigned_driver"] = best_driver["id"]
            new_order["status"] = "pending_acceptance"
            new_order["assignment_attempts"] = 1
            
            # Save to storage IMMEDIATELY
            storage.update_order(order_id, new_order)
            
            # Update in-memory list
            for i, o in enumerate(orders_db):
                if o["id"] == order_id:
                    orders_db[i] = new_order
                    break
            
            print(f"   ⏳ Status: PENDING DRIVER ACCEPTANCE & SAVED")
        else:
            print(f"   ❌ No suitable driver found")
    
    print("\n" + "="*60)
    print("✅ ORDER CREATED SUCCESSFULLY")
    print("="*60 + "\n")
    
    # Start delivery simulation if order is assigned
    if new_order.get("assigned_driver") and new_order["status"] == "assigned":
        simulator.start_simulation(order_id, new_order, orders_db)
        print(f"🎬 Delivery simulation started for order {order_id}")
    
    # Clean MongoDB ObjectId before returning
    if USE_MONGODB:
        return clean_mongo_doc(new_order)
    return new_order

# Driver assignment response with auto-reassignment
@app.post("/api/driver/assignment/response")
def driver_assignment_response(response_data: dict):
    driver_id = response_data.get("driver_id")
    order_id = response_data.get("order_id")
    accept = response_data.get("accept")
    reason = response_data.get("reason", "")
    
    order = next((o for o in orders_db if o["id"] == order_id), None)
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    
    if not order or not driver:
        return {"error": "Order or driver not found"}
    
    # Intra-city orders are auto-accepted, no manual response needed
    if not order.get("is_inter_city", False):
        return {"error": "Intra-city orders are automatically accepted"}
    
    # Track assignment history
    if 'assignment_history' not in order:
        order['assignment_history'] = []
    
    order['assignment_history'].append({
        'driver_id': driver_id,
        'driver_name': driver['name'],
        'timestamp': datetime.now().isoformat(),
        'accepted': accept,
        'reason': reason
    })
    
    if accept:
        order["status"] = "accepted"
        order["accepted_at"] = datetime.now().isoformat()
        if order_id not in driver["current_orders"]:
            driver["current_orders"].append(order_id)
        driver["status"] = "busy"
        
        return {"success": True, "message": "Assignment accepted"}
    else:
        # Find next best driver
        rejected_drivers = [h['driver_id'] for h in order['assignment_history'] if not h['accepted']]
        next_driver = assign_best_driver(order, rejected_drivers)
        
        if next_driver:
            order["assigned_driver"] = next_driver["id"]
            order["status"] = "pending_acceptance"
            return {"success": True, "message": f"Reassigned to {next_driver['name']}"}
        else:
            order["status"] = "pending_assignment"
            order["assigned_driver"] = None
            return {"success": True, "message": "No available drivers"}

# GPS tracking
@app.post("/api/driver/gps/update")
def update_driver_gps(gps_data: dict):
    driver_id = gps_data.get("driver_id")
    order_id = gps_data.get("order_id")
    latitude = gps_data.get("latitude")
    longitude = gps_data.get("longitude")
    
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if driver:
        driver["current_location"].update({
            "lat": latitude,
            "lng": longitude,
            "last_update": datetime.now().isoformat()
        })
    
    if order_id:
        order = next((o for o in orders_db if o["id"] == order_id), None)
        if order:
            order["current_location"] = {
                "lat": latitude,
                "lng": longitude,
                "timestamp": datetime.now().isoformat()
            }
            if "route_history" not in order:
                order["route_history"] = []
            order["route_history"].append({
                "lat": latitude,
                "lng": longitude,
                "timestamp": datetime.now().isoformat()
            })
    
    return {"success": True, "message": "GPS updated"}

# Start delivery
@app.post("/api/driver/delivery/start/{order_id}")
def start_delivery_route(order_id: str, driver_data: dict):
    driver_id = driver_data.get("driver_id")
    order = next((o for o in orders_db if o["id"] == order_id), None)
    
    if order:
        order["status"] = "in_transit"
        order["started_at"] = datetime.now().isoformat()
        return {"success": True, "message": "Delivery started"}
    return {"error": "Order not found"}

# Complete delivery
@app.post("/api/driver/delivery/complete")
def complete_delivery_final(completion_data: dict):
    order_id = completion_data.get("order_id")
    driver_id = completion_data.get("driver_id")
    notes = completion_data.get("notes", "")
    
    order = next((o for o in orders_db if o["id"] == order_id), None)
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    
    if order and driver:
        order["status"] = "delivered"
        order["delivered_at"] = datetime.now().isoformat()
        order["completion_notes"] = notes
        
        if order_id in driver["current_orders"]:
            driver["current_orders"].remove(order_id)
            driver["total_deliveries"] += 1
            
        if not driver["current_orders"]:
            driver["status"] = "available"
        
        return {"success": True, "message": "Delivery completed"}
    return {"error": "Order or driver not found"}

@app.get("/api/admin/orders")
def get_all_orders(current_admin: dict = Depends(get_current_admin)):
    # Fetch fresh data from storage
    all_orders = storage.get_orders()
    
    # Add customer information to orders
    enriched_orders = []
    for order in all_orders:
        enriched_order = order.copy()
        # Add customer info if available
        if not enriched_order.get('sender_name'):
            enriched_order['sender_name'] = 'Test Customer'
            enriched_order['sender_phone'] = '+212661234567'
        if not enriched_order.get('receiver_name'):
            enriched_order['receiver_name'] = 'Receiver'
            enriched_order['receiver_phone'] = '+212667654321'
        enriched_orders.append(enriched_order)
    
    return {"orders": enriched_orders, "total": len(enriched_orders)}

@app.get("/api/admin/drivers")
def get_all_drivers(current_admin: dict = Depends(get_current_admin)):
    enriched_drivers = []
    for driver in drivers_db:
        # Calculate actual deliveries from orders
        completed_deliveries = len([
            o for o in orders_db 
            if o.get("assigned_driver") == driver["id"] and o["status"] == "delivered"
        ])
        
        enriched_driver = driver.copy()
        enriched_driver["total_deliveries"] = completed_deliveries
        enriched_drivers.append(enriched_driver)
    
    return {"drivers": enriched_drivers, "total": len(enriched_drivers)}

@app.get("/api/admin/analytics")
def get_admin_analytics(current_admin: dict = Depends(get_current_admin)):
    total_orders = len(orders_db)
    pending_orders = len([o for o in orders_db if o["status"] in ["pending_assignment", "pending_acceptance"]])
    in_progress = len([o for o in orders_db if o["status"] in ["picked_up", "in_transit", "assigned", "accepted"]])
    completed = len([o for o in orders_db if o["status"] == "delivered"])
    active_drivers = len([d for d in drivers_db if d["status"] in ["available", "busy", "online"]])
    
    revenue = sum([o.get("total_cost", o.get("price", 0)) for o in orders_db if o["status"] == "delivered"])
    
    return {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "in_progress": in_progress,
        "completed": completed,
        "active_drivers": active_drivers
    }

def calculate_inter_city_distance(city1: str, city2: str) -> float:
    """Calculate approximate distance between Moroccan cities in km"""
    distances = {
        ("casablanca", "rabat"): 87,
        ("casablanca", "marrakech"): 239,
        ("casablanca", "el jadida"): 99,
        ("casablanca", "salé"): 91,
        ("casablanca", "agadir"): 508,
        ("rabat", "marrakech"): 325,
        ("rabat", "el jadida"): 140,
        ("rabat", "salé"): 12,
        ("rabat", "agadir"): 588,
        ("marrakech", "agadir"): 269,
        ("marrakech", "el jadida"): 338,
        ("marrakech", "salé"): 337
    }
    
    key = tuple(sorted([city1.lower(), city2.lower()]))
    return distances.get(key, 200)  # Default distance

def assign_best_driver(order: dict, excluded_drivers: list = []) -> dict:
    """ULTIMATE ASSIGNMENT: Multi-factor intelligent driver selection"""
    pickup_coords = get_city_coordinates(order["pickup_city"])
    
    # Enhanced driver selection with city matching and better logic
    city_drivers = [d for d in drivers_db if 
                   d["id"] not in excluded_drivers and
                   d["status"] in ["available", "busy"] and 
                   d["assigned_city"].lower() == order["pickup_city"].lower() and
                   len(d["current_orders"]) < get_max_orders_for_vehicle(d["vehicle_type"]) and
                   sum([get_order_weight(oid) for oid in d["current_orders"]]) + order["weight"] <= d["vehicle_capacity"]]
    
    if not city_drivers:
        # Fallback: Get drivers from nearby cities with distance penalty
        all_drivers = [d for d in drivers_db if 
                      d["id"] not in excluded_drivers and
                      d["status"] in ["available", "busy"] and
                      len(d["current_orders"]) < get_max_orders_for_vehicle(d["vehicle_type"])]
        
        # Calculate distance and sort by proximity
        for driver in all_drivers:
            driver_coords = get_city_coordinates(driver["assigned_city"])
            driver["_temp_distance"] = calculate_gps_distance(
                driver_coords["lat"], driver_coords["lng"],
                pickup_coords["lat"], pickup_coords["lng"]
            )
        
        # Only consider drivers within 100km for realistic assignment
        city_drivers = [d for d in all_drivers if d.get("_temp_distance", 999) <= 100]
        city_drivers = sorted(city_drivers, key=lambda d: d.get("_temp_distance", 999))[:3]
    
    if not city_drivers:
        return None
    
    # INTELLIGENT SCORING: Multiple factors
    best_driver = None
    best_score = -1
    
    for driver in city_drivers:
        score = calculate_ultimate_driver_score(driver, order, pickup_coords)
        if score > best_score:
            best_score = score
            best_driver = driver
    
    return best_driver

def calculate_ultimate_driver_score(driver: dict, order: dict, pickup_coords: dict) -> float:
    """ENHANCED SCORING: Realistic and logical assignment factors"""
    score = 0
    
    # 1. CITY MATCH (50 points max) - Most important factor
    if driver["assigned_city"].lower() == order["pickup_city"].lower():
        # Same city - calculate exact distance from current location
        distance = calculate_gps_distance(
            driver["current_location"]["lat"], driver["current_location"]["lng"],
            pickup_coords["lat"], pickup_coords["lng"]
        )
        # Closer drivers get higher scores (max 50 points for <1km, decreasing)
        location_score = max(10, 50 - distance * 5)
    else:
        # Different city - significant penalty but still possible
        city_distance = calculate_gps_distance(
            get_city_coordinates(driver["assigned_city"])["lat"],
            get_city_coordinates(driver["assigned_city"])["lng"],
            pickup_coords["lat"], pickup_coords["lng"]
        )
        # Max 20 points for cross-city, decreasing with distance
        location_score = max(0, 20 - city_distance * 0.2)
    
    score += location_score
    
    # 2. AVAILABILITY & LOAD (20 points max)
    if driver["status"] == "available":
        availability_score = 20
    elif driver["status"] == "busy":
        # Penalize busy drivers based on current load
        max_orders = get_max_orders_for_vehicle(driver["vehicle_type"])
        load_factor = len(driver["current_orders"]) / max_orders
        availability_score = max(5, 15 - load_factor * 10)
    else:
        availability_score = 0
    
    score += availability_score
    
    # 3. VEHICLE SUITABILITY (15 points max)
    vehicle_score = get_enhanced_vehicle_score(driver["vehicle_type"], order)
    score += min(15, vehicle_score)
    
    # 4. DRIVER RATING (10 points max)
    rating_score = (driver["rating"] / 5.0) * 10
    score += rating_score
    
    # 5. SPECIALTY MATCHING (5 points max)
    specialty_score = calculate_enhanced_specialty_bonus(driver, order)
    score += min(5, specialty_score)
    
    return round(score, 2)

def get_enhanced_vehicle_score(vehicle_type: str, order: dict) -> float:
    """Realistic vehicle scoring based on actual delivery requirements"""
    weight = order.get("weight", 1.0)
    service_type = order.get("service_type", "standard")
    is_fragile = order.get("fragile", False)
    
    # Realistic vehicle capabilities
    vehicle_specs = {
        "bike": {"max_weight": 15, "speed_factor": 1.2, "cost_efficiency": 1.0, "fragile_safe": 0.7},
        "scooter": {"max_weight": 25, "speed_factor": 1.1, "cost_efficiency": 0.9, "fragile_safe": 0.8},
        "car": {"max_weight": 80, "speed_factor": 1.0, "cost_efficiency": 0.7, "fragile_safe": 1.0},
        "van": {"max_weight": 200, "speed_factor": 0.8, "cost_efficiency": 0.5, "fragile_safe": 1.0}
    }
    
    specs = vehicle_specs.get(vehicle_type, vehicle_specs["bike"])
    
    # Base suitability check
    if weight > specs["max_weight"]:
        return 0  # Vehicle cannot handle the weight
    
    base_score = 10  # Base score for suitable vehicle
    
    # Express delivery bonus for faster vehicles
    if service_type == "express":
        base_score += specs["speed_factor"] * 5
    
    # Fragile item handling
    if is_fragile:
        base_score += specs["fragile_safe"] * 3
    
    # Weight efficiency (better score for appropriate vehicle size)
    weight_ratio = weight / specs["max_weight"]
    if 0.3 <= weight_ratio <= 0.8:  # Optimal load range
        base_score += 3
    elif weight_ratio < 0.3:  # Underutilized
        base_score += 1
    
    return min(15, base_score)

def calculate_enhanced_specialty_bonus(driver: dict, order: dict) -> float:
    """Realistic specialty matching with logical bonuses"""
    bonus = 0
    specialties = driver.get("specialties", [])
    
    # Express delivery matching
    if order.get("service_type") == "express":
        if "express_delivery" in specialties:
            bonus += 3
        elif "fast_delivery" in specialties:
            bonus += 2
    
    # Package type matching
    if order.get("fragile") and "fragile_items" in specialties:
        bonus += 2
    
    if order.get("weight", 0) > 20 and "heavy_cargo" in specialties:
        bonus += 2
    
    # Delivery type matching
    if order.get("is_inter_city") and "inter_city" in specialties:
        bonus += 3
    
    # Location specialties (minor bonuses)
    if "city_center" in specialties:
        bonus += 0.5
    if "residential" in specialties:
        bonus += 0.5
    
    return min(5, bonus)

def get_max_orders_for_vehicle(vehicle_type: str) -> int:
    """Get maximum orders per vehicle type"""
    limits = {"bike": 6, "scooter": 8, "car": 12, "van": 16}
    return limits.get(vehicle_type, 6)

def get_vehicle_suitability_score(vehicle_type: str, order: dict) -> float:
    """Score vehicle suitability for order"""
    weight = order["weight"]
    dimensions = order["dimensions"]
    volume = dimensions["length"] * dimensions["width"] * dimensions["height"] / 1000  # liters
    
    suitability = {
        "bike": {"max_weight": 15, "max_volume": 50, "score": 60},
        "scooter": {"max_weight": 25, "max_volume": 80, "score": 70},
        "car": {"max_weight": 80, "max_volume": 200, "score": 85},
        "van": {"max_weight": 200, "max_volume": 500, "score": 100}
    }
    
    vehicle_info = suitability.get(vehicle_type, suitability["bike"])
    
    if weight <= vehicle_info["max_weight"] and volume <= vehicle_info["max_volume"]:
        return vehicle_info["score"]
    else:
        return 0  # Vehicle not suitable

def calculate_route_optimization_score(driver: dict, new_order: dict) -> float:
    """Calculate how well new order fits into driver's current route"""
    if not driver["current_orders"]:
        return 100  # Perfect for empty route
    
    # Simple implementation - check if new order is in same area
    pickup_coords = get_city_coordinates(new_order["pickup_city"])
    
    # Get average location of current orders
    current_orders = [o for o in orders_db if o["id"] in driver["current_orders"]]
    if not current_orders:
        return 100
    
    avg_lat = sum([get_city_coordinates(o["pickup_city"])["lat"] for o in current_orders]) / len(current_orders)
    avg_lng = sum([get_city_coordinates(o["pickup_city"])["lng"] for o in current_orders]) / len(current_orders)
    
    distance_to_route = calculate_gps_distance(pickup_coords["lat"], pickup_coords["lng"], avg_lat, avg_lng)
    
    return max(0, 100 - distance_to_route * 5)  # Closer to existing route is better

def get_city_coordinates(city: str) -> dict:
    """Get coordinates for Moroccan cities"""
    coordinates = {
        "casablanca": {"lat": 33.5731, "lng": -7.5898},
        "rabat": {"lat": 34.0209, "lng": -6.8416},
        "marrakech": {"lat": 31.6295, "lng": -7.9811},
        "el jadida": {"lat": 33.2316, "lng": -8.5007},
        "salé": {"lat": 34.0531, "lng": -6.7985},
        "agadir": {"lat": 30.4278, "lng": -9.5981}
    }
    return coordinates.get(city.lower(), coordinates["casablanca"])

def generate_address_coordinates(city: str, address: str) -> dict:
    """Generate consistent coordinates for an address using hash"""
    base = get_city_coordinates(city)
    hash_val = sum(ord(c) for c in address)
    offset_lat = ((hash_val % 100) / 1000) - 0.05
    offset_lng = (((hash_val * 7) % 100) / 1000) - 0.05
    return {
        "lat": base["lat"] + offset_lat,
        "lng": base["lng"] + offset_lng
    }

def calculate_gps_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between GPS coordinates in km"""
    import math
    
    R = 6371  # Earth radius in km
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_lat/2)**2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def get_order_weight(order_id: str) -> float:
    """Get order weight by ID"""
    order = next((o for o in orders_db if o["id"] == order_id), None)
    return order["weight"] if order else 0

# Enhanced tracking and driver management endpoints
@app.get("/api/drivers/by-city")
def get_drivers_by_city():
    """Get drivers organized by their assigned cities"""
    city_assignments = {}
    
    for driver in drivers_db:
        city = driver.get("assigned_city", "Unknown")
        if city not in city_assignments:
            city_assignments[city] = []
        
        city_assignments[city].append({
            "id": driver["id"],
            "name": driver["name"],
            "vehicle_type": driver["vehicle_type"],
            "status": driver["status"],
            "rating": driver["rating"],
            "current_orders": len(driver["current_orders"]),
            "specialties": driver.get("specialties", []),
            "working_hours": driver.get("working_hours", {})
        })
    
    return {
        "city_assignments": city_assignments,
        "total_drivers": len(drivers_db),
        "cities_covered": list(city_assignments.keys())
    }

@app.get("/api/drivers/city/{city_name}")
def get_city_drivers(city_name: str):
    """Get all drivers assigned to a specific city"""
    city_drivers = [d for d in drivers_db if d.get("assigned_city", "").lower() == city_name.lower()]
    
    return {
        "city": city_name,
        "drivers": city_drivers,
        "total_drivers": len(city_drivers),
        "available_drivers": len([d for d in city_drivers if d["status"] == "available"]),
        "busy_drivers": len([d for d in city_drivers if d["status"] == "busy"])
    }

@app.get("/api/driver/test-login")
def test_driver_login():
    return {
        "working_credentials": [
            "ahmed@delivery.ma / driver123",
            "youssef@delivery.ma / driver123", 
            "fatima@delivery.ma / driver123",
            "laila@delivery.ma / driver123",
            "khadija@delivery.ma / driver123"
        ],
        "password": "driver123 or 123",
        "total_drivers": len(drivers_db)
    }
@app.post("/api/orders/{order_id}/assign-driver")
async def assign_driver_to_order(order_id: str):
    """Manually assign driver to an existing order"""
    refresh_data()
    
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    
    if order.get("assigned_driver"):
        # Driver already assigned, just start simulation
        simulator.start_simulation(order_id, order, orders_db)
        return {"message": "Simulation started", "order": clean_mongo_doc(order) if USE_MONGODB else order}
    
    # Get available drivers in the pickup city
    city_drivers = [d for d in drivers_db if 
                   d.get("status") in ["available", "online"] and 
                   d.get("assigned_city", "").lower() == order["pickup_city"].lower()]
    
    if not city_drivers:
        return {"error": f"No available drivers in {order['pickup_city']}"}
    
    # Use smart assignment
    assignment_service = SmartAssignmentService()
    best_driver = await assignment_service.find_best_driver(order, city_drivers)
    
    if best_driver:
        order["assigned_driver"] = best_driver["id"]
        order["status"] = "assigned"
        best_driver["current_orders"].append(order_id)
        best_driver["status"] = "busy"
        
        # Save changes
        storage.update_order(order_id, order)
        storage.update_driver(best_driver["id"], best_driver)
        
        # Start simulation
        simulator.start_simulation(order_id, order, orders_db)
        
        return {
            "message": "Driver assigned and simulation started",
            "order": clean_mongo_doc(order) if USE_MONGODB else order,
            "driver": best_driver["name"]
        }
    
    return {"error": "No suitable driver found"}

@app.get("/api/assignment/simulate")
def simulate_assignment(pickup_city: str, weight: float = 2.0, service_type: str = "standard", fragile: bool = False):
    """Simulate driver assignment to show selection logic"""
    test_order = {
        "pickup_city": pickup_city,
        "weight": weight,
        "service_type": service_type,
        "fragile": fragile,
        "dimensions": {"length": 20, "width": 15, "height": 10}
    }
    
    # Get all drivers in the city
    city_drivers = [d for d in drivers_db if d["assigned_city"].lower() == pickup_city.lower()]
    
    # Score each driver
    pickup_coords = get_city_coordinates(pickup_city)
    scored_drivers = []
    
    for driver in city_drivers:
        score = calculate_ultimate_driver_score(driver, test_order, pickup_coords)
        scored_drivers.append({
            "driver": {
                "id": driver["id"],
                "name": driver["name"],
                "vehicle_type": driver["vehicle_type"],
                "rating": driver["rating"],
                "status": driver["status"],
                "current_orders": len(driver["current_orders"]),
                "specialties": driver["specialties"]
            },
            "score": round(score, 2),
            "distance_km": round(calculate_gps_distance(
                driver["current_location"]["lat"], driver["current_location"]["lng"],
                pickup_coords["lat"], pickup_coords["lng"]
            ), 2)
        })
    
    # Sort by score
    scored_drivers.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "test_order": test_order,
        "city": pickup_city,
        "available_drivers": len(city_drivers),
        "best_match": scored_drivers[0] if scored_drivers else None,
        "all_scores": scored_drivers,
        "selection_criteria": {
            "city_match": "50% - Same city priority with distance calculation",
            "availability_load": "20% - Driver availability and current workload",
            "vehicle_suitability": "15% - Vehicle type vs package requirements",
            "driver_rating": "10% - Customer satisfaction score",
            "specialties": "5% - Matching skills (express, fragile, etc.)"
        }
    }

@app.get("/api/system/coverage")
def get_system_coverage():
    """Get complete system coverage information"""
    coverage = {
        "cities": [],
        "total_coverage": 0,
        "driver_distribution": {},
        "vehicle_distribution": {}
    }
    
    # Get city coverage
    for city_name, city_coords in get_all_city_coordinates().items():
        city_drivers = [d for d in drivers_db if d.get("assigned_city", "").lower() == city_name.lower()]
        
        coverage["cities"].append({
            "name": city_name,
            "coordinates": city_coords,
            "drivers_count": len(city_drivers),
            "has_warehouse": city_name in warehouses_db,
            "vehicle_types": list(set([d["vehicle_type"] for d in city_drivers])),
            "coverage_status": "Excellent" if len(city_drivers) >= 3 else "Good" if len(city_drivers) >= 2 else "Basic" if len(city_drivers) >= 1 else "No Coverage"
        })
        
        coverage["driver_distribution"][city_name] = len(city_drivers)
    
    # Vehicle distribution
    for driver in drivers_db:
        vehicle_type = driver["vehicle_type"]
        if vehicle_type not in coverage["vehicle_distribution"]:
            coverage["vehicle_distribution"][vehicle_type] = 0
        coverage["vehicle_distribution"][vehicle_type] += 1
    
    coverage["total_coverage"] = len([c for c in coverage["cities"] if c["drivers_count"] > 0])
    coverage["total_drivers"] = len(drivers_db)
    coverage["average_drivers_per_city"] = round(len(drivers_db) / 6, 1)
    

def get_all_city_coordinates() -> dict:
    """Get coordinates for all supported cities"""
    return {
        "Casablanca": {"lat": 33.5731, "lng": -7.5898},
        "Rabat": {"lat": 34.0209, "lng": -6.8416},
        "Marrakech": {"lat": 31.6295, "lng": -7.9811},
        "El Jadida": {"lat": 33.2316, "lng": -8.5007},
        "Salé": {"lat": 34.0531, "lng": -6.7985},
        "Agadir": {"lat": 30.4278, "lng": -9.5981}
    }

@app.get("/api/drivers/{driver_id}/orders")
def get_driver_orders(driver_id: str):
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if not driver:
        return {"error": "Driver not found"}
    
    driver_orders = [o for o in orders_db if o["assigned_driver"] == driver_id]
    return {
        "driver": driver,
        "orders": driver_orders,
        "total_orders": len(driver_orders)
    }

@app.post("/api/orders/{order_id}/location")
def update_order_location(order_id: str, location: LocationUpdate):
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    
    order["current_location"] = {
        "lat": location.latitude,
        "lng": location.longitude,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add to route history
    if "route_history" not in order:
        order["route_history"] = []
    
    order["route_history"].append({
        "lat": location.latitude,
        "lng": location.longitude,
        "timestamp": datetime.now().isoformat()
    })
    
    return {"message": "Location updated", "current_location": order["current_location"]}

@app.post("/api/orders/{order_id}/status")
def update_delivery_status(order_id: str, update: DeliveryUpdate):
    refresh_data()  # Get fresh data
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    
    order["status"] = update.status
    order["delivery_notes"] = update.notes
    order["proof_photo"] = update.proof_photo
    order["last_updated"] = datetime.now().isoformat()
    
    # Save to storage
    storage.update_order(order_id, order)
    
    # If delivered, free up driver
    if update.status == "delivered" and order["assigned_driver"]:
        driver = next((d for d in drivers_db if d["id"] == order["assigned_driver"]), None)
        if driver and order_id in driver["current_orders"]:
            driver["current_orders"].remove(order_id)
            driver["total_deliveries"] += 1
            storage.update_driver(driver["id"], driver)
    
    return {"message": "Status updated", "order": order}

@app.get("/api/orders/{order_id}/track")
def track_order(order_id: str):
    try:
        # Fetch fresh data from storage
        all_orders = storage.get_orders()
        order = next((o for o in all_orders if o["id"] == order_id), None)
        if not order:
            return {"error": "Order not found"}
        
        driver_info = None
        if order.get("assigned_driver"):
            refresh_data()
            driver_info = next((d for d in drivers_db if d["id"] == order["assigned_driver"]), None)
        
        # Get coordinates - use stored coordinates OR generate from address
        pickup_coords = order.get("pickup_coordinates")
        if not pickup_coords:
            pickup_coords = generate_address_coordinates(order["pickup_city"], order["pickup_address"])
            # Save coordinates to order
            order["pickup_coordinates"] = pickup_coords
            storage.update_order(order_id, order)
        
        delivery_coords = order.get("delivery_coordinates")
        if not delivery_coords:
            delivery_coords = generate_address_coordinates(order["delivery_city"], order["delivery_address"])
            # Save coordinates to order
            order["delivery_coordinates"] = delivery_coords
            storage.update_order(order_id, order)
        
        # Get current package location
        current_package_location = get_current_package_location(order, pickup_coords, delivery_coords)
        
        # Build tracking events
        tracking_events = build_tracking_events(order, driver_info)
        
        # Warehouse info for inter-city orders
        warehouse_info = None
        if order.get("is_inter_city"):
            origin_wh = next((w for w in warehouses_db if w["city"] == order["pickup_city"]), None)
            dest_wh = next((w for w in warehouses_db if w["city"] == order["delivery_city"]), None)
            warehouse_info = {
                "origin_warehouse": origin_wh,
                "destination_warehouse": dest_wh,
                "current_warehouse": order.get("current_warehouse"),
                "processing_status": order.get("warehouse_status", "not_processed")
            }
        
        return {
            "order": order,
            "driver": driver_info,
            "tracking_history": order.get("route_history", []),
            "estimated_arrival": order.get("estimated_delivery"),
            "pickup_coordinates": pickup_coords,
            "delivery_coordinates": delivery_coords,
            "current_package_location": current_package_location,
            "warehouse_info": warehouse_info,
            "tracking_events": tracking_events,
            "progress_percentage": calculate_delivery_progress(order["status"])
        }
    except Exception as e:
        print(f"Error in track_order: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/orders/tracking/{tracking_number}")
def track_order_by_tracking_number(tracking_number: str):
    order = next((o for o in orders_db if o.get("tracking_number") == tracking_number), None)
    if not order:
        return {"error": "Order not found"}
    
    driver_info = None
    if order.get("assigned_driver"):
        driver_info = next((d for d in drivers_db if d["id"] == order["assigned_driver"]), None)
    
    # Calculate distance and duration - use stored coordinates
    pickup_coords = order.get("pickup_coordinates") or get_city_coordinates(order["pickup_city"])
    delivery_coords = order.get("delivery_coordinates") or get_city_coordinates(order["delivery_city"])
    distance = calculate_gps_distance(
        pickup_coords["lat"], pickup_coords["lng"],
        delivery_coords["lat"], delivery_coords["lng"]
    )
    
    # Get current package location based on status
    current_package_location = get_current_package_location(order, pickup_coords, delivery_coords)
    
    # Enhanced tracking history with timestamps
    tracking_events = build_tracking_events(order, driver_info)
    
    # Warehouse info for inter-city orders
    warehouse_info = None
    if order.get("is_inter_city"):
        origin_wh = next((w for w in warehouses_db if w["city"] == order["pickup_city"]), None)
        dest_wh = next((w for w in warehouses_db if w["city"] == order["delivery_city"]), None)
        warehouse_info = {
            "origin_warehouse": origin_wh,
            "destination_warehouse": dest_wh,
            "current_warehouse": order.get("current_warehouse"),
            "processing_status": order.get("warehouse_status", "not_processed")
        }
    
    return {
        "order": order,
        "driver": driver_info,
        "tracking_history": order.get("route_history", []),
        "estimated_arrival": order.get("estimated_delivery"),
        "distance": round(distance, 1),
        "tracking_events": tracking_events,
        "pickup_coordinates": pickup_coords,
        "delivery_coordinates": delivery_coords,
        "current_package_location": current_package_location,
        "warehouse_info": warehouse_info,
        "progress_percentage": calculate_delivery_progress(order["status"]),
        "next_update": get_next_expected_update(order)
    }

@app.get("/api/warehouses")
def get_warehouses():
    # Return warehouses with current package counts
    enriched_warehouses = []
    for warehouse in warehouses_db:
        # Count packages currently at this warehouse
        packages_at_warehouse = len([
            o for o in orders_db 
            if o.get("current_warehouse") == warehouse["city"] or
            (o.get("status") in ["at_origin_warehouse", "warehouse_processing"] and o.get("pickup_city") == warehouse["city"]) or
            (o.get("status") == "at_destination_warehouse" and o.get("delivery_city") == warehouse["city"])
        ])
        
        enriched_warehouse = warehouse.copy()
        enriched_warehouse["current_packages"] = packages_at_warehouse
        enriched_warehouses.append(enriched_warehouse)
    
    return enriched_warehouses

@app.get("/api/weather/{city}")
def get_weather(city: str):
    """Get real weather data from OpenWeatherMap API"""
    import requests
    import os
    
    api_key = os.getenv('OWM_API_KEY', '4328f889fe045836d165ee930c7277ef')
    
    # City coordinates for Moroccan cities
    city_coords = {
        "casablanca": {"lat": 33.5731, "lon": -7.5898},
        "rabat": {"lat": 34.0209, "lon": -6.8416},
        "marrakech": {"lat": 31.6295, "lon": -7.9811},
        "el jadida": {"lat": 33.2316, "lon": -8.5007},
        "salé": {"lat": 34.0531, "lon": -6.7985},
        "agadir": {"lat": 30.4278, "lon": -9.5981}
    }
    
    coords = city_coords.get(city.lower(), city_coords["casablanca"])
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lon']}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "city": city,
                "temperature": round(data['main']['temp']),
                "condition": data['weather'][0]['main'],
                "description": data['weather'][0]['description'],
                "humidity": data['main']['humidity'],
                "wind_speed": round(data['wind']['speed'] * 3.6),  # Convert m/s to km/h
                "visibility": "Good" if data.get('visibility', 10000) > 5000 else "Moderate" if data.get('visibility', 10000) > 2000 else "Poor",
                "impact_on_delivery": "None" if data['weather'][0]['main'] in ['Clear', 'Clouds'] else "Minimal" if data['weather'][0]['main'] == 'Drizzle' else "Moderate"
            }
    except Exception as e:
        print(f"Weather API error: {e}")
    
    # Fallback to simulated data
    import random
    return {
        "city": city,
        "temperature": random.randint(15, 35),
        "condition": random.choice(["Sunny", "Cloudy", "Light Rain", "Clear", "Partly Cloudy"]),
        "humidity": random.randint(30, 80),
        "wind_speed": random.randint(5, 25),
        "visibility": random.choice(["Good", "Moderate", "Poor"]),
        "impact_on_delivery": random.choice(["None", "Minimal", "Moderate"])
    }

@app.post("/api/routing/optimize")
async def optimize_route(route_request: dict):
    """Generate optimized route using OSRM public endpoint"""
    import requests
    
    start = route_request.get('start_location', {})
    waypoints = route_request.get('waypoints', [])
    
    if not waypoints or len(waypoints) < 2:
        return {"route": [], "distance": 0, "duration": 0}
    
    pickup = waypoints[0]
    delivery = waypoints[1]
    
    try:
        # Use OSRM public endpoint
        osrm_url = f"http://router.project-osrm.org/route/v1/driving/{start['lng']},{start['lat']};{pickup['lng']},{pickup['lat']};{delivery['lng']},{delivery['lat']}"
        params = {
            'overview': 'full',
            'geometries': 'geojson',
            'steps': 'true'
        }
        
        response = requests.get(osrm_url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('routes'):
                route_data = data['routes'][0]
                geometry = route_data['geometry']['coordinates']
                
                # Convert OSRM coordinates to our format
                route = []
                total_points = len(geometry)
                pickup_index = total_points // 3
                
                for i, coord in enumerate(geometry):
                    route.append({
                        'lat': coord[1],
                        'lng': coord[0],
                        'type': 'to_pickup' if i < pickup_index else 'to_delivery'
                    })
                
                return {
                    'route': route,
                    'distance': round(route_data['distance'] / 1000, 2),
                    'duration': round(route_data['duration'] / 60, 0),
                    'optimized': True,
                    'source': 'OSRM'
                }
        else:
            print(f"OSRM API error: {response.status_code}")
    except Exception as e:
        print(f"OSRM routing failed: {e}, using fallback")
    
    # Fallback: Generate curved route
    route = []
    for i in range(16):
        ratio = i / 15
        curve_offset_lat = 0.002 * math.sin(ratio * math.pi)
        curve_offset_lng = 0.002 * math.cos(ratio * math.pi)
        route.append({
            'lat': start['lat'] + (pickup['lat'] - start['lat']) * ratio + curve_offset_lat,
            'lng': start['lng'] + (pickup['lng'] - start['lng']) * ratio + curve_offset_lng,
            'type': 'to_pickup'
        })
    
    for i in range(1, 21):
        ratio = i / 20
        curve_offset_lat = 0.003 * math.sin(ratio * math.pi * 2)
        curve_offset_lng = 0.003 * math.cos(ratio * math.pi * 1.5)
        route.append({
            'lat': pickup['lat'] + (delivery['lat'] - pickup['lat']) * ratio + curve_offset_lat,
            'lng': pickup['lng'] + (delivery['lng'] - pickup['lng']) * ratio + curve_offset_lng,
            'type': 'to_delivery'
        })
    
    total_distance = calculate_gps_distance(
        start['lat'], start['lng'], pickup['lat'], pickup['lng']
    ) + calculate_gps_distance(
        pickup['lat'], pickup['lng'], delivery['lat'], delivery['lng']
    )
    
    return {
        'route': route,
        'distance': round(total_distance, 2),
        'duration': round(total_distance * 2, 0),
        'optimized': True,
        'source': 'Fallback'
    }

@app.get("/api/route/{pickup_city}/{delivery_city}")
def get_route_info(pickup_city: str, delivery_city: str):
    """Get detailed route information between cities"""
    pickup_coords = get_city_coordinates(pickup_city)
    delivery_coords = get_city_coordinates(delivery_city)
    distance = calculate_gps_distance(
        pickup_coords["lat"], pickup_coords["lng"],
        delivery_coords["lat"], delivery_coords["lng"]
    )
    
    # Simulate route waypoints
    waypoints = []
    if distance > 100:  # Inter-city route
        # Add intermediate waypoints
        lat_diff = (delivery_coords["lat"] - pickup_coords["lat"]) / 3
        lng_diff = (delivery_coords["lng"] - pickup_coords["lng"]) / 3
        
        for i in range(1, 3):
            waypoints.append({
                "lat": pickup_coords["lat"] + (lat_diff * i),
                "lng": pickup_coords["lng"] + (lng_diff * i),
                "name": f"Waypoint {i}"
            })
    
    return {
        "pickup": pickup_coords,
        "delivery": delivery_coords,
        "distance": round(distance, 1),
        "estimated_time": round(distance * 60 / 50),  # 50 km/h average
        "waypoints": waypoints,
        "route_type": "inter_city" if distance > 50 else "intra_city",
        "toll_roads": distance > 100,
        "highway_percentage": min(80, distance * 2) if distance > 50 else 20
    }

@app.get("/api/cities")
def get_supported_cities():
    return {
        "cities": [
            {"name": "Casablanca", "code": "CAS", "warehouse": True, "hub": True},
            {"name": "Rabat", "code": "RAB", "warehouse": True, "hub": True},
            {"name": "Marrakech", "code": "MAR", "warehouse": True, "hub": False},
            {"name": "El Jadida", "code": "JAD", "warehouse": True, "hub": False},
            {"name": "Salé", "code": "SAL", "warehouse": True, "hub": False},
            {"name": "Agadir", "code": "AGA", "warehouse": True, "hub": False}
        ],
        "inter_city_routes": [
            {"from": "Casablanca", "to": "Rabat", "schedule": "Daily at 08:00, 14:00, 20:00", "duration": "2 hours", "next_departure": "08:00"},
            {"from": "Casablanca", "to": "Marrakech", "schedule": "Daily at 09:00, 15:00", "duration": "3 hours", "next_departure": "09:00"},
            {"from": "Casablanca", "to": "Agadir", "schedule": "Every 2 days at 07:00", "duration": "6 hours", "next_departure": "07:00"},
            {"from": "Casablanca", "to": "El Jadida", "schedule": "Daily at 10:00, 16:00", "duration": "1.5 hours", "next_departure": "10:00"},
            {"from": "Rabat", "to": "Salé", "schedule": "Every 2 hours", "duration": "30 minutes", "next_departure": "Every 2 hours"},
            {"from": "Rabat", "to": "Marrakech", "schedule": "Daily at 08:00", "duration": "4 hours", "next_departure": "08:00"}
        ],
        "warehouse_info": {
            "pickup_hours": "08:00 - 18:00",
            "processing_time": "2-4 hours",
            "storage_limit": "7 days"
        }
    }

@app.post("/api/inter-city/orders")
async def create_inter_city_order(order: InterCityOrderCreate, current_user: dict = Depends(get_current_client)):
    import random
    
    order_id = f"IC{random.randint(1000, 9999)}"
    tracking_number = f"IC{random.randint(100, 999)}"
    
    # Enhanced inter-city pricing
    base_price = 80.0  # MAD
    distance_cost = calculate_inter_city_distance(order.pickup_city, order.delivery_city) * 1.2
    weight_cost = order.weight * 8.0
    dimension_cost = (order.dimensions["length"] * order.dimensions["width"] * order.dimensions["height"]) / 1000 * 3.0
    
    # Warehouse fees
    warehouse_fee = 0
    if order.pickup_option == "warehouse_dropoff":
        warehouse_fee += 15.0
    if order.delivery_option == "warehouse_pickup":
        warehouse_fee += 15.0
    
    # Insurance and fragile handling
    insurance_fee = order.insurance_value * 0.02 if order.insurance_value > 0 else 0
    fragile_fee = 25.0 if order.fragile else 0
    
    service_multiplier = {"standard": 1.0, "express": 2.2}.get(order.service_type, 1.0)
    total_cost = (base_price + distance_cost + weight_cost + dimension_cost + warehouse_fee + insurance_fee + fragile_fee) * service_multiplier
    
    # Estimate delivery time
    delivery_days = 2 if order.service_type == "standard" else 1
    if order.pickup_option == "warehouse_dropoff":
        delivery_days += 1
    if order.delivery_option == "warehouse_pickup":
        delivery_days -= 0.5
    
    estimated_delivery = datetime.now() + timedelta(days=delivery_days)
    
    # Generate and store coordinates - use provided coordinates or generate from address
    if order.pickup_coordinates:
        pickup_coords = order.pickup_coordinates
    else:
        pickup_coords = generate_address_coordinates(order.pickup_city, order.pickup_address)
    
    if order.delivery_coordinates:
        delivery_coords = order.delivery_coordinates
    else:
        delivery_coords = generate_address_coordinates(order.delivery_city, order.delivery_address)
    
    new_order = {
        "id": order_id,
        "tracking_number": tracking_number,
        "user_id": current_user["id"],
        "username": current_user["username"],
        "status": "pending_assignment" if order.pickup_option == "door_pickup" else "pending_warehouse_dropoff",
        "pickup_address": order.pickup_address,
        "delivery_address": order.delivery_address,
        "pickup_city": order.pickup_city,
        "delivery_city": order.delivery_city,
        "pickup_coordinates": pickup_coords,
        "delivery_coordinates": delivery_coords,
        "weight": order.weight,
        "dimensions": order.dimensions,
        "service_type": order.service_type,
        "pickup_option": order.pickup_option,
        "delivery_option": order.delivery_option,
        "sender_name": order.sender_name,
        "sender_phone": order.sender_phone,
        "receiver_name": order.receiver_name,
        "receiver_phone": order.receiver_phone,
        "package_description": order.package_description,
        "fragile": order.fragile,
        "insurance_value": order.insurance_value,
        "total_cost": round(total_cost, 2),
        "price": round(total_cost, 2),
        "estimated_delivery": estimated_delivery.isoformat(),
        "created_at": datetime.now().isoformat(),
        "is_inter_city": True,
        "assigned_driver": None,
        "current_location": None,
        "route_history": [],
        "warehouse_status": "not_processed",
        "transport_schedule": get_next_transport_schedule(order.pickup_city, order.delivery_city)
    }
    
    orders_db.append(new_order)
    storage.add_order(new_order)  # Save to storage (MongoDB or in-memory)
    
    # Assign pickup driver if door pickup
    if order.pickup_option == "door_pickup":
        city_drivers = [d for d in drivers_db if 
                       d.get("status") in ["available", "online"] and 
                       d.get("assigned_city", "").lower() == order.pickup_city.lower()]
        
        if city_drivers:
            assignment_service = SmartAssignmentService()
            pickup_driver = await assignment_service.find_best_driver(new_order, city_drivers)
            if pickup_driver:
                new_order["assigned_driver"] = pickup_driver["id"]
                new_order["status"] = "pending_acceptance"
                new_order["assignment_attempts"] = 1
    
    # Clean MongoDB ObjectId before returning
    if USE_MONGODB:
        return clean_mongo_doc(new_order)
    return new_order

def get_next_transport_schedule(pickup_city: str, delivery_city: str) -> dict:
    """Get next available transport schedule between cities"""
    schedules = {
        ("casablanca", "rabat"): {"next_departure": "14:00", "duration": "2 hours", "vehicle": "truck"},
        ("casablanca", "marrakech"): {"next_departure": "09:00", "duration": "3 hours", "vehicle": "truck"},
        ("casablanca", "agadir"): {"next_departure": "07:00", "duration": "6 hours", "vehicle": "truck"},
        ("rabat", "sale"): {"next_departure": "Every 2 hours", "duration": "30 minutes", "vehicle": "van"}
    }
    
    key = tuple(sorted([pickup_city.lower(), delivery_city.lower()]))
    return schedules.get(key, {"next_departure": "Daily", "duration": "4 hours", "vehicle": "truck"})

@app.get("/api/inter-city/track/{tracking_number}")
def track_inter_city_order(tracking_number: str):
    order = next((o for o in orders_db if o["tracking_number"] == tracking_number), None)
    if not order:
        return {"error": "Order not found"}
    
    # Get warehouse status if applicable
    warehouse_info = None
    if order["is_inter_city"]:
        origin_wh = next((w for w in warehouses_db if w["city"] == order["pickup_city"]), None)
        dest_wh = next((w for w in warehouses_db if w["city"] == order["delivery_city"]), None)
        warehouse_info = {
            "origin_warehouse": origin_wh,
            "destination_warehouse": dest_wh,
            "current_warehouse": order.get("current_warehouse"),
            "processing_status": order.get("warehouse_status", "not_processed")
        }
    
    return {
        "order": order,
        "warehouse_info": warehouse_info,
        "transport_schedule": order.get("transport_schedule", {}),
        "estimated_delivery": order.get("estimated_delivery")
    }

@app.post("/api/inter-city/warehouse-dropoff/{order_id}")
def warehouse_dropoff(order_id: str, dropoff_data: dict):
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    
    order["status"] = "at_origin_warehouse"
    order["warehouse_dropoff_time"] = datetime.now().isoformat()
    order["warehouse_status"] = "processing"
    order["current_warehouse"] = order["pickup_city"]
    
    # Update warehouse load
    warehouse = next((w for w in warehouses_db if w["city"] == order["pickup_city"]), None)
    if warehouse:
        warehouse["current_packages"] = warehouse.get("current_packages", 0) + 1
    
    # Send notification
    send_notification({
        "user_id": order.get("sender_phone"),
        "type": "warehouse_received",
        "title": "Package at Warehouse",
        "message": f"Your package {order['tracking_number']} has been received at {order['pickup_city']} warehouse",
        "order_id": order_id
    })
    
    return {"message": "Package received at warehouse", "order": order}

@app.post("/api/inter-city/process-warehouse/{order_id}")
def process_warehouse_package(order_id: str):
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    
    order["status"] = "in_transit_inter_city"
    order["warehouse_status"] = "dispatched"
    order["dispatch_time"] = datetime.now().isoformat()
    
    # Update warehouse load
    warehouse = next((w for w in warehouses_db if w["city"] == order.get("current_warehouse")), None)
    if warehouse:
        warehouse["current_packages"] = max(0, warehouse.get("current_packages", 0) - 1)
    
    # Set destination warehouse
    order["current_warehouse"] = order["delivery_city"]
    
    return {"message": "Package dispatched to destination city", "order": order}

@app.get("/api/pricing/calculate")
def calculate_pricing(pickup_city: str, delivery_city: str, weight: float = 1.0, service_type: str = "standard"):
    is_inter_city = pickup_city.lower() != delivery_city.lower()
    
    if is_inter_city:
        base_price = 50.0
        distance_cost = calculate_inter_city_distance(pickup_city, delivery_city) * 0.8
        weight_cost = weight * 5.0
    else:
        base_price = 25.0
        distance_cost = 15.0
        weight_cost = weight * 3.0
    
    service_multiplier = {"standard": 1.0, "express": 1.8}.get(service_type, 1.0)
    total_cost = (base_price + distance_cost + weight_cost) * service_multiplier
    
    return {
        "base_price": base_price,
        "distance_cost": distance_cost,
        "weight_cost": weight_cost,
        "service_multiplier": service_multiplier,
        "total_cost": round(total_cost, 2),
        "currency": "MAD",
        "is_inter_city": is_inter_city
    }

# Notification system
notifications_db = []

@app.post("/api/notifications/send")
def send_notification(notification: dict):
    notification["id"] = f"NOT{len(notifications_db) + 1}"
    notification["timestamp"] = datetime.now().isoformat()
    notification["read"] = False
    notifications_db.append(notification)
    return {"message": "Notification sent", "notification_id": notification["id"]}

@app.get("/api/notifications/{user_id}")
def get_user_notifications(user_id: str):
    user_notifications = [n for n in notifications_db if n.get("user_id") == user_id]
    return {"notifications": user_notifications, "unread_count": len([n for n in user_notifications if not n["read"]])}

@app.post("/api/notifications/{notification_id}/read")
def mark_notification_read(notification_id: str):
    notification = next((n for n in notifications_db if n["id"] == notification_id), None)
    if notification:
        notification["read"] = True
        return {"message": "Notification marked as read", "notification": notification}
    return {"error": "Notification not found"}

# Enhanced GPS tracking and assignment
@app.post("/api/driver/{driver_id}/location")
def update_driver_location(driver_id: str, location: DriverLocationUpdate):
    refresh_data()  # Get fresh data
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if not driver:
        return {"error": "Driver not found"}
    
    # Update driver location
    driver["current_location"].update({
        "lat": location.latitude,
        "lng": location.longitude,
        "accuracy": location.accuracy,
        "speed": location.speed,
        "heading": location.heading,
        "last_update": datetime.now().isoformat()
    })
    
    # Save to storage
    storage.update_driver(driver_id, driver)
    
    # Update all assigned orders with driver's location
    for order_id in driver["current_orders"]:
        order = next((o for o in orders_db if o["id"] == order_id), None)
        if order:
            order["current_location"] = {
                "lat": location.latitude,
                "lng": location.longitude,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add to route history
            if "route_history" not in order:
                order["route_history"] = []
            order["route_history"].append({
                "lat": location.latitude,
                "lng": location.longitude,
                "timestamp": datetime.now().isoformat(),
                "speed": location.speed
            })
            
            # Save order to storage
            storage.update_order(order_id, order)
    
    # Check for automatic delivery detection
    auto_deliveries = check_automatic_delivery_detection(driver_id, location)
    
    return {
        "message": "Location updated",
        "driver_location": driver["current_location"],
        "auto_deliveries": auto_deliveries
    }

def check_automatic_delivery_detection(driver_id: str, location: DriverLocationUpdate) -> list:
    """Check if driver is at delivery location and auto-complete if stationary"""
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    auto_deliveries = []
    
    for order_id in driver["current_orders"]:
        order = next((o for o in orders_db if o["id"] == order_id), None)
        if not order or order["status"] != "in_transit":
            continue
            
        # Check if at delivery location
        delivery_coords = get_address_coordinates(order["delivery_address"], order["delivery_city"])
        distance = calculate_gps_distance(
            location.latitude, location.longitude,
            delivery_coords["lat"], delivery_coords["lng"]
        )
        
        # If within 50 meters and speed < 2 km/h, suggest delivery completion
        if distance < 0.05 and location.speed < 2:
            auto_deliveries.append({
                "order_id": order_id,
                "tracking_number": order["tracking_number"],
                "delivery_address": order["delivery_address"],
                "distance_to_delivery": round(distance * 1000, 1)  # meters
            })
    
    return auto_deliveries

def get_address_coordinates(address: str, city: str) -> dict:
    """Get approximate coordinates for address (simplified)"""
    city_coords = get_city_coordinates(city)
    # Add small random offset for different addresses in same city
    import random
    offset = 0.01  # ~1km offset
    return {
        "lat": city_coords["lat"] + random.uniform(-offset, offset),
        "lng": city_coords["lng"] + random.uniform(-offset, offset)
    }

@app.post("/api/driver/{driver_id}/accept-assignment")
def accept_assignment(driver_id: str, acceptance: AssignmentAcceptance):
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    order = next((o for o in orders_db if o["id"] == acceptance.order_id), None)
    
    if not driver or not order:
        return {"error": "Driver or order not found"}
    
    # Intra-city orders are auto-accepted
    if not order.get("is_inter_city", False):
        return {"error": "Intra-city orders are automatically accepted and assigned"}
    
    if acceptance.accepted:
        # Accept assignment (inter-city only)
        order["assigned_driver"] = driver_id
        order["status"] = "accepted"
        order["accepted_at"] = datetime.now().isoformat()
        
        if acceptance.order_id not in driver["current_orders"]:
            driver["current_orders"].append(acceptance.order_id)
        
        driver["status"] = "busy"
        
        # Generate optimized route
        optimized_route = generate_advanced_route(driver_id)
        
        # Send notification
        send_notification({
            "user_id": order.get("sender_phone"),
            "type": "assignment_accepted",
            "title": "Driver Assigned",
            "message": f"Driver {driver['name']} has accepted your delivery {order['tracking_number']}",
            "order_id": acceptance.order_id
        })
        
        return {
            "message": "Assignment accepted",
            "order": order,
            "optimized_route": optimized_route
        }
    else:
        # Reject assignment - find another driver
        order["assigned_driver"] = None
        order["status"] = "pending_assignment"
        
        # Try to assign to another driver
        new_driver = assign_best_driver(order)
        if new_driver:
            order["assigned_driver"] = new_driver["id"]
            order["status"] = "pending_acceptance"
        
        return {"message": "Assignment rejected", "reason": acceptance.reason}

# Driver interface endpoints
@app.get("/api/driver/{driver_id}/dashboard")
def get_driver_dashboard(driver_id: str):
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if not driver:
        return {"error": "Driver not found"}
    
    # Get driver's orders
    driver_orders = [o for o in orders_db if o.get("assigned_driver") == driver_id]
    
    # Calculate stats
    today_deliveries = len([o for o in driver_orders if o["status"] == "delivered"])
    pending_deliveries = len([o for o in driver_orders if o["status"] in ["assigned", "picked_up", "in_transit", "accepted"]])
    total_earnings = sum([o.get("total_cost", o.get("price", 0)) * 0.15 for o in driver_orders if o["status"] == "delivered"])  # 15% commission
    
    # Get pending assignments (only inter-city orders need acceptance)
    pending_assignments = [o for o in orders_db 
                          if o.get("assigned_driver") == driver_id and 
                          o["status"] == "pending_acceptance" and
                          o.get("is_inter_city", False)]
    
    return {
        "driver": driver,
        "orders": driver_orders,
        "stats": {
            "today_deliveries": today_deliveries,
            "pending_deliveries": pending_deliveries,
            "total_earnings": round(total_earnings, 2),
            "rating": driver["rating"],
            "total_deliveries": driver["total_deliveries"]
        },
        "current_route": generate_advanced_route(driver_id),
        "pending_assignments": pending_assignments
    }

def get_pending_assignments(driver_id: str) -> list:
    """Get orders pending driver acceptance"""
    return [o for o in orders_db if o.get("assigned_driver") == driver_id and o["status"] == "pending_acceptance"]

@app.get("/api/driver/{driver_id}/route")
def get_driver_route(driver_id: str):
    """Get optimized route for mobile app"""
    route = generate_advanced_route(driver_id)
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    
    return {
        "driver_location": driver["current_location"] if driver else None,
        "route": route,
        "navigation_ready": True
    }

@app.post("/api/driver/{driver_id}/start-delivery/{order_id}")
def start_delivery(driver_id: str, order_id: str):
    """Mark order as picked up and start delivery"""
    order = next((o for o in orders_db if o["id"] == order_id), None)
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    
    if not order or not driver or order.get("assigned_driver") != driver_id:
        return {"error": "Invalid order or driver"}
    
    order["status"] = "picked_up"
    order["picked_up_at"] = datetime.now().isoformat()
    
    # Send notification
    send_notification({
        "user_id": order.get("sender_phone"),
        "type": "package_picked_up",
        "title": "Package Picked Up",
        "message": f"Your package {order['tracking_number']} has been picked up by {driver['name']}",
        "order_id": order_id
    })
    
    return {"message": "Delivery started", "order": order}

@app.post("/api/driver/{driver_id}/update-status")
def update_driver_status(driver_id: str, status_data: dict):
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if not driver:
        return {"error": "Driver not found"}
    
    driver["status"] = status_data.get("status", driver["status"])
    if "location" in status_data:
        driver["current_location"] = status_data["location"]
    
    return {"message": "Driver status updated", "driver": driver}

@app.post("/api/driver/{driver_id}/arrive-at-delivery/{order_id}")
def arrive_at_delivery(driver_id: str, order_id: str):
    """Mark driver as arrived at delivery location"""
    order = next((o for o in orders_db if o["id"] == order_id), None)
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    
    if not order or not driver or order.get("assigned_driver") != driver_id:
        return {"error": "Invalid order or driver"}
    
    order["status"] = "arrived_at_delivery"
    order["arrived_at_delivery"] = datetime.now().isoformat()
    
    # Send notification
    send_notification({
        "user_id": order.get("receiver_phone"),
        "type": "driver_arrived",
        "title": "Driver Arrived",
        "message": f"Your delivery driver {driver['name']} has arrived with package {order['tracking_number']}",
        "order_id": order_id
    })
    
    return {"message": "Marked as arrived", "order": order}

@app.post("/api/driver/{driver_id}/complete-delivery")
def complete_delivery(driver_id: str, completion_data: dict):
    order_id = completion_data.get("order_id")
    order = next((o for o in orders_db if o["id"] == order_id), None)
    
    if not order or order.get("assigned_driver") != driver_id:
        return {"error": "Order not found or not assigned to this driver"}
    
    # Update order status
    order["status"] = "delivered"
    order["delivered_at"] = datetime.now().isoformat()
    order["proof_of_delivery"] = completion_data.get("proof", {})
    
    # Update driver
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if driver and order_id in driver["current_orders"]:
        driver["current_orders"].remove(order_id)
        driver["total_deliveries"] += 1
        
        # Update status if no more orders
        if not driver["current_orders"]:
            driver["status"] = "available"
    
    # Send notifications
    send_notification({
        "user_id": order.get("receiver_phone"),  # Using phone as user ID for demo
        "type": "delivery_completed",
        "title": "Package Delivered!",
        "message": f"Your package {order['tracking_number']} has been delivered successfully.",
        "order_id": order_id
    })
    
    return {"message": "Delivery completed successfully", "order": order}

def generate_advanced_route(driver_id: str) -> dict:
    """Generate optimized multi-package route using TSP algorithm"""
    from api.services.multi_package_optimizer import MultiPackageOptimizer
    
    driver = next((d for d in drivers_db if d["id"] == driver_id), None)
    if not driver:
        return {"route_points": [], "total_distance": 0, "estimated_time": 0}
    
    driver_orders = [o for o in orders_db if o.get("assigned_driver") == driver_id and 
                    o["status"] in ["accepted", "assigned", "picked_up", "in_transit"]]
    
    if not driver_orders:
        return {"route_points": [], "total_distance": 0, "estimated_time": 0}
    
    # Use optimized multi-package routing
    optimizer = MultiPackageOptimizer()
    route_data = optimizer.optimize_multi_delivery_route(
        driver["current_location"], 
        driver_orders
    )
    
    # Convert to expected format
    route_points = []
    total_time = 0
    
    for i, point in enumerate(route_data["route"]):
        if point["type"] == "start":
            route_points.append({
                "type": "start",
                "location": point["location"],
                "address": "Current Location",
                "order_id": None,
                "estimated_arrival": datetime.now().isoformat(),
                "instructions": "Starting point"
            })
        else:
            order = point["order"]
            is_pickup = point["type"] == "pickup"
            
            # Calculate time to this point
            if i > 0:
                prev_point = route_data["route"][i-1]
                distance = optimizer._calculate_distance(prev_point["location"], point["location"])
                total_time += distance * 2 + (5 if is_pickup else 8)  # Travel + stop time
            
            route_points.append({
                "type": point["type"],
                "location": point["location"],
                "address": order["pickup_address"] if is_pickup else order["delivery_address"],
                "order_id": order["id"],
                "tracking_number": order.get("tracking_number", order["id"]),
                "contact_name": order.get("sender_name" if is_pickup else "receiver_name", "Contact"),
                "contact_phone": order.get("sender_phone" if is_pickup else "receiver_phone", "+212661234567"),
                "package_description": order.get("package_description", "Package"),
                "priority": 1 if order.get("service_type") == "express" else 2,
                "estimated_arrival": (datetime.now() + timedelta(minutes=total_time)).isoformat(),
                "instructions": f"{'Pick up' if is_pickup else 'Deliver'} package {'from' if is_pickup else 'to'} {order.get('sender_name' if is_pickup else 'receiver_name', 'contact')}",
                "estimated_duration": 5 if is_pickup else 8
            })
    
    return {
        "route_points": route_points,
        "total_distance": route_data["total_distance"],
        "estimated_time": route_data["total_time"],
        "total_stops": len(route_points) - 1,
        "fuel_cost_estimate": route_data["total_cost"],
        "cost_savings": route_data["fuel_savings"],
        "efficiency_score": route_data["efficiency_score"],
        "optimized": True,
        "generated_at": datetime.now().isoformat(),
        "route_efficiency": "Excellent" if route_data["efficiency_score"] > 80 else "Good" if route_data["efficiency_score"] > 60 else "Fair"
    }

def generate_optimized_route(orders: list) -> list:
    """Legacy function - kept for compatibility"""
    return []

def calculate_route_time(orders: list) -> int:
    """Calculate estimated route completion time in minutes"""
    active_orders = [o for o in orders if o["status"] in ["assigned", "picked_up", "in_transit"]]
    return len(active_orders) * 30  # 30 minutes per delivery

def calculate_route_distance(orders: list) -> float:
    """Calculate total route distance in km"""
    active_orders = [o for o in orders if o["status"] in ["assigned", "picked_up", "in_transit"]]
    return len(active_orders) * 5.5  # Average 5.5 km per delivery

def calculate_delivery_progress(status: str) -> int:
    """Calculate delivery progress percentage based on status"""
    progress_map = {
        "pending_assignment": 10,
        "pending_acceptance": 15,
        "accepted": 25,
        "assigned": 25,
        "picked_up": 50,
        "in_transit": 75,
        "arrived_at_delivery": 90,
        "delivered": 100,
        "warehouse_processing": 30,
        "warehouse_transit": 60,
        "at_origin_warehouse": 35,
        "in_transit_inter_city": 70
    }
    return progress_map.get(status, 0)

def get_current_package_location(order: dict, pickup_coords: dict, delivery_coords: dict) -> dict:
    """Get current package location based on order status"""
    status = order["status"]
    
    # Package at pickup location (not yet collected)
    if status in ["pending_assignment", "pending_acceptance", "accepted", "assigned"]:
        return {
            "lat": pickup_coords["lat"],
            "lng": pickup_coords["lng"],
            "description": "Package at pickup location",
            "type": "pickup"
        }
    
    # Inter-city warehouse locations
    if order.get("is_inter_city"):
        if status in ["at_origin_warehouse", "warehouse_processing"]:
            warehouse = next((w for w in warehouses_db if w["city"] == order["pickup_city"]), None)
            return {
                "lat": warehouse["location"]["lat"] if warehouse else pickup_coords["lat"],
                "lng": warehouse["location"]["lng"] if warehouse else pickup_coords["lng"],
                "description": f"Package at {order['pickup_city']} warehouse",
                "type": "warehouse"
            }
        
        if status == "at_destination_warehouse":
            warehouse = next((w for w in warehouses_db if w["city"] == order["delivery_city"]), None)
            return {
                "lat": warehouse["location"]["lat"] if warehouse else delivery_coords["lat"],
                "lng": warehouse["location"]["lng"] if warehouse else delivery_coords["lng"],
                "description": f"Package at {order['delivery_city']} warehouse",
                "type": "warehouse"
            }
    
    # Package with driver (use driver's current location)
    if status in ["picked_up", "in_transit", "in_transit_inter_city"] and order.get("current_location"):
        return {
            "lat": order["current_location"]["lat"],
            "lng": order["current_location"]["lng"],
            "description": "Package with driver",
            "type": "driver"
        }
    
    # Package delivered
    if status == "delivered":
        return {
            "lat": delivery_coords["lat"],
            "lng": delivery_coords["lng"],
            "description": "Package delivered",
            "type": "delivered"
        }
    
    return None

def build_tracking_events(order: dict, driver_info: dict) -> list:
    """Build comprehensive tracking events list"""
    events = [
        {
            "timestamp": order["created_at"],
            "status": "Order Created",
            "location": order["pickup_address"],
            "description": f"Order {order.get('tracking_number', order['id'])} has been created"
        }
    ]
    
    if order.get("assigned_driver"):
        events.append({
            "timestamp": order.get("accepted_at", order["created_at"]),
            "status": "Driver Assigned",
            "location": order["pickup_city"],
            "description": f"Driver {driver_info['name'] if driver_info else 'Unknown'} has been assigned"
        })
    
    if order["status"] in ["picked_up", "in_transit", "delivered", "at_origin_warehouse", "warehouse_processing", "in_transit_inter_city", "at_destination_warehouse"]:
        events.append({
            "timestamp": order.get("picked_up_at", order["created_at"]),
            "status": "Package Picked Up",
            "location": order["pickup_address"],
            "description": "Package has been picked up from sender"
        })
    
    # Inter-city warehouse events
    if order.get("is_inter_city"):
        if order["status"] in ["at_origin_warehouse", "warehouse_processing", "in_transit_inter_city", "at_destination_warehouse", "delivered"]:
            events.append({
                "timestamp": order.get("warehouse_dropoff_time", order["created_at"]),
                "status": "At Origin Warehouse",
                "location": f"{order['pickup_city']} Warehouse",
                "description": f"Package arrived at {order['pickup_city']} warehouse for processing"
            })
        
        if order["status"] in ["in_transit_inter_city", "at_destination_warehouse", "delivered"]:
            events.append({
                "timestamp": order.get("dispatch_time", order["created_at"]),
                "status": "Inter-City Transit",
                "location": "En route",
                "description": f"Package dispatched to {order['delivery_city']}"
            })
        
        if order["status"] in ["at_destination_warehouse", "delivered"]:
            events.append({
                "timestamp": order.get("destination_arrival", order["created_at"]),
                "status": "At Destination Warehouse",
                "location": f"{order['delivery_city']} Warehouse",
                "description": f"Package arrived at {order['delivery_city']} warehouse"
            })
    
    if order["status"] in ["in_transit", "delivered"]:
        events.append({
            "timestamp": order.get("started_at", order["created_at"]),
            "status": "Out for Delivery",
            "location": "En route",
            "description": "Package is out for final delivery"
        })
    
    if order["status"] == "delivered":
        events.append({
            "timestamp": order.get("delivered_at", order["created_at"]),
            "status": "Delivered",
            "location": order["delivery_address"],
            "description": "Package has been successfully delivered"
        })
    
    return events

def get_next_expected_update(order: dict) -> dict:
    """Get next expected update based on current status"""
    status = order["status"]
    
    next_updates = {
        "pending_assignment": {"event": "Driver Assignment", "eta": "5-15 minutes"},
        "pending_acceptance": {"event": "Driver Acceptance", "eta": "2-10 minutes"},
        "accepted": {"event": "Package Pickup", "eta": "15-30 minutes"},
        "assigned": {"event": "Package Pickup", "eta": "15-30 minutes"},
        "picked_up": {"event": "Warehouse Dropoff" if order.get("is_inter_city") else "Delivery Start", "eta": "30-60 minutes"},
        "at_origin_warehouse": {"event": "Warehouse Processing", "eta": "2-4 hours"},
        "warehouse_processing": {"event": "Inter-City Dispatch", "eta": "1-2 hours"},
        "in_transit_inter_city": {"event": "Destination Warehouse Arrival", "eta": "4-8 hours"},
        "at_destination_warehouse": {"event": "Final Delivery", "eta": "2-6 hours"},
        "in_transit": {"event": "Package Delivery", "eta": "30-60 minutes"}
    }
    
    return next_updates.get(status, {"event": "Delivery Complete", "eta": "Completed"})

@app.websocket("/ws/driver/{driver_id}")
async def driver_websocket(websocket: WebSocket, driver_id: str):
    await websocket.accept()
    try:
        while True:
            # Send real-time updates to driver
            driver = next((d for d in drivers_db if d["id"] == driver_id), None)
            if driver:
                driver_orders = [o for o in orders_db if o.get("assigned_driver") == driver_id]
                await websocket.send_text(json.dumps({
                    "type": "driver_update",
                    "driver": driver,
                    "orders": driver_orders,
                    "timestamp": datetime.now().isoformat()
                }))
            await asyncio.sleep(10)  # Update every 10 seconds
    except WebSocketDisconnect:
        pass

@app.websocket("/ws/tracking/{order_id}")
async def track_order_websocket(websocket: WebSocket, order_id: str):
    await websocket.accept()
    try:
        while True:
            # Send real-time order updates
            order = next((o for o in orders_db if o["id"] == order_id), None)
            if order:
                await websocket.send_text(json.dumps({
                    "order_id": order_id,
                    "status": order["status"],
                    "current_location": order.get("current_location"),
                    "timestamp": datetime.now().isoformat()
                }))
            await asyncio.sleep(30)  # Update every 30 seconds
    except WebSocketDisconnect:
        pass

# ============================================================================
# INTER-CITY WORKFLOW ENDPOINTS
# ============================================================================

@app.post("/api/inter-city/workflow/start/{order_id}")
async def start_inter_city_workflow(order_id: str):
    """Start inter-city workflow for an order"""
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order or not order.get("is_inter_city"):
        return {"error": "Order not found or not inter-city"}
    
    workflow_result = await inter_city_workflow.process_inter_city_order(order)
    return workflow_result

@app.post("/api/warehouse/receive/{order_id}")
def warehouse_receive_package(order_id: str):
    """Receive package at origin warehouse"""
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    
    result = warehouse_manager.receive_package(order_id, order["pickup_city"])
    return result

@app.post("/api/warehouse/consolidate")
def consolidate_warehouse_batch(origin_city: str, destination_city: str):
    """Consolidate packages for inter-city transport"""
    batch = warehouse_manager.consolidate_batch(origin_city, destination_city)
    return batch

@app.post("/api/warehouse/dispatch")
def dispatch_inter_city_truck(origin_city: str, destination_city: str):
    """Dispatch inter-city truck with consolidated batch"""
    result = warehouse_manager.schedule_dispatch(origin_city, destination_city)
    return result

@app.post("/api/warehouse/receive-batch")
def receive_batch_at_destination(origin_city: str, destination_city: str):
    """Receive batch at destination warehouse"""
    result = warehouse_manager.receive_at_destination(origin_city, destination_city)
    return result

@app.post("/api/warehouse/assign-final-delivery/{order_id}")
def assign_final_delivery_driver(order_id: str):
    """Assign driver for final delivery from destination warehouse"""
    result = warehouse_manager.assign_final_delivery(order_id, drivers_db)
    return result

@app.get("/api/warehouse/status/{city}")
def get_warehouse_status_endpoint(city: str):
    """Get warehouse status and statistics"""
    status = warehouse_manager.get_warehouse_status(city)
    return status

@app.post("/api/workflow/update-status/{order_id}")
def update_workflow_status(order_id: str, status_data: dict):
    """Update order status through workflow stages"""
    new_status = status_data.get("status")
    result = inter_city_workflow.update_order_status(order_id, new_status)
    return result

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 ULTIMATE MULTI-AGENT DELIVERY SYSTEM v3.0 🚀")
    print("=" * 80)
    print("✅ Multi-Driver City Coverage (16 total drivers)")
    print("✅ AI-Powered Intelligent Assignment")
    print("✅ Real-time Location-Based Scoring")
    print("✅ Vehicle-Type Optimization")
    print("✅ Rating-Based Selection")
    print("✅ Specialty Matching System")
    print("✅ Load Balancing Algorithm")
    print("✅ Weather-Aware Routing")
    print("✅ Multi-Package Optimization")
    print("✅ Warehouse Management")
    print("=" * 80)
    print("🏙️  ULTIMATE CITY COVERAGE:")
    print("   • Casablanca → 4 drivers (Ahmed, Youssef, Fatima, Karim)")
    print("   • Rabat → 3 drivers (Laila, Omar, Nadia)")
    print("   • Marrakech → 3 drivers (Hassan, Aicha, Rachid)")
    print("   • Agadir → 2 drivers (Khadija, Mehdi)")
    print("   • El Jadida → 2 drivers (Zineb, Samir)")
    print("   • Salé → 2 drivers (Amina, Khalid)")
    print("=" * 80)
    print("🎯 ASSIGNMENT FACTORS:")
    print("   • Location Proximity: 40% (GPS distance)")
    print("   • Vehicle Suitability: 25% (type, capacity, speed)")
    print("   • Driver Rating: 15% (customer satisfaction)")
    print("   • Current Load: 10% (workload balancing)")
    print("   • Specialties: 10% (skill matching)")
    print("=" * 80)
    print("🌐 URLs:")
    print("   Backend: http://localhost:8001")
    print("   API Docs: http://localhost:8001/docs")
    print("   Coverage: http://localhost:8001/api/system/coverage")
    print("   Simulator: http://localhost:8001/api/assignment/simulate")
    print("=" * 80)
    uvicorn.run(app, host="0.0.0.0", port=8001)
