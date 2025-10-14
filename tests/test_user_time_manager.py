from app.lib.user_time_manager import UserTimeManager


def test_user_time_manager_initializes_timezone(monkeypatch):
    calls = []

    def fake_get_user_timezone(user_id):
        calls.append(user_id)
        return "Asia/Tokyo"

    monkeypatch.setattr(
        "app.lib.user_time_manager.get_user_timezone",
        fake_get_user_timezone,
    )

    manager = UserTimeManager("user-123")

    assert manager.get_timezone() == "Asia/Tokyo"
    assert calls == ["user-123"]


def test_user_time_manager_delegates_to_time_utils(monkeypatch):
    monkeypatch.setattr(
        "app.lib.user_time_manager.get_user_timezone",
        lambda _user_id: "Asia/Taipei",
    )

    captured = {}

    def record(name, value):
        captured[name] = value
        return value

    monkeypatch.setattr(
        "app.lib.user_time_manager.get_weekday",
        lambda tz: record("weekday", "Tuesday" if tz == "Asia/Taipei" else "bad"),
    )
    monkeypatch.setattr(
        "app.lib.user_time_manager.get_date",
        lambda tz: record("date", "2024-02-10" if tz == "Asia/Taipei" else "bad"),
    )
    monkeypatch.setattr(
        "app.lib.user_time_manager.get_current_time",
        lambda tz: record(
            "current_time", "2024-02-10 15:00:00" if tz == "Asia/Taipei" else "bad"
        ),
    )
    monkeypatch.setattr(
        "app.lib.user_time_manager.get_relative_date",
        lambda tz, offset: record(
            "relative",
            f"{tz}-{offset}" if tz == "Asia/Taipei" and offset == 1 else "bad",
        ),
    )
    monkeypatch.setattr(
        "app.lib.user_time_manager.get_weekday_date",
        lambda tz, weekday, weeks_offset: record(
            "weekday_date",
            f"{tz}-{weekday}-{weeks_offset}"
            if tz == "Asia/Taipei" and weekday == 3 and weeks_offset == 1
            else "bad",
        ),
    )

    manager = UserTimeManager("user-456")

    assert manager.get_weekday() == "Tuesday"
    assert manager.get_date() == "2024-02-10"
    assert manager.get_current_time() == "2024-02-10 15:00:00"
    assert manager.get_relative_date(1) == "Asia/Taipei-1"
    assert manager.get_weekday_date(3, 1) == "Asia/Taipei-3-1"


def test_user_time_manager_convert_helpers(monkeypatch):
    monkeypatch.setattr(
        "app.lib.user_time_manager.get_user_timezone",
        lambda _user_id: "Asia/Tokyo",
    )

    calls = {"local": [], "utc": []}

    def fake_convert_local(user_id, value):
        calls["local"].append((user_id, value))
        return "2024-01-01T01:00:00Z", {"status": "ok"}

    def fake_convert_utc(user_id, value):
        calls["utc"].append((user_id, value))
        return "2024-01-01T10:00:00+09:00", {"status": "ok"}

    monkeypatch.setattr(
        "app.lib.user_time_manager.convert_user_local_to_utc_time",
        fake_convert_local,
    )
    monkeypatch.setattr(
        "app.lib.user_time_manager.convert_utc_to_user_local_time",
        fake_convert_utc,
    )

    manager = UserTimeManager("user-789")

    assert (
        manager.convert_local_to_utc_time("2024-01-01 10:00:00")
        == "2024-01-01T01:00:00Z"
    )
    assert calls["local"] == [("user-789", "2024-01-01 10:00:00")]

    assert (
        manager.convert_utc_to_local_time("2024-01-01T01:00:00Z")
        == "2024-01-01T10:00:00+09:00"
    )
    assert calls["utc"] == [("user-789", "2024-01-01T01:00:00Z")]
