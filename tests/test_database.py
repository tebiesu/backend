import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import asyncio #创建异步测试环境
from database import create_user, get_user, client, db
from models import User

@pytest.mark.asyncio
async def test_create_get_user():
    user_data = {"email": "test@example.com", "password_hash": "123456"}
    result = await create_user(user_data)
    assert result.acknowledged
    user = await get_user("test@example.com")
    assert user["email"] == "test@example.com"
    # Cleanup
    await db.users.delete_one({"email": "test@example.com"})

if __name__ == "__main__":
    try:
        result = asyncio.run(test_create_get_user())
        print("Test completed successfully!")
    except Exception as e:
        print(f"Test failed with error: {e}")