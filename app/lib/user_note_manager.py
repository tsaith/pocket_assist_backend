
from typing import Optional, List, Dict, Any

from app.lib.supabase import supabase_admin
from app.lib.utils.time_utils import (
    convert_user_local_to_utc_time,
    convert_utc_to_user_local_time
)

from app.core.constants import Constants

class UserNoteManager:
    """Manager class for user note operations"""
    
    def __init__(self, user_id: str):
        """
        Initialize UserNoteManager
        
        Args:
            user_id: The user's ID
        """
        self.user_id = user_id
    
    def get_note_count(self) -> int:
        """
        Get the count of user's notes
        
        Returns:
            int: Number of notes for the user
        """
        print(f"取得筆記數量 from user_id：{self.user_id}")
        try:
            response = supabase_admin.from_("notes").select("*", count="exact").eq("user_id", self.user_id).execute()
            count = response.count if response.count is not None else 0
            print(f"筆記數量：{count}")
            return count
        except Exception as e:
            print(f"取得筆記數量時發生錯誤：{str(e)}")
            return 0
    
    def create_note(self, title: str, content: str) -> str:
        """
        Create a new note with subscription limit check
        
        Args:
            title: Note title
            content: Note content
            
        Returns:
            str: Success or error message
        """
        print(f"添加筆記：Title {title}, Content {content}")
        try:
            # Get current notes count
            current_notes_count = self.get_note_count()
            
            if current_notes_count >= Constants.NOTES_MAX:
                print(f"超過最大筆記上限：{Constants.NOTES_MAX}")
                return f"無法新增筆記：達到最大筆記上限，最多只能新增 {Constants.NOTES_MAX} 個筆記"
                
            # Check if note with same title already exists
            response = supabase_admin.from_("notes").select("*").eq("user_id", self.user_id).eq("title", title).execute()
            
            if response.data:
                return f"已存在相同的 Title: {title} 記錄"
            
            # Insert new record
            result = supabase_admin.from_("notes").insert({
                "user_id": self.user_id,
                "title": title,
                "content": content
            }).execute()
            
            if result.data:
                new_record = result.data[0]
                return f"成功添加筆記，ID: {new_record.get('id', '')}, Title: {title}, Content: {content}"
            else:
                return "添加筆記失敗"
                
        except Exception as e:
            error_msg = f"添加筆記時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg
    
    def read_notes(self) -> str:
        """
        Read all notes
        
        Returns:
            str: Formatted notes list or error message
        """
        print(f"讀取全部筆記 from user_id：{self.user_id}")
        try:
            response = supabase_admin.from_("notes").select("id, title, content, created_at, updated_at").eq("user_id", self.user_id).execute()
            if response.data:
                notes_list = []
                for note_data in response.data:
                    note_info = f"ID: {note_data.get('id', '')}, Title: {note_data.get('title', '')}, Content: {note_data.get('content', '')}, Created: {note_data.get('created_at', '')}, Updated: {note_data.get('updated_at', '')}"
                    notes_list.append(note_info)
                content = "\n".join(notes_list)
                
                print(f"筆記內容：{content}")
                return content
            else:
                return "No notes found"
        except Exception as e:
            print(f"讀取筆記內容時發生錯誤：{str(e)}")
            return ""
    
    def read_note(self, id: str) -> str:
        """
        Read a single note
        
        Args:
            id: Note ID
            
        Returns:
            str: Note information or error message
        """
        print(f"讀取單個筆記 from user_id：{self.user_id}, note_id：{id}")
        try:
            response = supabase_admin.from_("notes").select("id, title, content, created_at, updated_at").eq("id", id).eq("user_id", self.user_id).execute()
            
            if response.data:
                note_data = response.data[0]
                note_info = f"ID: {note_data.get('id', '')}, Title: {note_data.get('title', '')}, Content: {note_data.get('content', '')}, Created: {note_data.get('created_at', '')}, Updated: {note_data.get('updated_at', '')}"
                
                print(f"筆記內容：{note_info}")
                return note_info
            else:
                return f"找不到 ID {id} 的筆記記錄"
        except Exception as e:
            print(f"讀取筆記內容時發生錯誤：{str(e)}")
            return ""
    
    def update_note(self, id: str, title: str, content: str) -> bool:
        """
        Update a note
        
        Args:
            id: Note ID
            title: New title
            content: New content
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        print(f"更新筆記內容：ID {id}, Title {title}, Content {content}")
        try:
            # Check if record exists
            response = supabase_admin.from_("notes").select("*").eq("id", id).eq("user_id", self.user_id).execute()
            
            if response.data:
                # Update record
                supabase_admin.from_("notes").update({
                    "title": title,
                    "content": content,
                    "updated_at": "now()"
                }).eq("id", id).eq("user_id", self.user_id).execute()
                return True
            else:
                print(f"找不到 ID {id} 的筆記記錄")
                return False
                
        except Exception as e:
            print(f"更新筆記內容時發生錯誤：{str(e)}")
            return False
    
    def delete_note(self, id: str) -> str:
        """
        Delete a note
        
        Args:
            id: Note ID
            
        Returns:
            str: Success or error message
        """
        print(f"刪除筆記：ID {id}")
        try:
            # Check if record exists
            response = supabase_admin.from_("notes").select("*").eq("id", id).eq("user_id", self.user_id).execute()
            
            if not response.data:
                return f"找不到 ID {id} 的筆記記錄"
            
            # Delete record
            result = supabase_admin.from_("notes").delete().eq("id", id).eq("user_id", self.user_id).execute()
            
            if result.data:
                return f"成功刪除筆記記錄，ID: {id}"
            else:
                return "刪除筆記記錄失敗"
                
        except Exception as e:
            error_msg = f"刪除筆記時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg
    
    def search_notes(self, keyword: str) -> str:
        """
        Search notes by keyword in title or content
        
        Args:
            keyword: Search keyword
            
        Returns:
            str: Formatted notes list or error message
        """
        print(f"搜尋筆記 from user_id：{self.user_id}, keyword：{keyword}")
        try:
            # Search in title and content fields
            response = supabase_admin.from_("notes").select("id, title, content, created_at, updated_at").eq("user_id", self.user_id).or_(f"title.ilike.%{keyword}%,content.ilike.%{keyword}%").execute()
            
            if response.data:
                notes_list = []
                for note_data in response.data:
                    note_info = f"ID: {note_data.get('id', '')}, Title: {note_data.get('title', '')}, Content: {note_data.get('content', '')}, Created: {note_data.get('created_at', '')}, Updated: {note_data.get('updated_at', '')}"
                    notes_list.append(note_info)
                content = "\n".join(notes_list)
                
                print(f"搜尋結果：找到 {len(response.data)} 個筆記")
                return content
            else:
                return f"沒有找到包含關鍵字 '{keyword}' 的筆記"
        except Exception as e:
            print(f"搜尋筆記時發生錯誤：{str(e)}")
            return f"搜尋筆記時發生錯誤：{str(e)}"
    
    def search_notes_by_time(self, start_at: str, end_at: str) -> str:
        """
        Search notes by time range
        
        Args:
            start_at: Start time (user local time, format: YYYY-MM-DD HH:MM:SS)
            end_at: End time (user local time, format: YYYY-MM-DD HH:MM:SS)
            
        Returns:
            str: Formatted notes list or error message
        """
        print(f"根據時間範圍搜尋筆記 from user_id：{self.user_id}, start_at：{start_at}, end_at：{end_at}")
        try:
            # Convert user local time to UTC
            start_at_utc, start_info = convert_user_local_to_utc_time(self.user_id, start_at)
            end_at_utc, end_info = convert_user_local_to_utc_time(self.user_id, end_at)
            
            # Check if conversion was successful
            if "error" in start_info or "error" in end_info:
                return f"時間轉換失敗，請確認時間格式是否正確"
            
            print(f"start_at_utc：{start_at_utc}, end_at_utc：{end_at_utc}")
            
            # Search by time range
            response = supabase_admin.from_("notes").select("id, title, content, created_at, updated_at").eq("user_id", self.user_id).or_(f"created_at.gte.{start_at_utc},created_at.lte.{end_at_utc},updated_at.gte.{start_at_utc},updated_at.lte.{end_at_utc}").execute()
            
            if response.data:
                notes_list = []
                for note_data in response.data:
                    note_info = f"ID: {note_data.get('id', '')}, Title: {note_data.get('title', '')}, Content: {note_data.get('content', '')}, Created: {note_data.get('created_at', '')}, Updated: {note_data.get('updated_at', '')}"
                    notes_list.append(note_info)
                content = "\n".join(notes_list)
                
                print(f"時間範圍搜尋結果：找到 {len(response.data)} 個筆記")
                return content
            else:
                return f"沒有找到在時間範圍 '{start_at}' 到 '{end_at}' 之間創建或更新的筆記"
        except Exception as e:
            print(f"根據時間範圍搜尋筆記時發生錯誤：{str(e)}")
            return f"根據時間範圍搜尋筆記時發生錯誤：{str(e)}"
