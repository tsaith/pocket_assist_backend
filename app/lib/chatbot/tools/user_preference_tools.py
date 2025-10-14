from typing import Tuple
from langchain_core.tools import StructuredTool
from app.lib.supabase import supabase_admin
from app.lib.user_time_manager import UserTimeManager
from app.lib.user_reminder_manager import UserReminderManager
from app.lib.user_preference_manager import UserPreferenceManager

def create_get_user_timezone_tool(user_id: str) -> StructuredTool:
    """創建獲取用戶時區工具"""
    
    def get_user_timezone_wrapper() -> Tuple[str, dict]:
        """獲取用戶時區的包裝函數"""
        try:
            time_manager = UserTimeManager(user_id)
            timezone = time_manager.get_timezone()
            
            timezone_info = {
                "user_id": user_id,
                "timezone": timezone
            }
            
            content = f"目前時區：{timezone}"
            return content, timezone_info
        except Exception as e:
            error_msg = f"獲取時區資訊時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg, {"error": str(e)}
    
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
        try:
            preference_manager = UserPreferenceManager(user_id)
            language = preference_manager.get_user_language()
            
            # 檢查是否有錯誤
            if "錯誤" in language or "找不到" in language:
                return language, {"error": language}
            
            language_info = {
                "user_id": user_id,
                "language": language
            }
            
            content = f"目前設定語言：{language}"
            return content, language_info
        except Exception as e:
            error_msg = f"獲取設定語言時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg, {"error": str(e)}
    
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
        try:
            reminder_manager = UserReminderManager(user_id)
            reminder_method = reminder_manager.get_reminder_method()
            
            # 檢查是否有錯誤
            if "錯誤" in reminder_method or "找不到" in reminder_method:
                return reminder_method, {"error": reminder_method}
            
            reminder_method_info = {
                "user_id": user_id,
                "reminder_method": reminder_method
            }
            
            content = f"目前提醒方法：{reminder_method}"
            return content, reminder_method_info
        except Exception as e:
            error_msg = f"獲取提醒方法時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg, {"error": str(e)}
    
    get_user_reminder_method_tool = StructuredTool.from_function(
        func=get_user_reminder_method_wrapper,
        name="get_user_reminder_method",
        description="獲取提醒方法，支援 'notification' 或 'notification-long'。",
        return_direct=False
    )
    
    return get_user_reminder_method_tool

def create_set_user_timezone_tool(user_id: str) -> StructuredTool:
    """創建設定用戶時區工具"""
    
    def set_user_timezone_wrapper(timezone: str) -> Tuple[str, dict]:
        """設定用戶時區的包裝函數"""
        print(f"設定用戶 {user_id} 的時區為：{timezone}")
        try:
            # Validate timezone format
            import re
            timezone_pattern = r'^[A-Za-z_]+/[A-Za-z_]+$'
            if not re.match(timezone_pattern, timezone):
                error_msg = f"錯誤：時區格式 '{timezone}' 不正確。正確格式應為：Asia/Taipei, America/New_York, Europe/London 等"
                return error_msg, {"error": "Invalid timezone format"}
            
            # Update timezone in database
            update_response = supabase_admin.from_("profiles").update({
                "timezone": timezone
            }).eq("id", user_id).execute()
            
            if update_response.data:
                print(f"成功更新用戶 {user_id} 的時區為：{timezone}")
                return f"成功設定時區為：{timezone}", {
                    "user_id": user_id,
                    "timezone": timezone,
                    "status": "updated"
                }
            else:
                error_msg = f"更新時區失敗，找不到用戶 {user_id}"
                print(error_msg)
                return error_msg, {"error": "Update failed"}
                
        except Exception as e:
            error_msg = f"設定時區時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg, {"error": str(e)}
    
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
        try:
            preference_manager = UserPreferenceManager(user_id)
            result = preference_manager.set_user_language(language)
            
            # 檢查是否有錯誤
            if "錯誤" in result or "失敗" in result:
                return result, {"error": result}
            
            # 成功設定
            return result, {
                "user_id": user_id,
                "language": language,
                "status": "updated"
            }
        except Exception as e:
            error_msg = f"設定語言時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg, {"error": str(e)}
    
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
        try:
            reminder_manager = UserReminderManager(user_id)
            result = reminder_manager.set_reminder_method(reminder_method)
            
            # 檢查是否有錯誤
            if "錯誤" in result or "失敗" in result:
                return result, {"error": result}
            
            # 成功設定
            return result, {
                "user_id": user_id,
                "reminder_method": reminder_method.lower(),
                "status": "updated"
            }
        except Exception as e:
            error_msg = f"設定提醒方法時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg, {"error": str(e)}
    
    set_user_reminder_method_tool = StructuredTool.from_function(
        func=set_user_reminder_method_wrapper,
        name="set_user_reminder_method",
        description="設定提醒方法，需要提供 reminder_method 參數。允許的值有：'notification' 或 'notification-long'。",
        return_direct=False
    )
    
    return set_user_reminder_method_tool
