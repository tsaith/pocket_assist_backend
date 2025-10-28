from datetime import datetime as real_datetime
from zoneinfo import ZoneInfo

import pytest
from pytest_mock import MockFixture

from app.lib.utils import time_utils
from tests.mock_supabase_admin import MockSupabaseAdmin, create_mock_response


@pytest.fixture
def fixed_datetime(monkeypatch):
    """Fixture to provide fixed datetime for consistent testing"""
    class FixedDatetime(real_datetime):
        FIXED_UTC = real_datetime(2024, 1, 15, 2, 30, 45, tzinfo=ZoneInfo("UTC"))

        @classmethod
        def now(cls, tz=None):
            if tz is not None:
                return cls.FIXED_UTC.astimezone(tz)
            return cls.FIXED_UTC.replace(tzinfo=None)

    monkeypatch.setattr(time_utils, "datetime", FixedDatetime)
    yield
    monkeypatch.setattr(time_utils, "datetime", real_datetime)


def test_get_weekday_returns_expected_name(fixed_datetime):
    """Test getting weekday name for a timezone"""
    assert time_utils.get_weekday("Asia/Taipei") == "Monday"


def test_get_weekday_invalid_timezone_returns_error():
    """Test getting weekday with invalid timezone"""
    result = time_utils.get_weekday("Invalid/Zone")
    assert "Error" in result


def test_get_date_returns_iso_today(fixed_datetime):
    """Test getting date in ISO format for a timezone"""
    assert time_utils.get_date("Asia/Taipei") == "2024-01-15"


def test_get_current_time_returns_timestamp(fixed_datetime):
    """Test getting current time in timestamp format for a timezone"""
    assert time_utils.get_current_time("Asia/Taipei") == "2024-01-15 10:30:45"


def test_get_user_timezone_returns_value(mocker: MockFixture):
    """Test getting user timezone from database"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[{"timezone": "Europe/Berlin"}])
    ])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_admin)
    
    result = time_utils.get_user_timezone("user-123")
    assert result == "Europe/Berlin"


def test_get_user_timezone_missing_profile(mocker: MockFixture):
    """Test getting user timezone when profile not found"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_admin)
    
    result = time_utils.get_user_timezone("user-456")
    assert "Cannot find" in result


def test_get_user_timezone_database_error(mocker: MockFixture):
    """Test getting user timezone when database error occurs"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(error="Database connection failed")
    ])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_admin)
    
    result = time_utils.get_user_timezone("user-789")
    assert "Error" in result


def test_get_relative_date_offset(fixed_datetime):
    """Test getting relative date with offset"""
    assert time_utils.get_relative_date("Asia/Taipei", days_offset=1) == "2024-01-16"
    assert time_utils.get_relative_date("Asia/Taipei", days_offset=-1) == "2024-01-14"
    assert time_utils.get_relative_date("Asia/Taipei", days_offset=0) == "2024-01-15"


def test_get_user_relative_date_uses_user_timezone(mocker: MockFixture, fixed_datetime):
    """Test getting user relative date using user's timezone"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[{"timezone": "Asia/Taipei"}])
    ])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_admin)
    
    result = time_utils.get_user_relative_date("user-123", days_offset=-1)
    assert result == "2024-01-14"


def test_get_user_relative_date_propagates_error(mocker: MockFixture):
    """Test getting user relative date when timezone lookup fails"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_admin)
    
    result = time_utils.get_user_relative_date("user-123", days_offset=2)
    assert "Cannot find" in result


def test_get_weekday_date_next_week(fixed_datetime):
    """Test getting weekday date for next week"""
    assert time_utils.get_weekday_date("Asia/Taipei", weekday=3, weeks_offset=1) == "2024-01-24"


def test_get_weekday_date_this_week(fixed_datetime):
    """Test getting weekday date for this week"""
    assert time_utils.get_weekday_date("Asia/Taipei", weekday=1, weeks_offset=0) == "2024-01-15"


def test_get_weekday_date_last_week(fixed_datetime):
    """Test getting weekday date for last week"""
    assert time_utils.get_weekday_date("Asia/Taipei", weekday=1, weeks_offset=-1) == "2024-01-08"


def test_get_weekday_date_invalid_weekday():
    """Test getting weekday date with invalid weekday"""
    result = time_utils.get_weekday_date("Asia/Taipei", weekday=0)
    assert "weekday must be between 1-7" in result
    
    result = time_utils.get_weekday_date("Asia/Taipei", weekday=8)
    assert "weekday must be between 1-7" in result


def test_get_user_weekday_date(mocker: MockFixture, fixed_datetime):
    """Test getting user weekday date using user's timezone"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[{"timezone": "Asia/Taipei"}])
    ])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_admin)
    
    result = time_utils.get_user_weekday_date("user-123", weekday=1, weeks_offset=0)
    assert result == "2024-01-15"


def test_convert_utc_to_local_time():
    """Test converting UTC time to local time"""
    result = time_utils.convert_utc_to_local_time("2024-01-15T02:30:00Z", "Asia/Taipei")
    result_dt = real_datetime.fromisoformat(result)
    expected_dt = real_datetime(2024, 1, 15, 10, 30, tzinfo=ZoneInfo("Asia/Taipei"))
    assert result_dt == expected_dt


def test_convert_utc_to_local_time_with_timezone_info():
    """Test converting UTC time to local time with timezone info in result"""
    result = time_utils.convert_utc_to_local_time("2024-01-15T02:30:00Z", "Asia/Taipei")
    # Should include timezone info in ISO format
    assert "+08:00" in result or "Asia/Taipei" in result


def test_convert_local_to_utc_time():
    """Test converting local time to UTC time"""
    result = time_utils.convert_local_to_utc_time("2024-01-15 10:30:00", "Asia/Taipei")
    result_dt = real_datetime.fromisoformat(result.replace("Z", "+00:00"))
    expected_dt = real_datetime(2024, 1, 15, 2, 30, tzinfo=ZoneInfo("UTC"))
    assert result_dt == expected_dt


def test_convert_local_to_utc_time_with_utc_info():
    """Test converting local time to UTC time with UTC info in result"""
    result = time_utils.convert_local_to_utc_time("2024-01-15 10:30:00", "Asia/Taipei")
    # Should include UTC info in ISO format
    assert "Z" in result or "+00:00" in result


def test_convert_user_local_to_utc_time(mocker: MockFixture):
    """Test converting user local time to UTC time"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[{"timezone": "Asia/Taipei"}])
    ])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_admin)
    
    utc_time, info = time_utils.convert_user_local_to_utc_time("user-123", "2024-01-15 10:30:00")
    result_dt = real_datetime.fromisoformat(utc_time.replace("Z", "+00:00"))
    expected_dt = real_datetime(2024, 1, 15, 2, 30, tzinfo=ZoneInfo("UTC"))
    assert result_dt == expected_dt
    assert info["status"] == "success"
    assert info["timezone"] == "Asia/Taipei"


def test_convert_user_local_to_utc_time_error(mocker: MockFixture):
    """Test converting user local time to UTC time when timezone lookup fails"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_admin)
    
    utc_time, info = time_utils.convert_user_local_to_utc_time("user-123", "2024-01-15 10:30:00")
    assert utc_time == "2024-01-15 10:30:00"
    assert info["error"] is not None


def test_convert_utc_to_user_local_time(mocker: MockFixture):
    """Test converting UTC time to user local time"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[{"timezone": "Asia/Taipei"}])
    ])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_admin)
    
    local_time, info = time_utils.convert_utc_to_user_local_time("user-123", "2024-01-15T02:30:00Z")
    result_dt = real_datetime.fromisoformat(local_time)
    expected_dt = real_datetime(2024, 1, 15, 10, 30, tzinfo=ZoneInfo("Asia/Taipei"))
    assert result_dt == expected_dt
    assert info["status"] == "success"
    assert info["timezone"] == "Asia/Taipei"


def test_convert_utc_to_user_local_time_error(mocker: MockFixture):
    """Test converting UTC time to user local time when timezone lookup fails"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_admin)
    
    local_time, info = time_utils.convert_utc_to_user_local_time("user-123", "2024-01-15T02:30:00Z")
    assert local_time == "2024-01-15T02:30:00Z"
    assert info["error"] is not None


def test_convert_local_to_utc_date():
    """Test converting local date to UTC date"""
    result = time_utils.convert_local_to_utc_date("2024-01-15", "Asia/Tokyo")
    assert result == "2024-01-14"


def test_convert_utc_to_local_date():
    """Test converting UTC date to local date"""
    result = time_utils.convert_utc_to_local_date("2024-01-14", "Asia/Tokyo")
    assert result == "2024-01-14"


def test_convert_user_local_to_utc_date(mocker: MockFixture):
    """Test converting user local date to UTC date"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[{"timezone": "Asia/Tokyo"}])
    ])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_admin)
    
    utc_date, info = time_utils.convert_user_local_to_utc_date("user-123", "2024-01-15")
    assert utc_date == "2024-01-14"
    assert info["status"] == "success"
    assert info["timezone"] == "Asia/Tokyo"


def test_convert_utc_to_user_local_date(mocker: MockFixture):
    """Test converting UTC date to user local date"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[{"timezone": "Asia/Tokyo"}])
    ])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_admin)
    
    local_date, info = time_utils.convert_utc_to_user_local_date("user-123", "2024-01-14")
    assert local_date == "2024-01-14"
    assert info["status"] == "success"
    assert info["timezone"] == "Asia/Tokyo"


def test_time_conversion_edge_cases():
    """Test time conversion edge cases"""
    # Test midnight conversion
    result = time_utils.convert_utc_to_local_time("2024-01-15T00:00:00Z", "Asia/Taipei")
    assert "08:00:00" in result
    
    # Test end of day conversion
    result = time_utils.convert_utc_to_local_time("2024-01-15T23:59:59Z", "Asia/Taipei")
    assert "07:59:59" in result


def test_date_conversion_edge_cases():
    """Test date conversion edge cases"""
    # Test date boundary crossing
    result = time_utils.convert_local_to_utc_date("2024-01-01", "Pacific/Auckland")
    assert result == "2023-12-31"
    
    # Test same date
    result = time_utils.convert_local_to_utc_date("2024-01-15", "UTC")
    assert result == "2024-01-15"


def test_weekday_calculation_edge_cases(fixed_datetime):
    """Test weekday calculation edge cases"""
    # Test Sunday (weekday=7)
    result = time_utils.get_weekday_date("Asia/Taipei", weekday=7, weeks_offset=0)
    assert result == "2024-01-21"
    
    # Test Wednesday (weekday=3)
    result = time_utils.get_weekday_date("Asia/Taipei", weekday=3, weeks_offset=0)
    assert result == "2024-01-17"


def test_relative_date_edge_cases(fixed_datetime):
    """Test relative date calculation edge cases"""
    # Test month boundary
    result = time_utils.get_relative_date("Asia/Taipei", days_offset=17)
    assert result == "2024-02-01"
    
    # Test year boundary
    result = time_utils.get_relative_date("Asia/Taipei", days_offset=-15)
    assert result == "2023-12-31"