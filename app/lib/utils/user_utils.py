from typing import Tuple

from app.lib.supabase import supabase_admin


def get_user_timezone(user_id: str) -> Tuple[str, dict]:
    """獲取指定用戶的時區資訊"""
    print(f"獲取 user ID {user_id} 的時區資訊")
    
    try:
        # 從 profiles 表取得 timezone
        profile_response = supabase_admin.from_("profiles").select("timezone").eq("id", user_id).execute()
        
        if not profile_response.data:
            error_msg = f"找不到 user ID {user_id} 的 profile 記錄"
            print(error_msg)
            return error_msg, {"error": "Profile not found"}
        
        timezone = profile_response.data[0].get("timezone", "Asia/Taipei")
        
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

def set_user_timezone(user_id: str, timezone: str) -> Tuple[str, dict]:
    """設定指定用戶的時區"""
    print(f"設定 user ID {user_id} 的時區為：{timezone}")
    
    try:
        # 驗證時區格式是否為有效的時區名稱
        # 常見的時區格式：Asia/Taipei, America/New_York, Europe/London 等
        import re
        timezone_pattern = r'^[A-Za-z_]+/[A-Za-z_]+$'
        if not re.match(timezone_pattern, timezone):
            return f"錯誤：時區格式 '{timezone}' 不正確。正確格式應為：Asia/Taipei, America/New_York, Europe/London 等", {"error": "Invalid timezone format"}
        
        # 更新 profiles 表中的 timezone 欄位
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


def get_user_language(user_id: str) -> Tuple[str, dict]:
    """獲取指定用戶的設定語言"""
    print(f"獲取 user ID {user_id} 的設定語言")
    
    try:
        # 從 profiles 表取得 language
        profile_response = supabase_admin.from_("profiles").select("language").eq("id", user_id).execute()
        
        if not profile_response.data:
            error_msg = f"找不到 user ID {user_id} 的 profile 記錄"
            print(error_msg)
            return error_msg, {"error": "Profile not found"}
        
        language = profile_response.data[0].get("language", "zh-TW")
        
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

def set_user_language(user_id: str, language: str) -> Tuple[str, dict]:
    """設定指定用戶的語言"""
    print(f"設定 user ID {user_id} 的語言為：{language}")
    
    try:
        # 驗證語言格式是否符合 IETF BCP 47 標準
        # 基本格式：language-region 或 language
        # 例如：zh-TW, en-US, ja-JP, fr, de
        import re
        language_pattern = r'^[a-z]{2,3}(-[A-Z]{2})?$'
        if not re.match(language_pattern, language):
            return f"錯誤：語言格式 '{language}' 不符合 IETF BCP 47 標準。正確格式應為：zh-TW, en-US, ja-JP, fr, de 等", {"error": "Invalid language format"}
        
        # 更新 profiles 表中的 language 欄位
        update_response = supabase_admin.from_("profiles").update({
            "language": language
        }).eq("id", user_id).execute()
        
        if update_response.data:
            print(f"成功更新用戶 {user_id} 的語言為：{language}")
            return f"成功設定語言為：{language}", {
                "user_id": user_id,
                "language": language,
                "status": "updated"
            }
        else:
            error_msg = f"更新語言失敗，找不到用戶 {user_id}"
            print(error_msg)
            return error_msg, {"error": "Update failed"}
            
    except Exception as e:
        error_msg = f"設定語言時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


def get_user_reminder_method(user_id: str) -> Tuple[str, dict]:
    """獲取指定用戶的提醒方法"""
    print(f"獲取 user ID {user_id} 的提醒方法")
    
    try:
        # 從 profiles 表取得 reminder_method
        profile_response = supabase_admin.from_("profiles").select("reminder_method").eq("id", user_id).execute()
        
        if not profile_response.data:
            error_msg = f"找不到 user ID {user_id} 的 profile 記錄"
            print(error_msg)
            return error_msg, {"error": "Profile not found"}
        
        reminder_method = profile_response.data[0].get("reminder_method", "app")
        
        reminder_method_info = {
            "user_id": user_id,
            "reminder_method": reminder_method
        }
        
        print(f"目前的提醒方法：{reminder_method}")
        content = f"目前提醒方法：{reminder_method}"
        
        return content, reminder_method_info
        
    except Exception as e:
        error_msg = f"獲取提醒方法時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}

def set_user_reminder_method(user_id: str, reminder_method: str) -> Tuple[str, dict]:
    """設定指定用戶的提醒方法"""
    print(f"設定 user ID {user_id} 的提醒方法為：{reminder_method}")
    
    try:
        # 驗證提醒方法值
        allowed_methods = ["app", "line"]
        if reminder_method.lower() not in allowed_methods:
            return f"錯誤：提醒方法 '{reminder_method}' 不被支援。允許的值有：{', '.join(allowed_methods)}", {"error": "Invalid reminder method"}
        
        # 更新 profiles 表中的 reminder_method 欄位
        update_response = supabase_admin.from_("profiles").update({
            "reminder_method": reminder_method.lower()
        }).eq("id", user_id).execute()
        
        if update_response.data:
            print(f"成功設定用戶 {user_id} 的提醒方法為：{reminder_method.lower()}")
            return f"成功設定提醒方法為：{reminder_method.lower()}", {
                "user_id": user_id,
                "reminder_method": reminder_method.lower(),
                "status": "updated"
            }
        else:
            error_msg = f"更新提醒方法失敗，找不到用戶 {user_id}"
            print(error_msg)
            return error_msg, {"error": "Update failed"}
            
    except Exception as e:
        error_msg = f"設定提醒方法時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


