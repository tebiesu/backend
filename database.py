# -*- coding: utf-8 -*-
# 数据库模块：MongoDB异步操作封装
# 本文件定义了MongoDB客户端、数据库操作函数，如用户/会话/消息的CRUD
# 使用Motor库支持异步操作，适合FastAPI高并发场景
import motor.motor_asyncio  # MongoDB异步驱动库，提供AsyncIOMotorClient支持

from contextlib import asynccontextmanager  # 异步上下文管理器，用于依赖注入数据库连接
from pydantic_settings import BaseSettings  # Pydantic配置基类，支持从.env加载环境变量

from config import settings  # 导入全局配置，包含db_uri等

# 配置类：数据库设置，支持环境变量覆盖，默认本地MongoDB
class Settings(BaseSettings):
    db_uri: str = "mongodb://localhost:27017/ai_chat"  # 数据库URI，默认本地27017端口，db名为ai_chat

settings = Settings()  # 创建配置实例，自动加载.env中的DB_URI等变量

# 创建MongoDB异步客户端实例，用于所有数据库操作
# 连接到配置的URI，支持自动重连和连接池优化
client = motor.motor_asyncio.AsyncIOMotorClient(settings.db_uri)  # AsyncIOMotorClient异步MongoDB客户端

db = client.ai_chat  # 获取指定数据库实例，ai_chat为MVP数据库名

# 数据库依赖函数：用于FastAPI依赖注入，提供db实例
# 用途：路由函数中通过Depends(get_db)获取db，支持事务或连接管理
async def get_db():
    yield db  # 异步生成db实例，支持FastAPI的依赖生命周期

# 创建用户函数：异步插入用户到users集合
# 参数：user_data字典，包含email和password_hash
# 返回：InsertOneResult，包含inserted_id用于用户ID
async def create_user(user_data):  # 异步函数，插入用户数据
    users = db.users  # 获取users集合实例
    return await users.insert_one(user_data)  # 异步插入，返回结果
    return await users.insert_one(user_data)

async def get_user(email):
    users = db.users
    return await users.find_one({"email": email})

async def create_session(session_data):
    sessions = db.sessions
    return await sessions.insert_one(session_data)

async def get_session(session_id):
    sessions = db.sessions
    return await sessions.find_one({"_id": session_id})

async def save_message(session_id, message):
    messages = db.messages
    return await messages.insert_one({"session_id": session_id, "message": message})

async def get_messages(session_id):
    messages = db.messages
    return await messages.find({"session_id": session_id}).sort("timestamp", 1).to_list(None)