from langchain_core.tools import StructuredTool

from app.lib.user_reminder_manager import UserReminderManager


def create_create_reminder_tool(user_id: str) -> StructuredTool:
    """創建添加提醒工具"""

    def create_reminder(
        remind_at: str, 
        method: str, 
        description: str,
        is_recurring: bool = False,
        recurrence_rule: str = None,
        recurrence_exceptions: str = None
    ) -> str:
        """添加新的提醒"""
        manager = UserReminderManager(user_id)
        return manager.create_reminder(remind_at, method, description, is_recurring, recurrence_rule, recurrence_exceptions)

    create_reminder_tool = StructuredTool.from_function(
        func=create_reminder,
        name="create_reminder",
        description="""
            添加新的提醒，需要提供 remind_at、method、description 等參數。
            remind_at 請使用用戶本地時間（格式：YYYY-MM-DD HH:MM:SS），系統會自動轉換為 UTC 時間儲存。
            method 支援 notification、notification-long。
            is_recurring 設定是否為重複提醒（預設 false）。
            recurrence_rule 使用 iCalendar RRULE 格式設定重複規則，例如：
            - 每日：FREQ=DAILY
            - 每週：FREQ=WEEKLY
            - 每月：FREQ=MONTHLY
            - 每年：FREQ=YEARLY
            - 每週一到週五：FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR
            recurrence_exceptions 設定排除的例外日期，格式為逗號分隔的時間字串。
            """
    )

    return create_reminder_tool


def create_read_reminders_tool(user_id: str) -> StructuredTool:
    """創建讀取提醒工具"""

    def read_reminders() -> str:
        """讀取智能助理的提醒內容"""
        manager = UserReminderManager(user_id)
        return manager.read_reminders()

    read_reminders_tool = StructuredTool.from_function(
        func=read_reminders,
        name="read_reminders",
        description="讀取智能助理的提醒內容，返回所有記錄的詳細信息",
    )

    return read_reminders_tool


def create_read_reminder_tool(user_id: str) -> StructuredTool:
    """創建讀取單個提醒工具"""

    def read_reminder(id: str) -> str:
        """讀取智能助理的單個提醒內容"""
        manager = UserReminderManager(user_id)
        return manager.read_reminder(id)

    read_reminder_tool = StructuredTool.from_function(
        func=read_reminder,
        name="read_reminder",
        description="讀取智能助理的單個提醒內容，需要提供 id 參數",
    )

    return read_reminder_tool


def create_update_reminder_tool(user_id: str) -> StructuredTool:
    """創建更新提醒工具"""

    def update_reminder(id: str, remind_at: str, description: str, method: str = 'notification') -> bool:
        """更新智能助理的提醒內容"""
        manager = UserReminderManager(user_id)
        return manager.update_reminder(id, remind_at, description, method)

    update_reminder_tool = StructuredTool.from_function(
        func=update_reminder,
        name="update_reminder",
        description="""
            更新智能助理的提醒內容，
            需要提供 id、remind_at、description、method 等參數，
            時間參數時請用本地時間設定 remind_at;
            method 支援 notification 或 app 或 line。
            """
    )

    return update_reminder_tool


def create_delete_reminder_tool(user_id: str) -> StructuredTool:
    """創建刪除提醒工具"""

    def delete_reminder(id: str) -> str:
        """刪除指定的提醒記錄"""
        manager = UserReminderManager(user_id)
        return manager.delete_reminder(id)

    delete_reminder_tool = StructuredTool.from_function(
        func=delete_reminder,
        name="delete_reminder",
        description="刪除指定的提醒記錄，需要提供 id 參數",
    )

    return delete_reminder_tool


def create_search_reminders_by_keyword_tool(user_id: str) -> StructuredTool:
    """創建搜尋提醒工具"""

    def search_reminders_by_keyword(keyword: str) -> str:
        """搜尋智能助理的提醒內容，根據關鍵字搜尋描述"""
        manager = UserReminderManager(user_id)
        return manager.search_reminders_by_keyword(keyword)

    search_reminders_by_keyword_tool = StructuredTool.from_function(
        func=search_reminders_by_keyword,
        name="search_reminders_by_keyword",
        description="搜尋智能助理的提醒內容，根據關鍵字搜尋描述，需要提供 keyword 參數",
    )

    return search_reminders_by_keyword_tool


def create_search_reminder_by_time_tool(user_id: str) -> StructuredTool:
    """創建根據時間範圍搜尋提醒工具"""

    def search_reminders_by_time(start_at: str, end_at: str) -> str:
        """搜尋智能助理的提醒內容，根據時間範圍搜尋 remind_at 介於指定時間之間的提醒（支援一次性和重複性提醒）"""
        manager = UserReminderManager(user_id)
        return manager.search_reminders_by_time(start_at, end_at)

    search_reminders_by_time_tool = StructuredTool.from_function(
        func=search_reminders_by_time,
        name="search_reminders_by_time",
        description="搜尋提醒紀錄，根據時間範圍搜尋 remind_at 介於指定時間之間的提醒（支援一次性和重複性提醒），需要提供 start_at 和 end_at 參數（請使用本地的時間）。重複性提醒會顯示在指定時間範圍內的所有觸發實例。",
    )

    return search_reminders_by_time_tool
