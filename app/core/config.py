from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Extra
from datetime import datetime


class Settings(BaseSettings):
    """
    應用程序設置類
    """
    # 應用基本設置
    APP_NAME: str = "Chatbot Service"
    
    RUN_ENV: str = "development"
    
    # Site URL
    SITE_URL: str = ""

    # Private access token
    PRIVATE_ACCESS_TOKEN: str = ""

    # API密鑰
    OPENAI_API_KEY: str = ""

    # Google Map Platform API Key
    GOOGLE_MAP_PLATFORM_API_KEY: str = ""
    
    # Supabase設置
    SUPABASE_PROJECT_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    
    # LINE Offical Account
    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""

    # 聊天機器人設置
    TEST_CHATBOT_ID: str = ""

    def get_current_timestamp(self) -> str:
        """
        獲取當前時間戳
        """
        return datetime.utcnow().isoformat() + "Z"

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra=Extra.allow)

settings = Settings()