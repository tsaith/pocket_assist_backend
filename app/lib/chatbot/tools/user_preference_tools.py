from typing import Tuple
from langchain_core.tools import StructuredTool
from app.lib.supabase import supabase_admin
from app.lib.utils import (
    get_user_language, 
    set_user_language,
    get_user_timezone,
    set_user_timezone,
    get_user_reminder_method, 
    set_user_reminder_method
)

def create_get_user_timezone_tool(user_id: str) -> StructuredTool:
    """創建獲取用戶時區工具"""
    
    def get_user_timezone_wrapper() -> Tuple[str, dict]:
        """獲取用戶時區的包裝函數"""
        return get_user_timezone(user_id)
    
    get_user_timezone_tool = StructuredTool.from_function(
        func=get_user_timezone_wrapper,
        name="get_user_timezone",
        description="獲取目前用戶的時區設定。",
        return_direct=False
    )
    
    return get_user_timezone_tool




def create_get_user_language_tool(user_id: str) -> StructuredTool:
    """創建獲取用戶語言工具"""
    
    def get_user_language_wrapper() -> Tuple[str, dict]:
        """獲取用戶語言的包裝函數"""
        return get_user_language(user_id)
    
    get_user_language_tool = StructuredTool.from_function(
        func=get_user_language_wrapper,
        name="get_user_language",
        description="獲取目前用戶的語言設定。",
        return_direct=False
    )
    
    return get_user_language_tool


def create_get_user_reminder_method_tool(user_id: str) -> StructuredTool:
    """創建獲取用戶提醒方法工具"""
    
    def get_user_reminder_method_wrapper() -> Tuple[str, dict]:
        """獲取用戶提醒方法的包裝函數"""
        return get_user_reminder_method(user_id)
    
    get_user_reminder_method_tool = StructuredTool.from_function(
        func=get_user_reminder_method_wrapper,
        name="get_user_reminder_method",
        description="獲取提醒方法，支援 'app' 或 'line' 或 'notification'。",
        return_direct=False
    )
    
    return get_user_reminder_method_tool

def create_set_user_timezone_tool(user_id: str) -> StructuredTool:
    """創建設定用戶時區工具"""
    
    def set_user_timezone_wrapper(timezone: str) -> Tuple[str, dict]:
        """設定用戶時區的包裝函數"""
        print(f"設定用戶 {user_id} 的時區為：{timezone}")
        return set_user_timezone(user_id, timezone)
    
    set_user_timezone_tool = StructuredTool.from_function(
        func=set_user_timezone_wrapper,
        name="set_user_timezone",
        description="設定時區，需要提供 timezone 參數。時區格式應為標準時區名稱，例如：Asia/Taipei, America/New_York, Europe/London 等。",
        return_direct=False
    )
    
    return set_user_timezone_tool


def create_set_user_language_tool(user_id: str) -> StructuredTool:
    """創建設定用戶語言工具"""
    
    def set_user_language_wrapper(language: str) -> Tuple[str, dict]:
        """設定用戶語言的包裝函數"""
        print(f"設定用戶 {user_id} 的語言為：{language}")
        return set_user_language(user_id, language)
    
    set_user_language_tool = StructuredTool.from_function(
        func=set_user_language_wrapper,
        name="set_user_language",
        description="設定語言，需要提供 language 參數。語言格式需符合 IETF BCP 47 標準，例如：zh-TW, en-US, ja-JP, fr, de 等。",
        return_direct=False
    )
    
    return set_user_language_tool


def create_set_user_reminder_method_tool(user_id: str) -> StructuredTool:
    """創建設定用戶提醒方法工具"""
    
    def set_user_reminder_method_wrapper(reminder_method: str) -> Tuple[str, dict]:
        """設定用戶提醒方法的包裝函數"""
        return set_user_reminder_method(user_id, reminder_method)
    
    set_user_reminder_method_tool = StructuredTool.from_function(
        func=set_user_reminder_method_wrapper,
        name="set_user_reminder_method",
        description="設定提醒方法，需要提供 reminder_method 參數。允許的值有：'app' 或 'line' 或 'notification'。",
        return_direct=False
    )
    
    return set_user_reminder_method_tool
