from langchain_core.tools import StructuredTool

from app.lib.user_reminder_manager import UserReminderManager


def create_create_reminder_tool(user_id: str) -> StructuredTool:
    """Create add reminder tool"""

    def create_reminder(
        remind_at: str, 
        method: str, 
        description: str,
        is_recurring: bool = False,
        recurrence_rule: str = None,
        recurrence_exceptions: str = None
    ) -> str:
        """Create a new reminder"""
        manager = UserReminderManager(user_id)
        return manager.create_reminder(remind_at, method, description, is_recurring, recurrence_rule, recurrence_exceptions)

    create_reminder_tool = StructuredTool.from_function(
        func=create_reminder,
        name="create_reminder",
        description="""
            Create a new reminder. Requires remind_at, method, description parameters.
            remind_at should use user local time (format: YYYY-MM-DD HH:MM:SS), system will automatically convert to UTC for storage.
            method supports notification and alarm:
            - notification: general notification reminder (default)
            - alarm: alarm reminder, suitable for scenarios requiring stronger reminders
            is_recurring sets whether this is a recurring reminder (default false).
            recurrence_rule uses iCalendar RRULE format to set recurrence rules, for example:
            - Daily: FREQ=DAILY
            - Weekly: FREQ=WEEKLY
            - Monthly: FREQ=MONTHLY
            - Yearly: FREQ=YEARLY
            - Monday to Friday: FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR
            recurrence_exceptions sets excluded exception dates, format is comma-separated time strings.
            """
    )

    return create_reminder_tool


def create_read_reminders_tool(user_id: str) -> StructuredTool:
    """Create read reminders tool"""

    def read_reminders() -> str:
        """Read the assistant's reminder content"""
        manager = UserReminderManager(user_id)
        return manager.read_reminders()

    read_reminders_tool = StructuredTool.from_function(
        func=read_reminders,
        name="read_reminders",
        description="Read the assistant's reminder content and return detailed information of all records",
    )

    return read_reminders_tool


def create_read_reminder_tool(user_id: str) -> StructuredTool:
    """Create read single reminder tool"""

    def read_reminder(id: str) -> str:
        """Read the assistant's single reminder content"""
        manager = UserReminderManager(user_id)
        return manager.read_reminder(id)

    read_reminder_tool = StructuredTool.from_function(
        func=read_reminder,
        name="read_reminder",
        description="Read the assistant's single reminder content, requires id parameter",
    )

    return read_reminder_tool


def create_update_reminder_tool(user_id: str) -> StructuredTool:
    """Create update reminder tool"""

    def update_reminder(id: str, remind_at: str, description: str, method: str = 'notification') -> bool:
        """Update the assistant's reminder content"""
        manager = UserReminderManager(user_id)
        return manager.update_reminder(id, remind_at, description, method)

    update_reminder_tool = StructuredTool.from_function(
        func=update_reminder,
        name="update_reminder",
        description="""
            Update the assistant's reminder content.
            Requires id, remind_at, description, method parameters.
            When setting remind_at parameter, use local time.
            method supports notification or alarm.
            """
    )

    return update_reminder_tool


def create_delete_reminder_tool(user_id: str) -> StructuredTool:
    """Create delete reminder tool"""

    def delete_reminder(id: str) -> str:
        """Delete the specified reminder record"""
        manager = UserReminderManager(user_id)
        return manager.delete_reminder(id)

    delete_reminder_tool = StructuredTool.from_function(
        func=delete_reminder,
        name="delete_reminder",
        description="Delete the specified reminder record, requires id parameter",
    )

    return delete_reminder_tool


def create_search_reminders_by_keyword_tool(user_id: str) -> StructuredTool:
    """Create search reminders tool"""

    def search_reminders_by_keyword(keyword: str) -> str:
        """Search the assistant's reminder content by keyword in description"""
        manager = UserReminderManager(user_id)
        return manager.search_reminders_by_keyword(keyword)

    search_reminders_by_keyword_tool = StructuredTool.from_function(
        func=search_reminders_by_keyword,
        name="search_reminders_by_keyword",
        description="Search the assistant's reminder content by keyword in description, requires keyword parameter",
    )

    return search_reminders_by_keyword_tool


def create_search_reminder_by_time_tool(user_id: str) -> StructuredTool:
    """Create search reminders by time range tool"""

    def search_reminders_by_time(start_at: str, end_at: str) -> str:
        """Search the assistant's reminder content by time range, looking for reminders where remind_at is between specified times (supports one-time and recurring reminders)"""
        manager = UserReminderManager(user_id)
        return manager.search_reminders_by_time(start_at, end_at)

    search_reminders_by_time_tool = StructuredTool.from_function(
        func=search_reminders_by_time,
        name="search_reminders_by_time",
        description="Search reminder records by time range, looking for reminders where remind_at is between specified times (supports one-time and recurring reminders). Requires start_at and end_at parameters (please use local time). Recurring reminders will show all trigger instances within the specified time range.",
    )

    return search_reminders_by_time_tool
