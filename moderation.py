import google.generativeai as genai # Gemini API SDK，用于内容安全检测
from config import settings # 导入配置，包含Gemini API Key

genai.configure(api_key=settings.gemini_api_key)

# 使用Gemini模型进行内容安全检测，返回是否违规及违规类别
# content参数是要检测的文本内容，类型为字符串
async def check_content_safety(content: str):   # 异步安全审核函数：检测用户输入有害内容
    """Gemini内容审核：使用safety_settings阻塞有害内容，返回flagged状态和类别
    参数：content字符串，用户消息
    返回：字典 {"flagged": bool, "categories": []}
    用途：聊天前调用，防止骚扰/仇恨/有害内容通过
    模型：gemini-2.5-flash快且支持安全过滤"""
    model = genai.GenerativeModel('gemini-2.5-flash')  # 创建审核模型实例 (2.5-flash适合审核)
    safety_settings = [  # 安全阈值列表，BLOCK_MEDIUM_AND_ABOVE阻塞中等及以上风险
        {  # 骚扰类别
            "category": genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            "threshold": genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        },
        # 添加更多类别如HARM_CATEGORY_HATE_SPEECH, HARM_CATEGORY_DANGEROUS_CONTENT等
        # 用途：自定义风险阈值，MVP聚焦骚扰，扩展时添加
    ]
    response = model.generate_content(  # 调用Gemini生成，实际用于评估prompt_feedback
        content,  # 输入审核内容
        safety_settings=safety_settings,  # 应用安全设置
        generation_config=genai.types.GenerationConfig(candidate_count=1)  # 配置1候选，少输出
    )
    if response.prompt_feedback and any(blocked := [r for r in response.prompt_feedback.block_reason if r]):  # 检查prompt反馈阻塞原因
        return {"flagged": True, "categories": [str(reason) for reason in blocked]}  # 返回标记和原因列表
    return {"flagged": False, "categories": []}  # 无问题，返回false