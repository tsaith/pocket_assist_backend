from langchain_core.tools import StructuredTool

from app.lib.user_note_manager import UserNoteManager


def create_create_note_tool(user_id: str) -> StructuredTool:
    """創建添加筆記工具"""

    def create_note(title: str, content: str) -> str:
        """添加新的筆記"""
        manager = UserNoteManager(user_id)
        return manager.create_note(title, content)

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
        manager = UserNoteManager(user_id)
        return manager.read_notes()

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
        manager = UserNoteManager(user_id)
        return manager.read_note(id)

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
        manager = UserNoteManager(user_id)
        return manager.update_note(id, title, content)

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
        manager = UserNoteManager(user_id)
        return manager.delete_note(id)

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
        manager = UserNoteManager(user_id)
        return manager.search_notes(keyword)

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
        manager = UserNoteManager(user_id)
        return manager.search_notes_by_time(start_at, end_at)

    search_notes_by_time_tool = StructuredTool.from_function(
        func=search_notes_by_time,
        name="search_notes_by_time",
        description="搜尋智能助理的筆記內容，可以根據時間範圍搜尋 created_at 或 updated_at 介於指定時間之間的筆記，需要提供 start_at 和 end_at 參數（請使用本地時間）",
    )

    return search_notes_by_time_tool
