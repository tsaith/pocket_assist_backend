import pytest
from pytest_mock import MockFixture

from app.lib.user_time_manager import UserTimeManager
from tests.mock_supabase_admin import MockSupabaseAdmin, create_mock_response


def test_user_time_manager_initializes_timezone(mocker: MockFixture):
    """Test that UserTimeManager initializes with user timezone"""
    # Setup mock for time_utils supabase_admin (used by get_user_timezone)
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[{"timezone": "Asia/Tokyo"}])
    ])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_admin)
    
    manager = UserTimeManager("550e8400-e29b-41d4-a716-446655440000")

    assert manager.get_timezone() == "Asia/Tokyo"
    # Verify the supabase call was made
    assert mock_admin.get_call_count("select", "profiles") == 1


def test_user_time_manager_delegates_to_time_utils(mocker: MockFixture):
    """Test that UserTimeManager delegates to time_utils functions"""
    # Setup mock for time_utils supabase_admin
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[{"timezone": "Asia/Taipei"}])
    ])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_admin)

    captured = {}

    def record(name, value):
        captured[name] = value
        return value

    mocker.patch(
        "app.lib.user_time_manager.get_weekday",
        side_effect=lambda tz: record("weekday", "Tuesday" if tz == "Asia/Taipei" else "bad"),
    )
    mocker.patch(
        "app.lib.user_time_manager.get_date",
        side_effect=lambda tz: record("date", "2024-02-10" if tz == "Asia/Taipei" else "bad"),
    )
    mocker.patch(
        "app.lib.user_time_manager.get_current_time",
        side_effect=lambda tz: record(
            "current_time", "2024-02-10 15:00:00" if tz == "Asia/Taipei" else "bad"
        ),
    )
    mocker.patch(
        "app.lib.user_time_manager.get_relative_date",
        side_effect=lambda tz, offset: record(
            "relative",
            f"{tz}-{offset}" if tz == "Asia/Taipei" and offset == 1 else "bad",
        ),
    )
    mocker.patch(
        "app.lib.user_time_manager.get_weekday_date",
        side_effect=lambda tz, weekday, weeks_offset: record(
            "weekday_date",
            f"{tz}-{weekday}-{weeks_offset}"
            if tz == "Asia/Taipei" and weekday == 3 and weeks_offset == 1
            else "bad",
        ),
    )

    manager = UserTimeManager("550e8400-e29b-41d4-a716-446655440001")

    assert manager.get_weekday() == "Tuesday"
    assert manager.get_date() == "2024-02-10"
    assert manager.get_current_time() == "2024-02-10 15:00:00"
    assert manager.get_relative_date(1) == "Asia/Taipei-1"
    assert manager.get_weekday_date(3, 1) == "Asia/Taipei-3-1"


def test_user_time_manager_convert_helpers(mocker: MockFixture):
    """Test that UserTimeManager convert helpers work correctly"""
    # Setup mock for time_utils supabase_admin
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("profiles", [
        create_mock_response(data=[{"timezone": "Asia/Tokyo"}])
    ])
    mocker.patch('app.lib.utils.time_utils.supabase_admin', mock_admin)

    calls = {"local": [], "utc": []}

    def fake_convert_local(user_id, value):
        calls["local"].append((user_id, value))
        return "2024-01-01T01:00:00Z", {"status": "ok"}

    def fake_convert_utc(user_id, value):
        calls["utc"].append((user_id, value))
        return "2024-01-01T10:00:00+09:00", {"status": "ok"}

    mocker.patch(
        "app.lib.user_time_manager.convert_user_local_to_utc_time",
        side_effect=fake_convert_local,
    )
    mocker.patch(
        "app.lib.user_time_manager.convert_utc_to_user_local_time",
        side_effect=fake_convert_utc,
    )

    manager = UserTimeManager("550e8400-e29b-41d4-a716-446655440002")

    assert (
        manager.convert_local_to_utc_time("2024-01-01 10:00:00")
        == "2024-01-01T01:00:00Z"
    )
    assert calls["local"] == [("550e8400-e29b-41d4-a716-446655440002", "2024-01-01 10:00:00")]

    assert (
        manager.convert_utc_to_local_time("2024-01-01T01:00:00Z")
        == "2024-01-01T10:00:00+09:00"
    )
    assert calls["utc"] == [("550e8400-e29b-41d4-a716-446655440002", "2024-01-01T01:00:00Z")]
