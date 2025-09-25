import os #用于读取环境变量
from pydantic_settings import BaseSettings #配置管理，支持从环境变量加载

class Settings(BaseSettings):
    db_uri: str = "mongodb://localhost:27017/ai_chat"
    jwt_secret: str = os.getenv("JWT_SECRET", "default_secret_key_change_me")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

settings = Settings()