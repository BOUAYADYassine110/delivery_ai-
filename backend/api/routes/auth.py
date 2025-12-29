from fastapi import APIRouter, Depends, HTTPException
from api.models.user import User, UserRole
from api.schemas.user import UserCreate, UserLogin, Token, UserResponse
from core.auth import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register")
async def register(user: UserCreate):
    try:
        if await User.find_one(User.email == user.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        if await User.find_one(User.username == user.username):
            raise HTTPException(status_code=400, detail="Username already taken")
        
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=get_password_hash(user.password),
            full_name=user.full_name,
            role=UserRole.client
        )
        await db_user.insert()
        
        access_token = create_access_token(data={"sub": str(db_user.id)})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(db_user.id),
                "email": db_user.email,
                "username": db_user.username,
                "full_name": db_user.full_name,
                "role": db_user.role.value,
                "is_active": db_user.is_active,
                "created_at": db_user.created_at
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
async def login(user: UserLogin):
    db_user = await User.find_one(User.username == user.username)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(db_user.id),
            "email": db_user.email,
            "username": db_user.username,
            "full_name": db_user.full_name,
            "role": db_user.role.value,
            "is_active": db_user.is_active,
            "created_at": db_user.created_at
        }
    }

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }
