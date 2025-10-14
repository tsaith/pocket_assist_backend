from types import SimpleNamespace

from app.lib.user_bookkeeping_manager import UserBookkeepingManager


class FakeSupabase:
    """Generic Supabase stub that returns predetermined responses."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.insert_payloads = []
        self.update_payloads = []
        self.delete_calls = 0
        self.operations = []

    def from_(self, table):
        self.operations.append(("from", table))
        return self

    def select(self, *args, **kwargs):
        self.operations.append(("select", args, kwargs))
        return self

    def eq(self, *args, **kwargs):
        self.operations.append(("eq", args, kwargs))
        return self

    def or_(self, condition):
        self.operations.append(("or", condition))
        return self

    def gte(self, *args, **kwargs):
        self.operations.append(("gte", args, kwargs))
        return self

    def lte(self, *args, **kwargs):
        self.operations.append(("lte", args, kwargs))
        return self

    def insert(self, payload):
        self.insert_payloads.append(payload)
        self.operations.append(("insert", payload))
        return self

    def update(self, payload):
        self.update_payloads.append(payload)
        self.operations.append(("update", payload))
        return self

    def delete(self):
        self.delete_calls += 1
        self.operations.append(("delete",))
        return self

    def execute(self):
        if not self.responses:
            raise AssertionError("No stub response available for execute()")
        return self.responses.pop(0)


def make_response(data=None):
    return SimpleNamespace(data=data)


def test_create_bookkeeping_category_success(monkeypatch):
    responses = [
        make_response(data=[]),  # duplicate check
        make_response(data=[{"id": "cat-1"}]),  # insert result
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr(
        "app.lib.user_bookkeeping_manager.supabase_admin", fake_supabase
    )

    manager = UserBookkeepingManager("user-123")
    result = manager.create_bookkeeping_category("Food", "expense")

    assert "成功添加記帳類別" in result
    assert fake_supabase.insert_payloads[0] == {
        "user_id": "user-123",
        "name": "Food",
        "type": "expense",
    }


def test_create_bookkeeping_category_invalid_type(monkeypatch):
    manager = UserBookkeepingManager("user-123")
    result = manager.create_bookkeeping_category("Food", "invalid")
    assert "類型必須是" in result


def test_create_bookkeeping_category_duplicate(monkeypatch):
    responses = [
        make_response(data=[{"id": "existing"}]),
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr(
        "app.lib.user_bookkeeping_manager.supabase_admin", fake_supabase
    )

    manager = UserBookkeepingManager("user-123")
    result = manager.create_bookkeeping_category("Food", "expense")

    assert "已存在相同的記帳類別" in result


def test_read_bookkeeping_categories(monkeypatch):
    responses = [
        make_response(
            data=[{"id": "cat-1", "name": "Food", "type": "expense"}]
        ),
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr(
        "app.lib.user_bookkeeping_manager.supabase_admin", fake_supabase
    )

    manager = UserBookkeepingManager("user-123")
    result = manager.read_bookkeeping_categories()
    assert "ID: cat-1" in result
    assert "Food" in result


def test_update_bookkeeping_category_success(monkeypatch):
    responses = [
        make_response(data=[{"id": "cat-1"}]),
        make_response(data=[{"id": "cat-1"}]),
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr(
        "app.lib.user_bookkeeping_manager.supabase_admin", fake_supabase
    )

    manager = UserBookkeepingManager("user-123")
    result = manager.update_bookkeeping_category("cat-1", "Dining", "expense")

    assert result is True
    assert fake_supabase.update_payloads[0] == {
        "name": "Dining",
        "type": "expense",
    }


def test_update_bookkeeping_category_invalid_type(monkeypatch):
    manager = UserBookkeepingManager("user-123")
    assert manager.update_bookkeeping_category("cat-1", "Dining", "invalid") is False


def test_delete_bookkeeping_category_success(monkeypatch):
    responses = [
        make_response(data=[{"id": "cat-1"}]),
        make_response(data=[{"id": "cat-1"}]),
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr(
        "app.lib.user_bookkeeping_manager.supabase_admin", fake_supabase
    )

    manager = UserBookkeepingManager("user-123")
    result = manager.delete_bookkeeping_category("cat-1")

    assert "成功刪除記帳類別" in result
    assert fake_supabase.delete_calls == 1


def test_create_bookkeeping_transaction_success(monkeypatch):
    responses = [
        make_response(data=[{"id": "cat-1"}]),  # category exists
        make_response(data=[{"id": "txn-1"}]),  # insert
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr(
        "app.lib.user_bookkeeping_manager.supabase_admin", fake_supabase
    )

    manager = UserBookkeepingManager("user-123")
    result = manager.create_bookkeeping_transaction(
        "cat-1", 1200.0, "Lunch", date="2024-01-01", payment_method="card"
    )

    assert "成功添加記帳交易" in result
    assert fake_supabase.insert_payloads[-1] == {
        "user_id": "user-123",
        "category_id": "cat-1",
        "amount": 1200.0,
        "description": "Lunch",
        "date": "2024-01-01",
        "payment_method": "card",
    }


def test_create_bookkeeping_transaction_missing_category(monkeypatch):
    responses = [
        make_response(data=[]),
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr(
        "app.lib.user_bookkeeping_manager.supabase_admin", fake_supabase
    )

    manager = UserBookkeepingManager("user-123")
    result = manager.create_bookkeeping_transaction("cat-404", 50.0, "Snack")

    assert "找不到 ID cat-404 的記帳類別" in result


def test_read_bookkeeping_transactions(monkeypatch):
    responses = [
        make_response(
            data=[
                {
                    "id": "txn-1",
                    "category_id": "cat-1",
                    "amount": 250.0,
                    "description": "Dinner",
                    "payment_method": "cash",
                    "date": "2024-01-02",
                    "created_at": "2024-01-02T12:00:00Z",
                    "updated_at": "2024-01-02T12:00:00Z",
                    "bookkeeping_categories": {"name": "Food", "type": "expense"},
                }
            ]
        )
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr(
        "app.lib.user_bookkeeping_manager.supabase_admin", fake_supabase
    )

    manager = UserBookkeepingManager("user-123")
    result = manager.read_bookkeeping_transactions()

    assert "Category: Food (支出)" in result
    assert "Amount: 250.0" in result


def test_update_bookkeeping_transaction_success(monkeypatch):
    responses = [
        make_response(data=[{"id": "txn-1"}]),
        make_response(data=[{"id": "txn-1"}]),
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr(
        "app.lib.user_bookkeeping_manager.supabase_admin", fake_supabase
    )

    manager = UserBookkeepingManager("user-123")
    assert manager.update_bookkeeping_transaction(
        "txn-1", "cat-2", 500.0, "Groceries", date="2024-01-03", payment_method=""
    )
    assert fake_supabase.update_payloads[-1] == {
        "category_id": "cat-2",
        "amount": 500.0,
        "description": "Groceries",
        "date": "2024-01-03",
        "payment_method": "",
    }


def test_update_bookkeeping_transaction_not_found(monkeypatch):
    responses = [
        make_response(data=[]),
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr(
        "app.lib.user_bookkeeping_manager.supabase_admin", fake_supabase
    )

    manager = UserBookkeepingManager("user-123")
    assert (
        manager.update_bookkeeping_transaction("missing", "cat-1", 10.0, "Coffee")
        is False
    )


def test_delete_bookkeeping_transaction_not_found(monkeypatch):
    responses = [
        make_response(data=[]),
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr(
        "app.lib.user_bookkeeping_manager.supabase_admin", fake_supabase
    )

    manager = UserBookkeepingManager("user-123")
    result = manager.delete_bookkeeping_transaction("missing")

    assert "找不到 ID missing 的記帳交易" in result


def test_search_bookkeeping_transactions(monkeypatch):
    responses = [
        make_response(
            data=[
                {
                    "id": "txn-1",
                    "category_id": "cat-1",
                    "amount": 100.0,
                    "description": "Lunch",
                    "payment_method": "card",
                    "date": "2024-01-01",
                    "created_at": "2024-01-01T10:00:00Z",
                    "updated_at": "2024-01-01T10:00:00Z",
                    "bookkeeping_categories": {"name": "Food", "type": "expense"},
                }
            ]
        )
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr(
        "app.lib.user_bookkeeping_manager.supabase_admin", fake_supabase
    )

    manager = UserBookkeepingManager("user-123")
    result = manager.search_bookkeeping_transactions("Lunch")

    assert "Lunch" in result
    assert "Food (支出)" in result


def test_search_bookkeeping_transactions_by_date_no_results(monkeypatch):
    responses = [
        make_response(data=[]),
    ]
    fake_supabase = FakeSupabase(responses)
    monkeypatch.setattr(
        "app.lib.user_bookkeeping_manager.supabase_admin", fake_supabase
    )

    manager = UserBookkeepingManager("user-123")
    result = manager.search_bookkeeping_transactions_by_date(
        "2024-01-01", "2024-01-31"
    )

    assert "沒有找到在日期範圍 '2024-01-01' 到 '2024-01-31'" in result
