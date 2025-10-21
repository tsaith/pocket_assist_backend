import pytest
from pytest_mock import MockFixture
from datetime import datetime, timezone

from app.lib.user_reminder_manager import UserReminderManager
from tests.mock_supabase_admin import MockSupabaseAdmin, create_mock_response, create_reminder_data


def setup_user_time_manager_mock(mocker: MockFixture):
    """
    設置 UserTimeManager 的 supabase 客戶端 mock
    讓 UserTimeManager 可以正常工作但不會真的連接數據庫
    """
    # Mock time_utils 中使用的 supabase 客戶端
    # 用於獲取用戶時區信息
    mock_profiles_response = create_mock_response(data=[{
        "timezone": "Asia/Taipei"
    }])
    
    mock_time_admin = MockSupabaseAdmin()
    mock_time_admin.set_responses("profiles", [mock_profiles_response])
    
    # Patch time_utils 使用的 supabase_admin
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_time_admin)
    
    return mock_time_admin


# ========== Reminder Method Tests ==========

def test_get_reminder_method_returns_value(mocker: MockFixture):
    """Test getting reminder method from user profile"""
    # Setup mock
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[{"reminder_method": "line"}])
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440000")
    result = manager.get_reminder_method()

    assert result == "line"
    assert mock_admin.get_call_count("select", "profiles") == 1


def test_get_reminder_method_missing_profile(mocker: MockFixture):
    """Test getting reminder method when profile doesn't exist"""
    # Setup mock
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440001")
    result = manager.get_reminder_method()

    assert "找不到" in result


def test_set_reminder_method_updates_value(mocker: MockFixture):
    """Test setting reminder method successfully"""
    # Setup mock
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[{"id": "550e8400-e29b-41d4-a716-446655440002"}])
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440002")
    result = manager.set_reminder_method("notification")

    assert result == "成功設定提醒方法為：notification"
    last_update = mock_admin.get_last_update("profiles")
    assert last_update["payload"]["reminder_method"] == "notification"


def test_set_reminder_method_rejects_invalid_value():
    """Test rejecting invalid reminder method"""
    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440003")
    result = manager.set_reminder_method("email")

    assert "錯誤" in result


# ========== One-time Reminder Tests ==========

def test_create_one_time_reminder_success(mocker: MockFixture):
    """Test creating a one-time reminder successfully"""
    # Setup UserTimeManager mock for timezone handling
    setup_user_time_manager_mock(mocker)
    
    # Setup UserReminderManager mock
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("reminders", [
        create_mock_response(count=0),  # Count query
        create_mock_response(data=[]),  # Duplicate check
        create_mock_response(data=[create_reminder_data(id="test-reminder-id-123")])  # Insert
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440004")
    result = manager.create_reminder(
        remind_at="2024-12-25 10:00:00",
        method="notification",
        description="Test reminder",
        is_recurring=False
    )

    assert "成功添加提醒" in result
    assert "test-reminder-id-123" in result
    
    # Check insert was called
    last_insert = mock_admin.get_last_insert("reminders")
    assert last_insert["payload"]["description"] == "Test reminder"
    assert last_insert["payload"]["is_recurring"] == False


def test_create_one_time_reminder_with_timezone(mocker: MockFixture):
    """Test creating a one-time reminder with timezone info"""
    # Setup UserTimeManager mock
    setup_user_time_manager_mock(mocker)
    
    # Setup UserReminderManager mock
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("reminders", [
        create_mock_response(count=0),  # Count query
        create_mock_response(data=[]),  # Duplicate check
        create_mock_response(data=[create_reminder_data()])  # Insert
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440005")
    result = manager.create_reminder(
        remind_at="2024-12-25T10:00:00+08:00",
        method="notification",
        description="Test reminder with timezone",
        is_recurring=False
    )

    assert "成功添加提醒" in result


def test_create_one_time_reminder_duplicate_rejected(mocker: MockFixture):
    """Test rejecting duplicate one-time reminders"""
    # Setup UserTimeManager mock
    setup_user_time_manager_mock(mocker)
    
    # Setup UserReminderManager mock
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("reminders", [
        create_mock_response(count=0),  # Count query
        create_mock_response(data=[create_reminder_data(id="existing-reminder")])  # Duplicate found
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440006")
    result = manager.create_reminder(
        remind_at="2024-12-25 10:00:00",
        method="notification",
        description="Test reminder",
        is_recurring=False
    )

    assert "已存在相同的提醒記錄" in result
    # Should not reach insert
    assert mock_admin.get_call_count("insert", "reminders") == 0


# ========== Recurring Reminder Tests ==========

def test_create_daily_recurring_reminder(mocker: MockFixture):
    """Test creating a daily recurring reminder"""
    # Setup UserTimeManager mock
    setup_user_time_manager_mock(mocker)
    
    # Setup UserReminderManager mock
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("reminders", [
        create_mock_response(count=0),  # Count query
        create_mock_response(data=[create_reminder_data()])  # Insert
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440007")
    result = manager.create_reminder(
        remind_at="2024-12-25 10:00:00",
        method="notification",
        description="Daily standup meeting",
        is_recurring=True,
        recurrence_rule="FREQ=DAILY"
    )

    assert "成功添加提醒" in result
    assert "重複提醒: 是" in result
    
    # Check insert payload
    last_insert = mock_admin.get_last_insert("reminders")
    assert last_insert["payload"]["is_recurring"] == True
    assert last_insert["payload"]["recurrence_rule"] == "FREQ=DAILY"


def test_create_weekly_recurring_reminder(mocker: MockFixture):
    """Test creating a weekly recurring reminder"""
    # Setup UserTimeManager mock
    setup_user_time_manager_mock(mocker)
    
    # Setup UserReminderManager mock
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("reminders", [
        create_mock_response(count=0),  # Count query
        create_mock_response(data=[create_reminder_data()])  # Insert
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440008")
    result = manager.create_reminder(
        remind_at="2024-12-25 14:00:00",
        method="alarm",
        description="Weekly team meeting",
        is_recurring=True,
        recurrence_rule="FREQ=WEEKLY;BYDAY=WE"
    )

    assert "成功添加提醒" in result
    assert "重複提醒: 是" in result
    
    # Check insert payload
    last_insert = mock_admin.get_last_insert("reminders")
    assert last_insert["payload"]["method"] == "alarm"
    assert last_insert["payload"]["recurrence_rule"] == "FREQ=WEEKLY;BYDAY=WE"


def test_create_monthly_recurring_reminder_with_exceptions(mocker: MockFixture):
    """Test creating a monthly recurring reminder with exception dates"""
    # Setup UserTimeManager mock
    setup_user_time_manager_mock(mocker)
    
    # Setup UserReminderManager mock
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("reminders", [
        create_mock_response(count=0),  # Count query
        create_mock_response(data=[create_reminder_data()])  # Insert
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440009")
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
    
    # Check that exceptions were processed
    last_insert = mock_admin.get_last_insert("reminders")
    assert last_insert["payload"]["recurrence_exceptions"] == ["2025-01-01", "2025-07-01"]


def test_create_recurring_reminder_missing_rule():
    """Test creating recurring reminder without recurrence rule fails"""
    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440010")
    result = manager.create_reminder(
        remind_at="2024-12-25 10:00:00",
        method="notification",
        description="Invalid recurring reminder",
        is_recurring=True
        # Missing recurrence_rule
    )

    assert "錯誤：設定為重複提醒時必須提供 recurrence_rule" in result


def test_create_reminder_exceeds_limit(mocker: MockFixture):
    """Test creating reminder when exceeding the maximum limit"""
    # Setup UserTimeManager mock
    setup_user_time_manager_mock(mocker)
    
    # Setup mock to return max count
    from app.core.constants import Constants
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("reminders", [
        create_mock_response(count=Constants.REMINDERS_MAX)
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440011")
    result = manager.create_reminder(
        remind_at="2024-12-25 10:00:00",
        method="notification",
        description="Should fail due to limit",
        is_recurring=False
    )

    assert "達到最大提醒" in result or "最大提醒數量上限" in result


def test_create_reminder_invalid_method():
    """Test creating reminder with invalid method"""
    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440012")
    result = manager.create_reminder(
        remind_at="2024-12-25 10:00:00",
        method="invalid-method",
        description="Test reminder",
        is_recurring=False
    )

    assert "錯誤：method 必須是" in result


def test_create_reminder_invalid_time_format(mocker: MockFixture):
    """Test creating reminder with invalid time format"""
    # Setup UserTimeManager mock but let it handle the invalid time naturally
    setup_user_time_manager_mock(mocker)
    
    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440013")
    result = manager.create_reminder(
        remind_at="invalid-time-format",
        method="notification",
        description="Test reminder",
        is_recurring=False
    )

    # UserTimeManager 的真實邏輯會處理無效時間格式
    assert "錯誤：時間格式不正確" in result or "添加提醒時發生錯誤" in result


# ========== Real Time Conversion Tests ==========

def test_time_conversion_with_different_formats(mocker: MockFixture):
    """Test that UserTimeManager can handle different time formats"""
    # Setup UserTimeManager mock
    setup_user_time_manager_mock(mocker)
    
    # Setup UserReminderManager mock
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("reminders", [
        create_mock_response(count=0),  # Count query
        create_mock_response(data=[]),  # Duplicate check
        create_mock_response(data=[create_reminder_data()])  # Insert
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440014")
    
    # Test ISO format with timezone
    result = manager.create_reminder(
        remind_at="2024-12-25T10:00:00+08:00",
        method="notification",
        description="ISO format test",
        is_recurring=False
    )
    
    assert "成功添加提醒" in result
    
    # Check that the time was converted properly
    last_insert = mock_admin.get_last_insert("reminders")
    # The UserTimeManager should convert the time to UTC
    assert "T" in last_insert["payload"]["remind_at"]  # UTC format


def test_timezone_handling_with_user_timezone(mocker: MockFixture):
    """Test that user's timezone is properly handled"""
    # Setup UserTimeManager mock with specific timezone
    mock_profiles_response = create_mock_response(data=[{
        "timezone": "America/New_York"  # Different timezone
    }])
    
    mock_time_admin = MockSupabaseAdmin()
    mock_time_admin.set_responses("profiles", [mock_profiles_response])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_time_admin)
    
    # Setup UserReminderManager mock
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("reminders", [
        create_mock_response(count=0),  # Count query
        create_mock_response(data=[]),  # Duplicate check
        create_mock_response(data=[create_reminder_data()])  # Insert
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440015")
    result = manager.create_reminder(
        remind_at="2024-12-25 10:00:00",  # Local time
        method="notification",
        description="Timezone test",
        is_recurring=False
    )
    
    assert "成功添加提醒" in result


# ========== Read Reminder Tests ==========

def test_read_reminders_success(mocker: MockFixture):
    """Test reading all reminders successfully"""
    # Setup mock data
    mock_data = [
        create_reminder_data(
            id="reminder-1",
            description="Test reminder 1",
            remind_at="2024-12-25T10:00:00Z",
            is_sent=False
        ),
        create_reminder_data(
            id="reminder-2", 
            description="Test reminder 2",
            remind_at="2024-12-26T14:00:00Z",
            method="alarm",
            is_sent=True,
            sent_at="2024-12-26T14:00:00Z"
        )
    ]
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("reminders", [
        create_mock_response(data=mock_data)
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440016")
    result = manager.read_reminders()

    assert "ID: reminder-1" in result
    assert "Test reminder 1" in result
    assert "ID: reminder-2" in result
    assert "Test reminder 2" in result


def test_read_reminders_empty(mocker: MockFixture):
    """Test reading reminders when none exist"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("reminders", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440017")
    result = manager.read_reminders()

    assert result == "No reminders found"


# ========== Update and Delete Tests ==========

def test_update_reminder_success(mocker: MockFixture):
    """Test updating a reminder successfully"""
    # Setup mock
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("reminders", [
        create_mock_response(data=[create_reminder_data(id="reminder-1")]),  # Check existence
        create_mock_response(data=[create_reminder_data(id="reminder-1")])   # Update result
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440018")
    result = manager.update_reminder(
        id="reminder-1",
        remind_at="2024-12-26T11:00:00Z",
        description="Updated reminder",
        method="alarm"
    )

    assert result == True
    
    # Check update was called
    last_update = mock_admin.get_last_update("reminders")
    assert last_update["payload"]["description"] == "Updated reminder"


def test_delete_reminder_success(mocker: MockFixture):
    """Test deleting a reminder successfully"""
    # Setup mock
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("reminders", [
        create_mock_response(data=[create_reminder_data(id="reminder-1")]),  # Check existence
        create_mock_response(data=[{"id": "reminder-1"}])  # Delete result
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440019")
    result = manager.delete_reminder("reminder-1")

    assert "成功刪除提醒記錄，ID: reminder-1" in result
    assert mock_admin.get_call_count("delete", "reminders") == 1


# ========== Search Tests ==========

def test_search_reminders_by_keyword_success(mocker: MockFixture):
    """Test searching reminders by keyword successfully"""
    mock_data = [create_reminder_data(
        id="reminder-1",
        description="Meeting with client"
    )]
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("reminders", [
        create_mock_response(data=mock_data)
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440020")
    result = manager.search_reminders_by_keyword("meeting")

    assert "ID: reminder-1" in result
    assert "Meeting with client" in result


def test_search_reminders_by_time_range_with_real_time_manager(mocker: MockFixture):
    """Test searching reminders by time range using real UserTimeManager"""
    # Setup UserTimeManager mock
    setup_user_time_manager_mock(mocker)
    
    # Setup one-time reminders response
    one_time_data = [create_reminder_data(
        id="reminder-1",
        description="One-time reminder",
        is_recurring=False
    )]
    
    # Setup recurring reminders response (empty)
    recurring_data = []
    
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("reminders", [
        create_mock_response(data=one_time_data),  # One-time reminders
        create_mock_response(data=recurring_data)  # Recurring reminders
    ])
    mocker.patch('app.lib.user_reminder_manager.supabase_admin', mock_admin)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440021")
    result = manager.search_reminders_by_time("2024-12-25 00:00:00", "2024-12-25 23:59:59")

    assert "ID: reminder-1" in result
    assert "One-time reminder" in result
    assert "Type: 一次性提醒" in result


def test_search_reminders_invalid_time_with_real_time_manager(mocker: MockFixture):
    """Test searching with invalid time using real UserTimeManager"""
    # Setup UserTimeManager mock
    setup_user_time_manager_mock(mocker)

    manager = UserReminderManager("550e8400-e29b-41d4-a716-446655440022")
    result = manager.search_reminders_by_time("invalid-start-time", "invalid-end-time")

    # Real UserTimeManager should handle invalid time gracefully
    assert "時間轉換失敗" in result or "根據時間範圍搜尋提醒時發生錯誤" in result