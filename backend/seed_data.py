"""
Seed data for MongoDB initialization
"""
from datetime import datetime
from auth import get_password_hash

def get_default_drivers():
    """Get default 16 drivers"""
    return [
        # CASABLANCA (4 drivers)
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
            "status": "available",
            "current_orders": [],
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
        # RABAT (3 drivers)
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
        # MARRAKECH (3 drivers)
        {
            "id": "DRV008",
            "name": "Hassan Alami",
            "email": "hassan@delivery.ma",
            "phone": "+212668901234",
            "vehicle_type": "car",
            "vehicle_capacity": 90.0,
            "assigned_city": "Marrakech",
            "current_location": {"lat": 31.6295, "lng": -7.9811, "city": "Marrakech"},
            "status": "available",
            "current_orders": [],
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
        # AGADIR (2 drivers)
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
        # EL JADIDA (2 drivers)
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
        # SALÉ (2 drivers)
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

def get_default_warehouses():
    """Get default 6 warehouses"""
    return [
        {
            "id": "WH001",
            "name": "Casablanca Central Warehouse",
            "city": "Casablanca",
            "address": "Zone Industrielle Ain Sebaa, Casablanca",
            "location": {"lat": 33.6089, "lng": -7.5372},
            "capacity": 1000,
            "current_packages": 0,
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
            "current_packages": 0,
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
            "current_packages": 0,
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
            "current_packages": 0,
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
            "current_packages": 0,
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
            "current_packages": 0,
            "status": "operational",
            "manager": "Laila Tazi",
            "phone": "+212537678901",
            "operating_hours": "07:00-19:00",
            "facilities": ["loading_dock", "sorting_area"]
        }
    ]

def get_default_admin():
    """Get default admin user"""
    return {
        "id": "ADMIN001",
        "username": "admin",
        "password": get_password_hash("admin123"),
        "role": "admin",
        "permissions": ["view_orders", "manage_drivers", "view_analytics", "manage_users"],
        "created_at": datetime.now()
    }

def get_default_test_user():
    """Get default test user"""
    return {
        "id": "USER001",
        "username": "testuser",
        "email": "test@example.com",
        "password": get_password_hash("test123"),
        "role": "client",
        "full_name": "Test User",
        "phone": "+212661234567",
        "address": "Casablanca, Morocco",
        "created_at": datetime.now()
    }
