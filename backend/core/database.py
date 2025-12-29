from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from .config import settings

client = None
database = None

async def connect_db():
    global client, database
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.DATABASE_NAME]
    
    from api.models.order import Order
    from api.models.user import User
    from api.models.courier import Courier
    from api.models.analytics import DeliveryAnalytics, APICallLog, DeliveryEvent
    from api.models.tracking import TrackingEvent
    
    await init_beanie(database=database, document_models=[
        Order, User, Courier, DeliveryAnalytics, APICallLog, DeliveryEvent, TrackingEvent
    ])

async def close_db():
    global client
    if client:
        client.close()
