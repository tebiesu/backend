import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import asyncio #创建异步测试环境
from database import create_user, get_user, client, db
from models import User


@pytest.mark.asyncio
async def test_db_connection():
    """Test MongoDB connection"""
    try:
        result = await client.admin.command('ping')
        assert result == {'ok': 1.0}
        print("MongoDB connection successful")
    except Exception as e:
        pytest.fail(f"Connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_db_connection())