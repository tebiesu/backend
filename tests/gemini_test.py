
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import google.generativeai as genai
from config import settings

async def test_gemini():
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    # 用 to_thread 包装同步 generate_content 为协程
    response = await asyncio.to_thread(model.generate_content, "Hello")
    print("Gemini OK:", response.text[:50] if hasattr(response, 'text') else "No text generated")

asyncio.run(test_gemini())