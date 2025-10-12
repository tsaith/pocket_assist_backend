from datetime import datetime as real_datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from app.lib.utils import time_utils


@pytest.fixture
def fixed_datetime(monkeypatch):
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


def make_fake_supabase(data):
    class FakeSupabase:
        def __init__(self, payload):
            self._payload = payload

        def from_(self, _):
            return self

        def select(self, *_args, **_kwargs):
            return self

        def eq(self, *_args, **_kwargs):
            return self

        def execute(self):
            return SimpleNamespace(data=self._payload)

    return FakeSupabase(data)


def test_get_weekday_returns_expected_name(fixed_datetime):
    assert time_utils.get_weekday("Asia/Taipei") == "Monday"


def test_get_weekday_invalid_timezone_returns_error():
    result = time_utils.get_weekday("Invalid/Zone")
    assert "錯誤" in result


def test_get_date_returns_iso_today(fixed_datetime):
    assert time_utils.get_date("Asia/Taipei") == "2024-01-15"


def test_get_current_time_returns_timestamp(fixed_datetime):
    assert time_utils.get_current_time("Asia/Taipei") == "2024-01-15 10:30:45"


def test_get_user_timezone_returns_value(monkeypatch):
    monkeypatch.setattr(time_utils, "supabase_admin", make_fake_supabase([{"timezone": "Europe/Berlin"}]))
    assert time_utils.get_user_timezone("user-123") == "Europe/Berlin"


def test_get_user_timezone_missing_profile(monkeypatch):
    monkeypatch.setattr(time_utils, "supabase_admin", make_fake_supabase([]))
    result = time_utils.get_user_timezone("user-456")
    assert "找不到" in result


def test_get_relative_date_offset(fixed_datetime):
    assert time_utils.get_relative_date("Asia/Taipei", days_offset=1) == "2024-01-16"


def test_get_user_relative_date_uses_user_timezone(monkeypatch, fixed_datetime):
    monkeypatch.setattr(time_utils, "get_user_timezone", lambda _user_id: "Asia/Taipei")
    assert time_utils.get_user_relative_date("user-123", days_offset=-1) == "2024-01-14"


def test_get_user_relative_date_propagates_error(monkeypatch):
    monkeypatch.setattr(time_utils, "get_user_timezone", lambda _user_id: "找不到 user profile")
    assert time_utils.get_user_relative_date("user-123", days_offset=2) == "找不到 user profile"


def test_get_weekday_date_next_week(fixed_datetime):
    assert time_utils.get_weekday_date("Asia/Taipei", weekday=3, weeks_offset=1) == "2024-01-24"


def test_get_weekday_date_invalid_weekday():
    result = time_utils.get_weekday_date("Asia/Taipei", weekday=0)
    assert "weekday 必須在 1-7 之間" in result


def test_get_user_weekday_date(monkeypatch, fixed_datetime):
    monkeypatch.setattr(time_utils, "get_user_timezone", lambda _user_id: "Asia/Taipei")
    assert time_utils.get_user_weekday_date("user-123", weekday=1, weeks_offset=0) == "2024-01-15"


def test_convert_utc_to_local_time():
    result = time_utils.convert_utc_to_local_time("2024-01-15T02:30:00Z", "Asia/Taipei")
    assert result == "2024-01-15 10:30:00"


def test_convert_local_to_utc_time():
    result = time_utils.convert_local_to_utc_time("2024-01-15 10:30:00", "Asia/Taipei")
    assert result == "2024-01-15 02:30:00"


def test_convert_user_local_to_utc_time(monkeypatch):
    monkeypatch.setattr(
        time_utils,
        "get_user_timezone_with_info",
        lambda _user_id: ("內容", {"timezone": "Asia/Taipei"}),
    )
    utc_time, info = time_utils.convert_user_local_to_utc_time("user-123", "2024-01-15 10:30:00")
    assert utc_time == "2024-01-15 02:30:00"
    assert info["status"] == "success"
    assert info["timezone"] == "Asia/Taipei"


def test_convert_user_local_to_utc_time_error(monkeypatch):
    monkeypatch.setattr(
        time_utils,
        "get_user_timezone_with_info",
        lambda _user_id: ("錯誤", {"error": "Profile not found"}),
    )
    utc_time, info = time_utils.convert_user_local_to_utc_time("user-123", "2024-01-15 10:30:00")
    assert utc_time == "2024-01-15 10:30:00"
    assert info["error"] == "Profile not found"


def test_convert_utc_to_user_local_time(monkeypatch):
    monkeypatch.setattr(
        time_utils,
        "get_user_timezone_with_info",
        lambda _user_id: ("內容", {"timezone": "Asia/Taipei"}),
    )
    local_time, info = time_utils.convert_utc_to_user_local_time("user-123", "2024-01-15T02:30:00Z")
    assert local_time == "2024-01-15 10:30:00"
    assert info["status"] == "success"
    assert info["timezone"] == "Asia/Taipei"


def test_convert_utc_to_user_local_time_error(monkeypatch):
    monkeypatch.setattr(
        time_utils,
        "get_user_timezone_with_info",
        lambda _user_id: ("錯誤", {"error": "Profile not found"}),
    )
    local_time, info = time_utils.convert_utc_to_user_local_time("user-123", "2024-01-15T02:30:00Z")
    assert local_time == "2024-01-15T02:30:00Z"
    assert info["error"] == "Profile not found"


def test_convert_local_to_utc_date():
    result = time_utils.convert_local_to_utc_date("2024-01-15", "Asia/Tokyo")
    assert result == "2024-01-14"


def test_convert_utc_to_local_date():
    result = time_utils.convert_utc_to_local_date("2024-01-14", "Asia/Tokyo")
    assert result == "2024-01-14"


def test_convert_user_local_to_utc_date(monkeypatch):
    monkeypatch.setattr(
        time_utils,
        "get_user_timezone_with_info",
        lambda _user_id: ("內容", {"timezone": "Asia/Tokyo"}),
    )
    utc_date, info = time_utils.convert_user_local_to_utc_date("user-123", "2024-01-15")
    assert utc_date == "2024-01-14"
    assert info["status"] == "success"
    assert info["timezone"] == "Asia/Tokyo"


def test_convert_utc_to_user_local_date(monkeypatch):
    monkeypatch.setattr(
        time_utils,
        "get_user_timezone_with_info",
        lambda _user_id: ("內容", {"timezone": "Asia/Tokyo"}),
    )
    local_date, info = time_utils.convert_utc_to_user_local_date("user-123", "2024-01-14")
    assert local_date == "2024-01-14"
    assert info["status"] == "success"
    assert info["timezone"] == "Asia/Tokyo"
