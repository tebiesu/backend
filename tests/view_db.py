
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

async def view_db():
    client = AsyncIOMotorClient(settings.db_uri)
    db = client.ai_chat
    users = await db.users.find().to_list(None)
    print("Users collection:")
    for user in users:
        print(user)
    print(f"Total users: {len(users)}")

asyncio.run(view_db())