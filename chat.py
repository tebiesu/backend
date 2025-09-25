# -*- coding: utf-8 -*-
# 聊天核心模块：Gemini AI集成和流式响应生成
# 本文件处理聊天逻辑，包括内容审核、会话历史管理、Gemini生成、SSE流式输出
# 支持多轮对话，消息保存到MongoDB，安全设置防止有害内容

import google.generativeai as genai  # Gemini SDK导入，用于AI生成内容
from fastapi import Depends  # FastAPI依赖导入
from fastapi.responses import StreamingResponse  # 流式响应类，用于SSE
from typing import AsyncGenerator  # 类型提示，异步生成器用于yield chunk

from database import save_message, get_messages, create_session, get_session  # DB函数：消息/会话CRUD
from models import Message, ChatRequest  # 模型：消息结构和请求验证
from moderation import check_content_safety  # 审核模块：Gemini安全检测
from auth import get_current_user  # 认证依赖：获取当前用户

from config import settings  # 配置：Gemini API key

# 配置Gemini API密钥，支持.env中GEMINI_API_KEY
genai.configure(api_key=settings.gemini_api_key)  # 全局配置API key

# 聊天流式异步生成器：生成SSE事件流
# 参数：user_id字符串, chat_req聊天请求模型
# 返回：异步生成器，yield SSE格式字符串 (data: {"delta": "text"}\n\n)
# 流程：审核 -> 会话管理 -> 历史构建 -> 保存用户消息 -> Gemini生成 -> 保存/ yield助手消息
# 异常：安全审核失败yield错误，Gemini错误fallback
async def chat_stream(user_id: str, chat_req: ChatRequest) -> AsyncGenerator[str, None]:  # 异步生成器
    # 第一步：内容审核，使用Gemini Moderation过滤有害消息
    safety = await check_content_safety(chat_req.message)  # 异步审核用户消息
    if safety["flagged"]:  # 如果被标记有害
        yield f"data: {{\"error\": \"内容因安全原因被阻止\"}}\\n\\n"  # yield SSE错误事件
        return  # 终止生成

    # 第二步：获取或创建会话（MVP简化用default_session，后续可user_id生成session_id）
    session_id = "default_session"  # MVP简化session ID，后续增强为user_id+时间戳
    session = await get_session(session_id)  # 异步查询会话
    if not session:  # 如果不存在
        await create_session({"session_id": session_id, "user_id": user_id})  # 创建新会话

    # 第三步：构建对话历史，从DB获取session消息
    history = await get_messages(session_id)  # 异步获取消息列表
    content_parts = []  # 构建内容部分列表，[]是JSON数组
    for msg in history:  # 先添加历史
        if "role" in msg and "content" in msg:
            # Gemini内容部分格式：{"role": "user/assistant", "parts": [{"text": "内容"}]}
            # 支持多段内容，MVP简化为单段
            content_parts.append({"role": msg["role"], "parts": [{"text": msg["content"]}]})
    content_parts.append({"role": "user", "parts": [{"text": chat_req.message}]})  # 最后添加用户消息

    # 第四步：保存用户消息到DB，支持多轮上下文
    await save_message(session_id, {"role": "user", "content": chat_req.message})  # 异步保存

    # 第五步：Gemini流式生成
    model = genai.GenerativeModel('gemini-2.5-flash')  # 创建Gemini模型实例 (2.5-flash快且支持流式)
    response = model.generate_content(  # 生成内容调用
        content_parts,  # 输入对话历史
        stream=True,  # 启用流式，chunk-by-chunk
        safety_settings=[  # 安全设置，阻塞中等/高风险内容
            {"category": genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
            # 可添加更多类别如HARM_CATEGORY_HATE_SPEECH, HARM_CATEGORY_DANGEROUS_CONTENT等
        ]
    )
    assistant_parts = []  # 累积助手响应部分
    try:
        async for chunk in response:  # 异步迭代每个chunk
            if chunk.text:  # 如果chunk有文本
                assistant_parts.append(chunk.text)  # 追加到列表
                yield f"data: {{\"delta\": \"{chunk.text}\"}}\n\n"  # yield SSE delta事件：增量文本，前端拼接显示
    except Exception as e:  # 捕获生成异常
        yield f"data: {{\"error\": \"生成内容时出错: {str(e)}\"}}\n\n"  # yield SSE错误事件
        return  # 终止生成
    # 第六步：统一保存完整助手响应到DB
    if assistant_parts:  # 如果有回应
        full_response = ''.join(assistant_parts)  # 合并文本
        await save_message(session_id, {"role": "assistant", "content": full_response})  # 异步保存完整消息
    yield f"data: {{\"done\": true}}\n\n"  # 流结束事件，通知前端完成

# 聊天启动路由依赖函数：返回StreamingResponse
# 参数：current_user认证用户, chat_req请求 (FastAPI自动解析body)
# 返回：SSE StreamingResponse，支持浏览器EventSource
# headers：no-cache/keep-alive for持久连接
# 用途：/chat/start POST端点调用此函数
def start_chat_stream(  # 同步函数，返回流响应
    current_user: dict = Depends(get_current_user),  # 依赖当前用户验证
    chat_req: ChatRequest = Depends()  # 依赖聊天请求 (body解析)
):
    return StreamingResponse(  # 创建流式响应
        chat_stream(current_user["email"], chat_req),  # 传入user email作为user_id
        media_type="text/event-stream",  # MIME类型为SSE
        headers={  # HTTP headers
            "Cache-Control": "no-cache",  # 无缓存
            "Connection": "keep-alive",  # 保持连接
            "Access-Control-Allow-Origin": "*",  # CORS允许所有源 (MVP)
        }
    )