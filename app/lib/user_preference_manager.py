
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
        
        try:
            # Query language from profiles table
            profile_response = supabase_admin.from_("profiles").select("language").eq("id", self.user_id).execute()
            
            if not profile_response.data:
                error_msg = f"Profile record not found for user ID {self.user_id}"
                print(error_msg)
                return error_msg
            
            language = profile_response.data[0].get("language", "en-US")
            
            return language
            
        except Exception as e:
            error_msg = f"Error occurred while getting language preference: {str(e)}"
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
        print(f"Setting language for user ID {self.user_id} to: {language}")
        
        try:
            # Validate language format (IETF BCP 47 standard)
            # Format: language-region or language
            # Examples: zh-TW, en-US, ja-JP, fr, de
            language_pattern = r'^[a-z]{2,3}(-[A-Z]{2})?$'
            if not re.match(language_pattern, language):
                return f"Error: Language format '{language}' does not conform to IETF BCP 47 standard. Correct format should be: zh-TW, en-US, ja-JP, fr, de, etc."
            
            # Update language in profiles table
            update_response = supabase_admin.from_("profiles").update({
                "language": language
            }).eq("id", self.user_id).execute()
            
            if update_response.data:
                print(f"Successfully updated language for user {self.user_id} to: {language}")
                return f"Successfully set language to: {language}"
            else:
                error_msg = f"Failed to update language, user {self.user_id} not found"
                print(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"Error occurred while setting language: {str(e)}"
            print(error_msg)
            return error_msg
