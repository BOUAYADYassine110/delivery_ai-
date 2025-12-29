from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.models.courier import Courier
from core.auth import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/api/driver", tags=["driver-auth"])

class DriverLogin(BaseModel):
    email: str
    password: str

class DriverRegister(BaseModel):
    email: str
    password: str
    name: str
    phone: str
    vehicle_type: str
    vehicle_number: str

@router.post("/register")
async def register_driver(driver: DriverRegister):
    existing = await Courier.find_one(Courier.email == driver.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_driver = Courier(
        email=driver.email,
        password_hash=get_password_hash(driver.password),
        name=driver.name,
        phone=driver.phone,
        vehicle_type=driver.vehicle_type,
        vehicle_number=driver.vehicle_number,
        status="available"
    )
    
    await new_driver.insert()
    
    token = create_access_token({"sub": driver.email, "role": "driver", "driver_id": str(new_driver.id)})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "driver": {
            "id": str(new_driver.id),
            "email": new_driver.email,
            "name": new_driver.name,
            "vehicle_type": new_driver.vehicle_type
        }
    }

@router.post("/login")
async def login_driver(credentials: DriverLogin):
    driver = await Courier.find_one(Courier.email == credentials.email)
    
    if not driver or not verify_password(credentials.password, driver.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": driver.email, "role": "driver", "driver_id": str(driver.id)})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "driver": {
            "id": str(driver.id),
            "email": driver.email,
            "name": driver.name,
            "vehicle_type": driver.vehicle_type,
            "status": driver.status
        }
    }

@router.get("/me")
async def get_driver_profile():
    driver_id = "placeholder"
    driver = await Courier.get(driver_id)
    
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    return {
        "id": str(driver.id),
        "email": driver.email,
        "name": driver.name,
        "phone": driver.phone,
        "vehicle_type": driver.vehicle_type,
        "vehicle_number": driver.vehicle_number,
        "status": driver.status,
        "rating": driver.rating,
        "total_deliveries": driver.total_deliveries
    }
