import pytest
import asyncio

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import register_user, authenticate_user
from models import RegisterRequest, LoginRequest

@pytest.mark.asyncio
async def test_register():
    """测试注册功能：验证用户创建和ID返回"""
    reg_req = RegisterRequest(email="test@test.com", password="testpass")
    result = await register_user(reg_req)  # 异步注册
    assert "user_id" in result  # 验证返回user_id
    # Cleanup: 测试后删除用户，避免DB污染
    from database import db
    await db.users.delete_one({"email": "test@test.com"})  # 异步删除

@pytest.mark.asyncio
async def test_login_after_register():
    """测试登录功能：注册后验证token生成"""
    reg_req = RegisterRequest(email="login@test.com", password="loginpass")
    await register_user(reg_req)  # 先注册
    login_req = LoginRequest(email="login@test.com", password="loginpass")
    result = await authenticate_user(login_req)  # 异步登录
    assert "access_token" in result  # 验证token返回
    # Cleanup: 删除测试用户
    #from database import db
    #await db.users.delete_one({"email": "login@test.com"})