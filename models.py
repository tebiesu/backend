# -*- coding: utf-8 -*-
# Pydantic模型模块：数据验证和序列化模型定义
# 本文件定义了API请求/响应和数据库模型，使用Pydantic BaseModel确保类型安全和验证
# 支持JSON序列化，EmailStr验证邮件格式，datetime自动处理时间，Field约束长度/最小
from pydantic import BaseModel, EmailStr, Field  # BaseModel基类用于模型定义，EmailStr验证邮件，Field for约束
from typing import List, Optional  # Optional支持可选字段，List用于数组类型
from datetime import datetime  # 日期时间模块，用于消息时间戳

# 用户模型：表示用户实体，用于注册/登录/数据库存储
class User(BaseModel):  # Pydantic模型，用户数据结构
    id: Optional[str] = None  # 可选ID，由MongoDB ObjectId生成
    email: EmailStr  # 必需邮件地址，Pydantic验证格式如user@example.com
    password_hash: str  # 必需密码哈希，使用bcrypt加密存储

# 消息模型：聊天消息实体，支持用户/助手角色
class Message(BaseModel):  # Pydantic模型，单个消息结构
    id: Optional[str] = None  # 可选ID，MongoDB生成
    role: str  # 角色字段，"user"表示用户消息，"assistant"表示AI回复
    content: str  # 消息内容，字符串类型
    timestamp: datetime = datetime.utcnow()  # 时间戳，默认UTC当前时间

# 会话模型：聊天会话实体，包含消息历史
class Session(BaseModel):  # Pydantic模型，会话结构
    id: Optional[str] = None  # 可选会话ID
    user_id: Optional[str] = None  # 可选用户ID，匿名会话为None
    messages: List[Message] = []  # 消息列表，默认空，支持多轮对话历史

# 登录请求模型：API登录POST body验证
class LoginRequest(BaseModel):  # Pydantic模型，登录输入
    email: EmailStr  # 必需邮件
    password: str = Field(..., min_length=8, description="密码至少8位")  # 密码约束：最小8位

# 注册请求模型：API注册POST body验证
class RegisterRequest(BaseModel):  # Pydantic模型，注册输入
    email: EmailStr  # 必需邮件
    password: str = Field(..., min_length=8, description="密码至少8位")  # 密码约束：最小8位

# 聊天请求模型：API聊天POST body验证
class ChatRequest(BaseModel):  # Pydantic模型，聊天输入
    message: str = Field(..., max_length=2000, description="消息长度限制2000字符")  # 消息约束：最大2000字，防滥用