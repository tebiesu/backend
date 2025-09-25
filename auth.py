# -*- coding: utf-8 -*-
# 认证模块：用户认证和JWT token管理
# 本文件处理用户注册、登录、密码哈希、JWT token生成/验证
# 使用PyJWT for token, bcrypt for密码哈希，支持FastAPI依赖

import bcrypt  # 密码哈希库，用于安全存储明文密码
from fastapi import Depends, HTTPException, status  # FastAPI导入，用于依赖、异常、状态码
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # HTTP Bearer token安全方案
from jose import JWTError, jwt  # JWT库，用于token编码/解码和错误处理
from datetime import datetime, timedelta  # 日期时间处理，用于token过期时间
from typing import Optional  # 类型提示，用于可选参数

from database import get_db, create_user, get_user, db  # 数据库函数导入，用于用户CRUD
from models import User, LoginRequest, RegisterRequest  # 模型导入，用于请求验证
from config import settings  # 配置导入，用于JWT secret

# HTTP Bearer安全方案实例，用于提取Authorization header token
security = HTTPBearer()  # FastAPI Bearer方案

# JWT算法常量：HS256 (HMAC with SHA256)
ALGORITHM = "HS256"  # JWT签名算法

# 访问token过期时间：30分钟
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # token有效期常量

# 密码哈希函数：生成bcrypt哈希，用于安全存储密码
# 参数：明文密码字符串
# 返回：base64编码的哈希字符串
def hash_password(password: str) -> str:  # 同步函数，生成盐并哈希
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()  # 编码为bytes, gensalt生成盐

# 密码验证函数：比对明文和哈希密码
# 参数：明文密码, 哈希密码
# 返回：布尔值, true如果匹配
# 用途：登录时验证用户密码
def verify_password(plain_password: str, hashed_password: str) -> bool:  # 同步验证
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())  # 字节比对

# 创建访问token函数：生成JWT token
# 参数：data字典 (sub: email等), expires_delta可选过期时间
# 返回：编码JWT字符串
# 标准：RFC 7519, exp claim for过期
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):  # 同步token生成
    to_encode = data.copy()  # 复制数据避免修改原dict
    if expires_delta:  # 如果提供自定义过期时间
        expire = datetime.utcnow() + expires_delta  # 当前UTC + delta
    else:  # 默认30分钟
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})  # 添加过期claim
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGORITHM)  # 使用secret编码
    return encoded_jwt  # 返回token字符串

# 用户注册异步函数：验证并创建用户
# 参数：reg_req注册请求模型
# 返回：字典含user_id和email, 插入ID为str
# 异常：400如果email已存在
async def register_user(reg_req: RegisterRequest):  # 异步注册
    existing = await get_user(reg_req.email)  # 查询现有用户
    if existing:  # 如果存在
        raise HTTPException(status_code=400, detail="邮箱已注册")  # 400异常, 中文详情
    hashed_pwd = hash_password(reg_req.password)  # 哈希密码
    user_data = {"email": reg_req.email, "password_hash": hashed_pwd}  # 用户数据字典
    result = await create_user(user_data)  # 异步插入DB
    return {"user_id": str(result.inserted_id), "email": reg_req.email}  # 返回ID和邮件

# 用户认证异步函数：登录验证并生成token
# 参数：login_req登录请求模型
# 返回：字典含access_token和token_type
# 异常：401如果凭证无效
async def authenticate_user(login_req: LoginRequest):  # 异步登录
    user = await get_user(login_req.email)  # 获取用户
    if not user or not verify_password(login_req.password, user["password_hash"]):  # 验证用户/密码
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")  # 401异常
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # 30分钟过期
    access_token = create_access_token(  # 生成token
        data={"sub": user["email"]}, expires_delta=access_token_expires  # sub为email, exp delta
    )
    return {"access_token": access_token, "token_type": "bearer"}  # 返回token和类型

# 获取当前用户异步函数：JWT验证依赖
# 参数：credentials Bearer token
# 返回：用户字典
# 异常：401如果token无效/过期/用户不存在
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):  # 依赖Bearer
    credentials_exception = HTTPException(  # 401异常模板
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="凭证验证失败",
        headers={"WWW-Authenticate": "Bearer"},  # WWW-Authenticate header for client
    )
    try:  # 尝试解码token
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[ALGORITHM])  # 解码JWT
        email: str = payload.get("sub")  # 获取sub claim (email)
        if email is None:  # 如果无sub
            raise credentials_exception  # 抛异常
    except JWTError:  # JWT解码错误 (过期/签名无效)
        raise credentials_exception  # 抛异常
    user = await get_user(email)  # 查询用户
    if user is None:  # 如果用户不存在
        raise credentials_exception  # 抛异常
    return user  # 返回用户dict