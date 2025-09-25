import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import asyncio
from chat import chat_stream
from models import ChatRequest
from config import settings

@pytest.mark.asyncio
@pytest.mark.skipif(not settings.gemini_api_key, reason="Gemini API 未设置，跳过集成测试")
async def test_chat_stream_real():
    """真实集成测试：使用实际的 Gemini API 和 MongoDB 测试 chat_stream 函数的完整流程"""
    req = ChatRequest(message="hello")  # 创建测试聊天请求，消息内容为简单问候
    session_id = "default_session"  # 定义测试会话 ID，用于隔离测试数据，避免影响其他会话
    
    # 预清理：删除之前的测试会话和消息，确保测试环境干净，避免数据冲突
    from database import db
    await db.sessions.delete_one({"session_id": session_id})  # 删除会话文档
    await db.messages.delete_many({"session_id": session_id})  # 删除所有相关消息文档
    
    # 定义内部异步函数，用于收集生成器的所有 yield 值（chunks），因为 chat_stream 是异步生成器
    async def collect_generator():
        chunks = []  # 初始化空列表，用于存储所有 SSE 事件字符串
        async for chunk in chat_stream("test_user", req):  # 异步迭代 chat_stream 生成器，收集每个 yield 的 chunk
            chunks.append(chunk)  # 追加每个 chunk 到列表
        return chunks  # 返回收集的 chunks 列表
    
    # 执行收集函数，获取所有 chunks
    chunks = await collect_generator()
    
    # 断言检查：验证生成器是否产生了至少一个事件（流式响应成功）
    assert len(chunks) > 0, "没有生成事件"  # 如果 chunks 为空，测试失败，提示无生成事件
    
    # 断言检查：验证 chunks 中至少有一个包含 "delta" 字段（SSE 标准格式，用于增量文本）
    assert any("delta" in chunk for chunk in chunks), "No delta in chunks"  # 检查是否有 delta 事件
    
    # 检查数据库保存：验证用户消息和助手消息是否正确保存到 MongoDB
    messages = await db.messages.find({"session_id": session_id}).to_list(None)  # 异步查询测试会话的所有消息
    assert len(messages) >= 2, "没有保存用户和助手消息"  # 至少 2 条消息：用户输入 + 助手响应
    
    # 查找用户消息，验证内容匹配输入
    user_msg = next((m for m in messages if m["role"] == "user"), None)  # 迭代 messages，找 role="user" 的文档
    assert user_msg and user_msg["content"] == "你好", "用户消息未保存"  # 验证用户消息存在且内容正确

    # 后清理：测试结束后删除测试数据，保持数据库干净
    await db.sessions.delete_one({"session_id": session_id})  # 删除会话
    await db.messages.delete_many({"session_id": session_id})  # 删除消息