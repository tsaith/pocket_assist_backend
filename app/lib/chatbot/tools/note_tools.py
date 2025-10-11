from typing import List, Tuple
from langchain_core.tools import StructuredTool

from app.lib.supabase import supabase_admin

from app.lib.utils.time_utils import (
    convert_user_local_to_utc_time,
    convert_utc_to_user_local_time
)

from app.core.constants import Constants

def create_create_note_tool(user_id: str) -> StructuredTool:
    """創建添加筆記工具"""

    def create_note(title: str, content: str) -> str:
        """添加新的筆記"""

        print(f"添加筆記：Title {title}, Content {content}")
        try:
            
            # 查詢當前用戶的筆記數量
            notes_response = supabase_admin.from_("notes").select("id", count="exact").eq("user_id", user_id).execute()
            current_notes_count = notes_response.count if notes_response.count is not None else 0
            
            print(f"當前筆記數量：{current_notes_count}")
            
            # 檢查是否超過限制
            if current_notes_count >= Constants.NOTES_MAX:
                print(f"無法新增筆記：超過訂閱限制：{Constants.NOTES_MAX}")
                return f"無法新增筆記：超過訂閱限制：{Constants.NOTES_MAX}"
            
            # 檢查是否已存在相同的 title 組合
            response = supabase_admin.from_("notes").select("*").eq("user_id", user_id).eq("title", title).execute()
            
            if response.data:
                return f"已存在相同的 Title: {title} 記錄"
            
            # 添加新記錄
            result = supabase_admin.from_("notes").insert({
                "user_id": user_id,
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

    create_note_tool = StructuredTool.from_function(
        func=create_note,
        name="create_note",
        description="添加新的筆記，需要提供 title 和 content 參數",
    )

    return create_note_tool


def create_read_notes_tool(user_id: str) -> StructuredTool:
    """創建讀取筆記工具"""

    def read_notes() -> str:
        """讀取智能助理的筆記內容"""

        print(f"讀取全部筆記 from user_id：{user_id}")
        content = ""
        try:
            response = supabase_admin.from_("notes").select("id, title, content, created_at, updated_at").eq("user_id", user_id).execute()
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

    read_notes_tool = StructuredTool.from_function(
        func=read_notes,
        name="read_notes",
        description="讀取所有筆記內容，返回所有記錄的詳細信息。",
    )

    return read_notes_tool


def create_read_note_tool(user_id: str) -> StructuredTool:
    """創建讀取單個筆記工具"""

    def read_note(id: str) -> str:
        """讀取智能助理的單個筆記內容"""

        print(f"讀取單個筆記 from user_id：{user_id}, note_id：{id}")
        try:
            response = supabase_admin.from_("notes").select("id, title, content, created_at, updated_at").eq("id", id).eq("user_id", user_id).execute()
            
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

    read_note_tool = StructuredTool.from_function(
        func=read_note,
        name="read_note",
        description="讀取智能助理的單個筆記內容，需要提供 id 參數",
    )

    return read_note_tool


def create_update_note_tool(user_id: str) -> StructuredTool:
    """創建更新筆記工具"""

    def update_note(id: str, title: str, content: str) -> bool:
        """更新智能助理的筆記內容"""

        print(f"更新筆記內容：ID {id}, Title {title}, Content {content}")
        is_updated = False
        try:
            # 檢查指定 ID 的記錄是否存在
            response = supabase_admin.from_("notes").select("*").eq("id", id).eq("user_id", user_id).execute()
            
            if response.data:
                # 如果記錄存在，更新內容
                supabase_admin.from_("notes").update({
                    "title": title,
                    "content": content,
                    "updated_at": "now()"
                }).eq("id", id).eq("user_id", user_id).execute()
                is_updated = True
            else:
                print(f"找不到 ID {id} 的筆記記錄")
                is_updated = False
                
        except Exception as e:
            is_updated = False
            print(f"更新筆記內容時發生錯誤：{str(e)}")

        return is_updated

    update_note_tool = StructuredTool.from_function(
        func=update_note,
        name="update_note",
        description="更新智能助理的筆記內容，需要提供 id、title 和 content 參數",
    )

    return update_note_tool


def create_delete_note_tool(user_id: str) -> StructuredTool:
    """創建刪除筆記工具"""

    def delete_note(id: str) -> str:
        """刪除指定的筆記記錄"""

        print(f"刪除筆記：ID {id}")
        try:
            # 檢查指定 ID 的記錄是否存在且屬於該 chatbot
            response = supabase_admin.from_("notes").select("*").eq("id", id).eq("user_id", user_id).execute()
            
            if not response.data:
                return f"找不到 ID {id} 的筆記記錄"
            
            # 刪除記錄
            result = supabase_admin.from_("notes").delete().eq("id", id).eq("user_id", user_id).execute()
            
            if result.data:
                return f"成功刪除筆記記錄，ID: {id}"
            else:
                return "刪除筆記記錄失敗"
                
        except Exception as e:
            error_msg = f"刪除筆記時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg

    delete_note_tool = StructuredTool.from_function(
        func=delete_note,
        name="delete_note",
        description="刪除指定的筆記記錄，需要提供 id 參數",
    )

    return delete_note_tool


def create_search_notes_tool(user_id: str) -> StructuredTool:
    """創建搜尋筆記工具"""

    def search_notes(keyword: str) -> str:
        """搜尋智能助理的筆記內容，根據關鍵字搜尋標題或內容"""

        print(f"搜尋筆記 from user_id：{user_id}, keyword：{keyword}")
        content = ""
        try:
            # 使用 ilike 進行模糊搜尋，搜尋標題或內容包含關鍵字的筆記
            response = supabase_admin.from_("notes").select("id, title, content, created_at, updated_at").eq("user_id", user_id).or_(f"title.ilike.%{keyword}%,content.ilike.%{keyword}%").execute()
            
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

    search_notes_tool = StructuredTool.from_function(
        func=search_notes,
        name="search_notes",
        description="搜尋智能助理的筆記內容，根據關鍵字搜尋標題或內容，需要提供 keyword 參數",
    )

    return search_notes_tool

def create_search_notes_by_time_tool(user_id: str) -> StructuredTool:
    """創建根據時間範圍搜尋筆記工具"""

    def search_notes_by_time(start_at: str, end_at: str) -> str:
        """搜尋智能助理的筆記內容，根據時間範圍搜尋 created_at 或 updated_at 介於指定時間之間的筆記"""

        print(f"根據時間範圍搜尋筆記 from user_id：{user_id}, start_at：{start_at}, end_at：{end_at}")
        content = ""
        try:
            # 使用時間轉換函數，將用戶本地時間轉換為 UTC
            start_at_utc, start_info = convert_user_local_to_utc_time(user_id, start_at)
            end_at_utc, end_info = convert_user_local_to_utc_time(user_id, end_at)
            
            # 檢查時間轉換是否成功
            if "error" in start_info or "error" in end_info:
                return f"時間轉換失敗，請確認時間格式是否正確"
            
            print(f"start_at_utc：{start_at_utc}, end_at_utc：{end_at_utc}")
            
            # 使用 or_ 和 gte/lte 進行時間範圍搜尋，搜尋 created_at 或 updated_at 介於指定時間之間的筆記
            response = supabase_admin.from_("notes").select("id, title, content, created_at, updated_at").eq("user_id", user_id).or_(f"created_at.gte.{start_at_utc},created_at.lte.{end_at_utc},updated_at.gte.{start_at_utc},updated_at.lte.{end_at_utc}").execute()
            
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

    search_notes_by_time_tool = StructuredTool.from_function(
        func=search_notes_by_time,
        name="search_notes_by_time",
        description="搜尋智能助理的筆記內容，可以根據時間範圍搜尋 created_at 或 updated_at 介於指定時間之間的筆記，需要提供 start_at 和 end_at 參數（請使用台灣時間）",
    )

    return search_notes_by_time_tool
