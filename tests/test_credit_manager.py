import sys
import types
from types import SimpleNamespace

import pytest

# Stub Supabase modules before importing credit_manager to avoid external dependency
fake_supabase_module = types.ModuleType("app.lib.supabase")
fake_supabase_admin_module = types.ModuleType("app.lib.supabase.admin")
fake_supabase_admin_module.supabase_admin = SimpleNamespace(
    table=lambda *args, **kwargs: None,
    auth=SimpleNamespace(admin=SimpleNamespace(list_users=lambda: SimpleNamespace(error=None, users=[]))),
)
fake_supabase_module.admin = fake_supabase_admin_module
sys.modules.setdefault("app.lib.supabase", fake_supabase_module)
sys.modules.setdefault("app.lib.supabase.admin", fake_supabase_admin_module)

from app.lib import credit_manager as cm
from app.lib.credit_manager import CreditManager, CreditBalance, CreditTransaction


def make_response(data=None, count=None):
    return SimpleNamespace(data=data, count=count)


class StubSupabaseAdmin:
    def __init__(self, table_responses=None, list_users_response=None):
        self.table_responses = table_responses or {}
        self.insert_calls = []
        self.update_calls = []
        self.delete_calls = []
        self.list_users_response = list_users_response or SimpleNamespace(
            error=None, users=[]
        )
        self.auth = SimpleNamespace(admin=self)

    def list_users(self):
        return self.list_users_response

    def table(self, name):
        return _StubQuery(self, name)


class _StubQuery:
    def __init__(self, admin: StubSupabaseAdmin, table_name: str):
        self.admin = admin
        self.table_name = table_name

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def range(self, *args, **kwargs):
        return self

    def insert(self, payload):
        self.admin.insert_calls.append({"table": self.table_name, "payload": payload})
        return self

    def update(self, payload):
        self.admin.update_calls.append({"table": self.table_name, "payload": payload})
        return self

    def delete(self):
        self.admin.delete_calls.append({"table": self.table_name})
        return self

    def execute(self):
        queue = self.admin.table_responses.setdefault(self.table_name, [])
        if not queue:
            raise AssertionError(f"No stub response for table '{self.table_name}'")
        return queue.pop(0)


@pytest.mark.asyncio
async def test_get_credit_balance_existing_record(monkeypatch):
    stub = StubSupabaseAdmin(
        table_responses={
            "credits": [
                make_response(data=[{"balance": 12.5, "updated_at": "2024-01-01"}])
            ]
        }
    )
    monkeypatch.setattr(cm, "supabase_admin", stub)

    result = await CreditManager.get_credit_balance("user-1")

    assert isinstance(result, CreditBalance)
    assert result.balance == 12.5
    assert result.updated_at == "2024-01-01"
    assert stub.insert_calls == []


@pytest.mark.asyncio
async def test_get_credit_balance_creates_record_when_missing(monkeypatch):
    stub = StubSupabaseAdmin(
        table_responses={
            "credits": [
                make_response(data=[]),
                make_response(data=[{"balance": 0, "updated_at": "2024-01-02"}]),
            ]
        }
    )
    monkeypatch.setattr(cm, "supabase_admin", stub)

    result = await CreditManager.get_credit_balance("user-2")

    assert result.balance == 0
    assert result.updated_at == "2024-01-02"
    assert stub.insert_calls[0]["table"] == "credits"
    assert stub.insert_calls[0]["payload"]["user_id"] == "user-2"


@pytest.mark.asyncio
async def test_get_credit_transactions_with_pagination(monkeypatch):
    transactions = [
        {
            "id": "txn-1",
            "type": "recharge",
            "amount": 5.0,
            "description": "充值",
            "meta_data": {"source": "admin"},
            "created_at": "2024-01-03T00:00:00Z",
        }
    ]
    stub = StubSupabaseAdmin(
        table_responses={
            "credit_transactions": [
                make_response(data=transactions),
                make_response(data=None, count=3),
            ]
        }
    )
    monkeypatch.setattr(cm, "supabase_admin", stub)

    response = await CreditManager.get_credit_transactions("user-3", limit=1, offset=0)

    assert len(response.transactions) == 1
    txn = response.transactions[0]
    assert isinstance(txn, CreditTransaction)
    assert txn.id == "txn-1"
    assert response.pagination == {
        "total": 3,
        "limit": 1,
        "offset": 0,
        "has_more": True,
    }


@pytest.mark.asyncio
async def test_add_transaction_rounds_amount(monkeypatch):
    stub = StubSupabaseAdmin(
        table_responses={
            "credit_transactions": [
                make_response(
                    data=[
                        {
                            "id": "txn-2",
                            "type": "recharge",
                            "amount": 1.2346,
                            "description": "desc",
                            "meta_data": {"key": "value"},
                            "created_at": "2024-01-04",
                        }
                    ]
                )
            ]
        }
    )
    monkeypatch.setattr(cm, "supabase_admin", stub)

    transaction = await CreditManager.add_transaction(
        "user-4", "recharge", 1.23456, description="desc", meta_data={"key": "value"}
    )

    assert transaction.amount == 1.2346
    payload = stub.insert_calls[0]["payload"]
    assert payload["amount"] == 1.2346
    assert payload["user_id"] == "user-4"


@pytest.mark.asyncio
async def test_update_balance_success(monkeypatch):
    stub = StubSupabaseAdmin(
        table_responses={
            "credits": [
                make_response(data=[{"balance": 20.5, "updated_at": "2024-01-05"}])
            ]
        }
    )
    monkeypatch.setattr(cm, "supabase_admin", stub)

    result = await CreditManager.update_balance("user-5", 20.5)

    assert result.balance == 20.5
    update_payload = stub.update_calls[0]["payload"]
    assert update_payload["balance"] == 20.5
    assert "updated_at" in update_payload


@pytest.mark.asyncio
async def test_consume_credits_insufficient_balance(monkeypatch):
    async def fake_get_balance(user_id):
        return CreditBalance(balance=5.0, updated_at="now")

    async def fail_update(*args, **kwargs):
        raise AssertionError("update should not be called")

    async def fail_transaction(*args, **kwargs):
        raise AssertionError("transaction should not be called")

    monkeypatch.setattr(
        CreditManager, "get_credit_balance", staticmethod(fake_get_balance)
    )
    monkeypatch.setattr(CreditManager, "update_balance", staticmethod(fail_update))
    monkeypatch.setattr(CreditManager, "add_transaction", staticmethod(fail_transaction))

    result = await CreditManager.consume_credits("user-6", 10.0)

    assert result == 5.0


@pytest.mark.asyncio
async def test_consume_credits_success(monkeypatch):
    calls = {}

    async def fake_get_balance(user_id):
        return CreditBalance(balance=10.0, updated_at="now")

    async def fake_update(user_id, new_balance):
        calls["updated_balance"] = new_balance
        return CreditBalance(balance=new_balance, updated_at="later")

    async def fake_add_transaction(user_id, transaction_type, amount, description, meta):
        calls["transaction"] = {
            "user_id": user_id,
            "type": transaction_type,
            "amount": amount,
            "description": description,
            "meta": meta,
        }
        return SimpleNamespace()

    monkeypatch.setattr(
        CreditManager, "get_credit_balance", staticmethod(fake_get_balance)
    )
    monkeypatch.setattr(CreditManager, "update_balance", staticmethod(fake_update))
    monkeypatch.setattr(
        CreditManager, "add_transaction", staticmethod(fake_add_transaction)
    )

    new_balance = await CreditManager.consume_credits(
        "user-7", 3.33335, description="use", meta_data={"from": "test"}
    )

    assert pytest.approx(new_balance, rel=1e-5) == 6.6667
    assert pytest.approx(calls["updated_balance"], rel=1e-5) == 6.6667
    assert calls["transaction"]["type"] == "consumption"
    assert pytest.approx(calls["transaction"]["amount"], rel=1e-5) == 3.3333


@pytest.mark.asyncio
async def test_recharge_credits_invalid_amount():
    with pytest.raises(Exception) as exc:
        await CreditManager.recharge_credits("user-8", 0)
    assert "充值金額必須大於 0" in str(exc.value)


@pytest.mark.asyncio
async def test_recharge_credits_success(monkeypatch):
    calls = {}

    async def fake_get_balance(user_id):
        return CreditBalance(balance=5.0, updated_at="now")

    async def fake_update(user_id, new_balance):
        calls["updated_balance"] = new_balance
        return CreditBalance(balance=new_balance, updated_at="later")

    async def fake_add_transaction(user_id, transaction_type, amount, description, meta):
        calls["transaction"] = {
            "user_id": user_id,
            "type": transaction_type,
            "amount": amount,
            "description": description,
            "meta": meta,
        }
        return SimpleNamespace()

    monkeypatch.setattr(
        CreditManager, "get_credit_balance", staticmethod(fake_get_balance)
    )
    monkeypatch.setattr(CreditManager, "update_balance", staticmethod(fake_update))
    monkeypatch.setattr(
        CreditManager, "add_transaction", staticmethod(fake_add_transaction)
    )

    updated = await CreditManager.recharge_credits(
        "user-9", 2.22225, description="admin recharge", admin_user_id="admin-1"
    )

    assert pytest.approx(updated, rel=1e-5) == 7.2222
    assert pytest.approx(calls["updated_balance"], rel=1e-5) == 7.2222
    assert calls["transaction"]["meta"]["admin_user_id"] == "admin-1"
    assert calls["transaction"]["type"] == "recharge"


@pytest.mark.asyncio
async def test_consume_credits_from_tokens_limited_by_balance(monkeypatch):
    calls = {}

    async def fake_get_balance(user_id):
        return CreditBalance(balance=1.5, updated_at="now")

    async def fake_consume(user_id, amount, description, meta):
        calls["amount"] = amount
        return 0.0

    monkeypatch.setattr(
        CreditManager, "get_credit_balance", staticmethod(fake_get_balance)
    )
    monkeypatch.setattr(
        CreditManager, "consume_credits", staticmethod(fake_consume)
    )

    remaining = await CreditManager.consume_credits_from_tokens("user-10", tokens=10000)

    assert calls["amount"] == 1.5  # capped to balance
    assert remaining == 0.0


@pytest.mark.asyncio
async def test_consume_credits_from_tokens_regular(monkeypatch):
    calls = {}

    async def fake_get_balance(user_id):
        return CreditBalance(balance=5.0, updated_at="now")

    async def fake_consume(user_id, amount, description, meta):
        calls["amount"] = amount
        calls["description"] = description
        calls["meta"] = meta
        return 4.8

    monkeypatch.setattr(
        CreditManager, "get_credit_balance", staticmethod(fake_get_balance)
    )
    monkeypatch.setattr(
        CreditManager, "consume_credits", staticmethod(fake_consume)
    )

    remaining = await CreditManager.consume_credits_from_tokens("user-11", tokens=1000)

    assert pytest.approx(calls["amount"], rel=1e-5) == 0.2
    assert "1000 tokens" in calls["description"]
    assert calls["meta"]["tokens_consumed"] == 1000
    assert remaining == 4.8


@pytest.mark.asyncio
async def test_get_user_by_email_success(monkeypatch):
    user = SimpleNamespace(id="user-12", email="test@example.com")
    stub = StubSupabaseAdmin(list_users_response=SimpleNamespace(error=None, users=[user]))
    monkeypatch.setattr(cm, "supabase_admin", stub)

    result = await CreditManager.get_user_by_email("test@example.com")

    assert result.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(monkeypatch):
    stub = StubSupabaseAdmin(
        list_users_response=SimpleNamespace(
            error=None,
            users=[SimpleNamespace(id="other", email="other@example.com")],
        )
    )
    monkeypatch.setattr(cm, "supabase_admin", stub)

    with pytest.raises(Exception) as exc:
        await CreditManager.get_user_by_email("missing@example.com")

    assert "找不到 email 為 missing@example.com 的用戶" in str(exc.value)


@pytest.mark.asyncio
async def test_get_user_by_email_error(monkeypatch):
    stub = StubSupabaseAdmin(
        list_users_response=SimpleNamespace(
            error=SimpleNamespace(message="boom"), users=[]
        )
    )
    monkeypatch.setattr(cm, "supabase_admin", stub)

    with pytest.raises(Exception) as exc:
        await CreditManager.get_user_by_email("foo@example.com")

    assert "查詢用戶時發生錯誤: boom" in str(exc.value)
