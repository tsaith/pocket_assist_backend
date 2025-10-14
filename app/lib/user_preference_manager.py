
from typing import Optional
import re

from app.lib.supabase import supabase_admin


class UserPreferenceManager:
    """Manager class for user preference operations"""
    
    def __init__(self, user_id: str):
        """
        Initialize UserPreferenceManager
        
        Args:
            user_id: The user's ID
        """
        self.user_id = user_id
    
    def get_user_language(self) -> str:
        """
        Get user's language preference
        
        Returns:
            str: Language code (e.g., 'zh-TW', 'en-US') or error message
        """
        print(f"獲取 user ID {self.user_id} 的設定語言")
        
        try:
            # Query language from profiles table
            profile_response = supabase_admin.from_("profiles").select("language").eq("id", self.user_id).execute()
            
            if not profile_response.data:
                error_msg = f"找不到 user ID {self.user_id} 的 profile 記錄"
                print(error_msg)
                return error_msg
            
            language = profile_response.data[0].get("language", "zh-TW")
            print(f"目前設定語言：{language}")
            
            return language
            
        except Exception as e:
            error_msg = f"獲取設定語言時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg
    
    def set_user_language(self, language: str) -> str:
        """
        Set user's language preference
        
        Args:
            language: Language code (e.g., 'zh-TW', 'en-US', 'ja-JP')
            
        Returns:
            str: Success or error message
        """
        print(f"設定 user ID {self.user_id} 的語言為：{language}")
        
        try:
            # Validate language format (IETF BCP 47 standard)
            # Format: language-region or language
            # Examples: zh-TW, en-US, ja-JP, fr, de
            language_pattern = r'^[a-z]{2,3}(-[A-Z]{2})?$'
            if not re.match(language_pattern, language):
                return f"錯誤：語言格式 '{language}' 不符合 IETF BCP 47 標準。正確格式應為：zh-TW, en-US, ja-JP, fr, de 等"
            
            # Update language in profiles table
            update_response = supabase_admin.from_("profiles").update({
                "language": language
            }).eq("id", self.user_id).execute()
            
            if update_response.data:
                print(f"成功更新用戶 {self.user_id} 的語言為：{language}")
                return f"成功設定語言為：{language}"
            else:
                error_msg = f"更新語言失敗，找不到用戶 {self.user_id}"
                print(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"設定語言時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg
