from types import SimpleNamespace

import pytest

from app.core.constants import Constants
from app.lib.user_note_manager import UserNoteManager


class FakeSupabase:
    """Minimal Supabase stub returning predefined responses per execute call."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.select_calls = []
        self.eq_calls = []
        self.or_calls = []
        self.insert_payloads = []
        self.update_payloads = []
        self.delete_calls = 0
        self.table = None

    def from_(self, table):
        self.table = table
        return self

    def select(self, *args, **kwargs):
        self.select_calls.append((args, kwargs))
        return self

    def eq(self, *args, **kwargs):
        self.eq_calls.append((args, kwargs))
        return self

    def or_(self, condition):
        self.or_calls.append(condition)
        return self

    def insert(self, payload):
        self.insert_payloads.append(payload)
        return self

    def update(self, payload):
        self.update_payloads.append(payload)
        return self

    def delete(self):
        self.delete_calls += 1
        return self

    def execute(self):
        if not self.responses:
            raise AssertionError("No more stub responses available")
        return self.responses.pop(0)


def make_response(data=None, count=None):
    return SimpleNamespace(data=data, count=count)


def test_create_note_success(monkeypatch):
    responses = [
        make_response(data=[], count=0),  # count check
        make_response(data=[], count=None),  # duplicate check
        make_response(data=[{"id": "note-1"}], count=None),  # insert result
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr("app.lib.user_note_manager.supabase_admin", fake_supabase)

    manager = UserNoteManager("user-123")
    result = manager.create_note("Daily log", "content")

    assert "成功添加筆記" in result
    assert fake_supabase.insert_payloads[0]["title"] == "Daily log"


def test_create_note_reaches_limit(monkeypatch):
    responses = [
        make_response(data=[], count=Constants.NOTES_MAX),  # simulate reaching cap
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr("app.lib.user_note_manager.supabase_admin", fake_supabase)

    manager = UserNoteManager("user-123")
    result = manager.create_note("Daily log", "content")

    assert "無法新增筆記" in result
    assert str(Constants.NOTES_MAX) in result


def test_create_note_duplicate_title(monkeypatch):
    responses = [
        make_response(data=[], count=1),
        make_response(data=[{"id": "existing"}], count=None),
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr("app.lib.user_note_manager.supabase_admin", fake_supabase)

    manager = UserNoteManager("user-123")
    result = manager.create_note("Daily log", "content")

    assert "已存在相同" in result


def test_read_notes_returns_formatted_content(monkeypatch):
    responses = [
        make_response(
            data=[
                {
                    "id": "note-1",
                    "title": "Daily log",
                    "content": "something",
                    "created_at": "2024-01-01",
                    "updated_at": "2024-01-02",
                }
            ]
        )
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr("app.lib.user_note_manager.supabase_admin", fake_supabase)

    manager = UserNoteManager("user-123")
    result = manager.read_notes()

    assert "ID: note-1" in result
    assert "Daily log" in result


def test_read_notes_empty(monkeypatch):
    fake_supabase = FakeSupabase([make_response(data=[])])
    monkeypatch.setattr("app.lib.user_note_manager.supabase_admin", fake_supabase)

    manager = UserNoteManager("user-123")
    assert manager.read_notes() == "No notes found"


def test_read_note_success(monkeypatch):
    responses = [
        make_response(
            data=[
                {
                    "id": "note-1",
                    "title": "Daily log",
                    "content": "something",
                    "created_at": "2024-01-01",
                    "updated_at": "2024-01-02",
                }
            ]
        )
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr("app.lib.user_note_manager.supabase_admin", fake_supabase)

    manager = UserNoteManager("user-123")
    result = manager.read_note("note-1")

    assert "ID: note-1" in result
    assert "Daily log" in result


def test_read_note_not_found(monkeypatch):
    fake_supabase = FakeSupabase([make_response(data=[])])
    monkeypatch.setattr("app.lib.user_note_manager.supabase_admin", fake_supabase)

    manager = UserNoteManager("user-123")
    result = manager.read_note("missing")

    assert "找不到 ID missing" in result


def test_update_note_success(monkeypatch):
    responses = [
        make_response(data=[{"id": "note-1"}]),
        make_response(data=[{"id": "note-1"}]),
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr("app.lib.user_note_manager.supabase_admin", fake_supabase)

    manager = UserNoteManager("user-123")
    assert manager.update_note("note-1", "New title", "New content") is True
    assert fake_supabase.update_payloads[0]["title"] == "New title"


def test_update_note_not_found(monkeypatch):
    fake_supabase = FakeSupabase([make_response(data=[])])
    monkeypatch.setattr("app.lib.user_note_manager.supabase_admin", fake_supabase)

    manager = UserNoteManager("user-123")
    assert manager.update_note("missing", "Title", "Content") is False


def test_delete_note_success(monkeypatch):
    responses = [
        make_response(data=[{"id": "note-1"}]),
        make_response(data=[{"id": "note-1"}]),
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr("app.lib.user_note_manager.supabase_admin", fake_supabase)

    manager = UserNoteManager("user-123")
    result = manager.delete_note("note-1")

    assert "成功刪除筆記記錄" in result
    assert fake_supabase.delete_calls == 1


def test_delete_note_not_found(monkeypatch):
    fake_supabase = FakeSupabase([make_response(data=[])])
    monkeypatch.setattr("app.lib.user_note_manager.supabase_admin", fake_supabase)

    manager = UserNoteManager("user-123")
    result = manager.delete_note("missing")

    assert "找不到 ID missing" in result


def test_search_notes_success(monkeypatch):
    responses = [
        make_response(
            data=[
                {
                    "id": "note-1",
                    "title": "Daily log",
                    "content": "something",
                    "created_at": "2024-01-01",
                    "updated_at": "2024-01-02",
                }
            ]
        )
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr("app.lib.user_note_manager.supabase_admin", fake_supabase)

    manager = UserNoteManager("user-123")
    result = manager.search_notes("log")

    assert "Daily log" in result


def test_search_notes_no_match(monkeypatch):
    fake_supabase = FakeSupabase([make_response(data=[])])
    monkeypatch.setattr("app.lib.user_note_manager.supabase_admin", fake_supabase)

    manager = UserNoteManager("user-123")
    result = manager.search_notes("log")

    assert "沒有找到包含關鍵字" in result


def test_search_notes_by_time_success(monkeypatch):
    responses = [
        make_response(
            data=[
                {
                    "id": "note-1",
                    "title": "Daily log",
                    "content": "note",
                    "created_at": "2024-01-01T01:00:00Z",
                    "updated_at": "2024-01-02T02:00:00Z",
                }
            ]
        )
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr("app.lib.user_note_manager.supabase_admin", fake_supabase)

    conversions = iter(
        [
            ("2024-01-01T00:00:00Z", {"status": "success"}),
            ("2024-01-02T00:00:00Z", {"status": "success"}),
        ]
    )

    def fake_convert(_user_id, _value):
        return next(conversions)

    monkeypatch.setattr(
        "app.lib.user_note_manager.convert_user_local_to_utc_time",
        fake_convert,
    )

    manager = UserNoteManager("user-123")
    result = manager.search_notes_by_time("2024-01-01 08:00:00", "2024-01-02 08:00:00")

    assert "ID: note-1" in result
    assert "Daily log" in result


def test_search_notes_by_time_conversion_error(monkeypatch):
    fake_supabase = FakeSupabase([])
    monkeypatch.setattr("app.lib.user_note_manager.supabase_admin", fake_supabase)

    conversions = iter(
        [
            ("invalid", {"error": "格式錯誤"}),
            ("should-not-be-used", {"status": "success"}),
        ]
    )

    def fake_convert(_user_id, _value):
        return next(conversions)

    monkeypatch.setattr(
        "app.lib.user_note_manager.convert_user_local_to_utc_time",
        fake_convert,
    )

    manager = UserNoteManager("user-123")
    result = manager.search_notes_by_time("bad", "worse")

    assert "時間轉換失敗" in result
