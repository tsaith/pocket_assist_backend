import pytest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
from datetime import datetime, timezone

from app.lib.user_reminder_manager import UserReminderManager


class MockSupabaseResponse:
    """Mock Supabase response object"""
    def __init__(self, data=None, count=None):
        self.data = data or []
        self.count = count


class MockSupabaseQuery:
    """Mock Supabase query builder"""
    def __init__(self, response_data=None, count=None, insert_data=None, update_data=None, delete_data=None):
        self.response_data = response_data or []
        self.count = count
        self.insert_data = insert_data
        self.update_data = update_data or []
        self.delete_data = delete_data or []
        self.conditions = {}
        self.insert_payload = None
        self.update_payload = None
        self._is_delete = False
        
    def select(self, *args, **kwargs):
        return self
    
    def insert(self, data):
        self.insert_payload = data
        return self
    
    def update(self, data):
        self.update_payload = data
        return self
    
    def delete(self):
        self._is_delete = True
        return self
    
    def eq(self, column, value):
        self.conditions[column] = value
        return self
    
    def gte(self, column, value):
        self.conditions[f"{column}_gte"] = value
        return self
    
    def lte(self, column, value):
        self.conditions[f"{column}_lte"] = value
        return self
    
    def or_(self, condition):
        self.conditions["or"] = condition
        return self
    
    def execute(self):
        if self.insert_payload:
            # Return inserted data with generated ID
            inserted_data = self.insert_payload.copy()
            inserted_data["id"] = "test-reminder-id-123"
            return MockSupabaseResponse(data=[inserted_data])
        elif self.update_payload:
            return MockSupabaseResponse(data=self.update_data)
        elif self._is_delete:
            return MockSupabaseResponse(data=self.delete_data)
        else:
            return MockSupabaseResponse(data=self.response_data, count=self.count)


# ========== Reminder Method Tests ==========

@patch('app.lib.user_reminder_manager.supabase_admin')
def test_get_reminder_method_returns_value(mock_supabase):
    """Test getting reminder method from user profile"""
    # Setup mock
    mock_query = MockSupabaseQuery(response_data=[{"reminder_method": "line"}])
    mock_supabase.from_.return_value = mock_query

    manager = UserReminderManager("user-123")
    result = manager.get_reminder_method()

    assert result == "line"
    mock_supabase.from_.assert_called_with("profiles")


@patch('app.lib.user_reminder_manager.supabase_admin')
def test_set_reminder_method_updates_value(mock_supabase):
    """Test setting reminder method successfully"""
    # Setup mock
    mock_query = MockSupabaseQuery(update_data=[{"id": "user-789"}])
    mock_supabase.from_.return_value = mock_query

    manager = UserReminderManager("user-789")
    result = manager.set_reminder_method("notification")

    assert result == "成功設定提醒方法為：notification"
    assert mock_query.update_payload == {"reminder_method": "notification"}


# ========== One-time Reminder Tests ==========

@patch('app.lib.user_reminder_manager.supabase_admin')
def test_create_one_time_reminder_success(mock_supabase):
    """Test creating a one-time reminder successfully"""
    
    # Setup supabase mocks
    call_count = 0
    def mock_from(table):
        nonlocal call_count
        call_count += 1
        if table == "reminders":
            if call_count == 1:
                return MockSupabaseQuery(count=0)  # Count query
            elif call_count == 2:
                return MockSupabaseQuery(response_data=[])  # Duplicate check
            else:
                return MockSupabaseQuery()  # Insert query
        return MockSupabaseQuery()
    
    mock_supabase.from_.side_effect = mock_from

    manager = UserReminderManager("user-123")
    result = manager.create_reminder(
        remind_at="2024-12-25 10:00:00",
        method="notification",
        description="Test reminder",
        is_recurring=False
    )

    assert "成功添加提醒" in result
    assert "test-reminder-id-123" in result


@patch('app.lib.user_reminder_manager.supabase_admin')
def test_create_one_time_reminder_duplicate_rejected(mock_supabase):
    """Test rejecting duplicate one-time reminders"""
    
    # Setup supabase mocks
    call_count = 0
    def mock_from(table):
        nonlocal call_count
        call_count += 1
        if table == "reminders":
            if call_count == 1:
                return MockSupabaseQuery(count=0)  # Count query
            elif call_count == 2:
                return MockSupabaseQuery(response_data=[{"id": "existing-reminder"}])  # Duplicate found
            else:
                return MockSupabaseQuery()  # Should not reach insert
        return MockSupabaseQuery()
    
    mock_supabase.from_.side_effect = mock_from

    manager = UserReminderManager("user-123")
    result = manager.create_reminder(
        remind_at="2024-12-25 10:00:00",
        method="notification",
        description="Test reminder",
        is_recurring=False
    )

    assert "已存在相同的提醒記錄" in result


# ========== Recurring Reminder Tests ==========

@patch('app.lib.user_reminder_manager.supabase_admin')
def test_create_daily_recurring_reminder(mock_supabase):
    """Test creating a daily recurring reminder"""
    
    # Setup supabase mocks - only count and insert for recurring reminders
    call_count = 0
    def mock_from(table):
        nonlocal call_count
        call_count += 1
        if table == "reminders":
            if call_count == 1:
                return MockSupabaseQuery(count=0)  # Count query
            else:
                return MockSupabaseQuery()  # Insert query
        return MockSupabaseQuery()
    
    mock_supabase.from_.side_effect = mock_from

    manager = UserReminderManager("user-123")
    result = manager.create_reminder(
        remind_at="2024-12-25 10:00:00",
        method="notification",
        description="Daily standup meeting",
        is_recurring=True,
        recurrence_rule="FREQ=DAILY"
    )

    assert "成功添加提醒" in result
    assert "重複提醒: 是" in result


@patch('app.lib.user_reminder_manager.supabase_admin')
def test_create_weekly_recurring_reminder(mock_supabase):
    """Test creating a weekly recurring reminder"""
    
    # Setup supabase mocks
    call_count = 0
    def mock_from(table):
        nonlocal call_count
        call_count += 1
        if table == "reminders":
            if call_count == 1:
                return MockSupabaseQuery(count=0)
            else:
                return MockSupabaseQuery()
        return MockSupabaseQuery()
    
    mock_supabase.from_.side_effect = mock_from

    manager = UserReminderManager("user-123")
    result = manager.create_reminder(
        remind_at="2024-12-25 14:00:00",
        method="notification-long",
        description="Weekly team meeting",
        is_recurring=True,
        recurrence_rule="FREQ=WEEKLY;BYDAY=WE"
    )

    assert "成功添加提醒" in result
    assert "重複提醒: 是" in result


@patch('app.lib.user_reminder_manager.supabase_admin')
def test_create_monthly_recurring_reminder_with_exceptions(mock_supabase):
    """Test creating a monthly recurring reminder with exception dates"""
    
    # Setup supabase mocks
    call_count = 0
    def mock_from(table):
        nonlocal call_count
        call_count += 1
        if table == "reminders":
            if call_count == 1:
                return MockSupabaseQuery(count=0)
            else:
                insert_query = MockSupabaseQuery()
                return insert_query
        return MockSupabaseQuery()
    
    mock_supabase.from_.side_effect = mock_from

    manager = UserReminderManager("user-123")
    result = manager.create_reminder(
        remind_at="2024-12-01 09:00:00",
        method="notification",
        description="Monthly report due",
        is_recurring=True,
        recurrence_rule="FREQ=MONTHLY;BYMONTHDAY=1",
        recurrence_exceptions="2025-01-01, 2025-07-01"
    )

    assert "成功添加提醒" in result
    assert "重複提醒: 是" in result


def test_create_recurring_reminder_missing_rule():
    """Test creating recurring reminder without recurrence rule fails"""
    manager = UserReminderManager("user-123")
    result = manager.create_reminder(
        remind_at="2024-12-25 10:00:00",
        method="notification",
        description="Invalid recurring reminder",
        is_recurring=True
        # Missing recurrence_rule
    )

    assert "錯誤：設定為重複提醒時必須提供 recurrence_rule" in result


@patch('app.lib.user_reminder_manager.supabase_admin')
def test_create_reminder_exceeds_limit(mock_supabase):
    """Test creating reminder when exceeding the maximum limit"""
    # Setup supabase mock to return max count
    from app.core.constants import Constants
    count_query = MockSupabaseQuery(count=Constants.REMINDERS_MAX)
    mock_supabase.from_.return_value = count_query

    manager = UserReminderManager("user-123")
    result = manager.create_reminder(
        remind_at="2024-12-25 10:00:00",
        method="notification",
        description="Should fail due to limit",
        is_recurring=False
    )

    assert "達到最大提醒上限" in result


def test_create_reminder_invalid_method():
    """Test creating reminder with invalid method"""
    manager = UserReminderManager("user-123")
    result = manager.create_reminder(
        remind_at="2024-12-25 10:00:00",
        method="invalid-method",
        description="Test reminder",
        is_recurring=False
    )

    assert "錯誤：method 必須是" in result