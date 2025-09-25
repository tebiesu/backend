# -*- coding: utf-8 -*-
# FastAPI应用入口文件
# 本文件定义了后端服务的核心应用实例、路由和依赖
# 包含认证、聊天、限流等功能路由，支持SSE流式响应

from fastapi import FastAPI, Depends  # FastAPI核心导入，用于构建API和依赖注入
from fastapi_limiter import FastAPILimiter  # 限流中间件导入，用于控制请求频率
from fastapi_limiter.depends import RateLimiter  # 限流依赖导入，用于路由装饰

import asyncio  # 异步IO库，用于处理并发操作
from motor.motor_asyncio import AsyncIOMotorClient  # MongoDB异步客户端，用于数据库连接

from auth import register_user, authenticate_user, get_current_user, RegisterRequest, LoginRequest  # 认证模块导入，包含用户注册/登录函数和模型
from config import settings  # 配置模块导入，包含环境变量如数据库URI、API密钥

from chat import start_chat_stream  # 聊天模块导入，用于流式响应生成
from models import ChatRequest  # 聊天请求模型导入，用于验证POST数据

# 创建FastAPI应用实例，标题AI Chat Backend，版本1.0.0
app = FastAPI(title="AI Chat Backend", version="1.0.0")

# CORS中间件：支持前端跨域请求（MVP允许localhost:5173）
from fastapi.middleware.cors import CORSMiddleware  # 跨域中间件导入
app.add_middleware(  # 添加CORS
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # React Vite端口
    allow_credentials=True,
    allow_methods=["*"],  # 所有方法
    allow_headers=["*"],  # 所有header
)

# 限流设置（MVP使用内存模式）
# 注释：对于生产环境，安装redis并使用Redis客户端初始化；MVP默认内存限流
# FastAPILimiter.init() 可选初始化为内存

# 根路由：健康检查，返回后端准备状态
@app.get("/")  # GET / 返回应用状态
def root():  # 简单函数，返回消息字典
    return {"message": "后端服务就绪"}  # 返回中文消息，表示服务正常

# 注册路由：用户注册端点
print("Adding register route")
@app.post("/auth/register", response_model=dict)  # POST /auth/register，响应模型为字典
async def register(reg_req: RegisterRequest):  # 异步函数，参数为注册请求模型
    return await register_user(reg_req)  # 调用认证模块注册函数，返回用户ID和邮件

# 登录路由：用户登录端点
@app.post("/auth/login", response_model=dict)  # POST /auth/login，响应模型为字典
async def login(login_req: LoginRequest):  # 异步函数，参数为登录请求模型
    return await authenticate_user(login_req)  # 调用认证模块登录函数，返回访问token

# 受保护路由：获取当前用户
@app.get("/protected")  # GET /protected，需要认证
async def protected_route(current_user: dict = Depends(get_current_user)):  # 依赖当前用户
# 返回当前用户邮件
    return {"user": current_user["email"]}  # 返回用户邮箱字典

# 限流示例路由：测试限流功能
@app.get("/rlimited", dependencies=[Depends(RateLimiter(times=10, seconds=60))])  # GET /rlimited，限流10次/60秒
async def rl():  # 简单函数
    return {"message": "限流测试成功"}  # 返回限流消息

# 聊天启动路由：发起聊天会话，支持SSE流式响应
# 路径：POST /chat/start
# 依赖：用户认证和限流
# 响应：StreamingResponse，为Gemini流式生成内容
@app.post("/chat/start")
async def chat_start(
    chat_req: ChatRequest,  # 聊天请求模型，包含消息内容
    current_user: dict = Depends(get_current_user),  # 依赖当前用户认证
    limiter = Depends(RateLimiter(times=10, seconds=60))  # 依赖限流，10次/60秒
):
    return await start_chat_stream(current_user, chat_req)  # 调用聊天模块，返回流式响应