from types import SimpleNamespace

import pytest
from pytest_mock import MockFixture

from app.lib.credit_manager import CreditManager, CreditBalance, CreditTransaction
from tests.mock_supabase_admin import MockSupabaseAdmin, create_mock_response


@pytest.mark.asyncio
async def test_get_credit_balance_existing_record(mocker: MockFixture):
    """Test getting existing credit balance"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("credits", [
        create_mock_response(data=[{"balance": 12.5, "updated_at": "2024-01-01"}])
    ])
    mocker.patch('app.lib.credit_manager.supabase_admin', mock_admin)

    result = await CreditManager.get_credit_balance("user-1")

    assert isinstance(result, CreditBalance)
    assert result.balance == 12.5
    assert result.updated_at == "2024-01-01"
    assert mock_admin.get_call_count("insert", "credits") == 0


@pytest.mark.asyncio
async def test_get_credit_balance_creates_record_when_missing(mocker: MockFixture):
    """Test creating credit balance record when missing"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("credits", [
        create_mock_response(data=[]),  # No existing record
        create_mock_response(data=[{"balance": 0, "updated_at": "2024-01-02"}])  # Created record
    ])
    mocker.patch('app.lib.credit_manager.supabase_admin', mock_admin)

    result = await CreditManager.get_credit_balance("user-2")

    assert result.balance == 0
    assert result.updated_at == "2024-01-02"
    
    # Verify insert was called
    last_insert = mock_admin.get_last_insert("credits")
    assert last_insert["payload"]["user_id"] == "user-2"
    assert last_insert["payload"]["balance"] == 0


@pytest.mark.asyncio
async def test_get_credit_balance_database_error(mocker: MockFixture):
    """Test getting credit balance when database error occurs"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("credits", [
        create_mock_response(error="Database connection failed")
    ])
    mocker.patch('app.lib.credit_manager.supabase_admin', mock_admin)

    with pytest.raises(Exception) as exc_info:
        await CreditManager.get_credit_balance("user-3")
    
    # The actual error message will be the original error
    assert "Database connection failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_credit_transactions_with_pagination(mocker: MockFixture):
    """Test getting credit transactions with pagination"""
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
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("credit_transactions", [
        create_mock_response(data=transactions),  # Transactions data
        create_mock_response(count=3)  # Total count
    ])
    mocker.patch('app.lib.credit_manager.supabase_admin', mock_admin)

    response = await CreditManager.get_credit_transactions("user-3", limit=1, offset=0)

    assert len(response.transactions) == 1
    txn = response.transactions[0]
    assert isinstance(txn, CreditTransaction)
    assert txn.id == "txn-1"
    assert txn.type == "recharge"
    assert txn.amount == 5.0
    assert response.pagination == {
        "total": 3,
        "limit": 1,
        "offset": 0,
        "has_more": True,
    }


@pytest.mark.asyncio
async def test_get_credit_transactions_empty(mocker: MockFixture):
    """Test getting credit transactions when none exist"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("credit_transactions", [
        create_mock_response(data=[]),  # No transactions
        create_mock_response(count=0)  # Total count
    ])
    mocker.patch('app.lib.credit_manager.supabase_admin', mock_admin)

    response = await CreditManager.get_credit_transactions("user-4", limit=10, offset=0)

    assert len(response.transactions) == 0
    assert response.pagination == {
        "total": 0,
        "limit": 10,
        "offset": 0,
        "has_more": False,
    }


@pytest.mark.asyncio
async def test_add_transaction_rounds_amount(mocker: MockFixture):
    """Test adding transaction with amount rounding"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("credit_transactions", [
        create_mock_response(data=[{
            "id": "txn-2",
            "type": "recharge",
            "amount": 1.2346,
            "description": "desc",
            "meta_data": {"key": "value"},
            "created_at": "2024-01-04",
        }])
    ])
    mocker.patch('app.lib.credit_manager.supabase_admin', mock_admin)

    transaction = await CreditManager.add_transaction(
        "user-4", "recharge", 1.23456, description="desc", meta_data={"key": "value"}
    )

    assert transaction.amount == 1.2346
    last_insert = mock_admin.get_last_insert("credit_transactions")
    assert last_insert["payload"]["amount"] == 1.2346
    assert last_insert["payload"]["user_id"] == "user-4"
    assert last_insert["payload"]["type"] == "recharge"


@pytest.mark.asyncio
async def test_add_transaction_database_error(mocker: MockFixture):
    """Test adding transaction when database error occurs"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("credit_transactions", [
        create_mock_response(error="Insert failed")
    ])
    mocker.patch('app.lib.credit_manager.supabase_admin', mock_admin)

    with pytest.raises(Exception) as exc_info:
        await CreditManager.add_transaction("user-5", "recharge", 10.0)
    
    # The actual error message will be the original error
    assert "Insert failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_balance_success(mocker: MockFixture):
    """Test updating balance successfully"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("credits", [
        create_mock_response(data=[{"balance": 20.5, "updated_at": "2024-01-05"}])
    ])
    mocker.patch('app.lib.credit_manager.supabase_admin', mock_admin)

    result = await CreditManager.update_balance("user-5", 20.5)

    assert result.balance == 20.5
    last_update = mock_admin.get_last_update("credits")
    assert last_update["payload"]["balance"] == 20.5
    assert "updated_at" in last_update["payload"]


@pytest.mark.asyncio
async def test_update_balance_database_error(mocker: MockFixture):
    """Test updating balance when database error occurs"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("credits", [
        create_mock_response(error="Update failed")
    ])
    mocker.patch('app.lib.credit_manager.supabase_admin', mock_admin)

    with pytest.raises(Exception) as exc_info:
        await CreditManager.update_balance("user-6", 15.0)
    
    # The actual error message will be the original error
    assert "Update failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_consume_credits_insufficient_balance(mocker: MockFixture):
    """Test consuming credits with insufficient balance"""
    async def fake_get_balance(user_id):
        return CreditBalance(balance=5.0, updated_at="now")

    async def fail_update(*args, **kwargs):
        raise AssertionError("update should not be called")

    async def fail_transaction(*args, **kwargs):
        raise AssertionError("transaction should not be called")

    mocker.patch.object(
        CreditManager, "get_credit_balance", staticmethod(fake_get_balance)
    )
    mocker.patch.object(CreditManager, "update_balance", staticmethod(fail_update))
    mocker.patch.object(CreditManager, "add_transaction", staticmethod(fail_transaction))

    result = await CreditManager.consume_credits("user-6", 10.0)

    assert result == 5.0


@pytest.mark.asyncio
async def test_consume_credits_success(mocker: MockFixture):
    """Test consuming credits successfully"""
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

    mocker.patch.object(
        CreditManager, "get_credit_balance", staticmethod(fake_get_balance)
    )
    mocker.patch.object(CreditManager, "update_balance", staticmethod(fake_update))
    mocker.patch.object(
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
    """Test recharging credits with invalid amount"""
    with pytest.raises(Exception) as exc:
        await CreditManager.recharge_credits("user-8", 0)
    assert "Recharge amount must be greater than 0" in str(exc.value)

    with pytest.raises(Exception) as exc:
        await CreditManager.recharge_credits("user-8", -5.0)
    assert "Recharge amount must be greater than 0" in str(exc.value)


@pytest.mark.asyncio
async def test_recharge_credits_success(mocker: MockFixture):
    """Test recharging credits successfully"""
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

    mocker.patch.object(
        CreditManager, "get_credit_balance", staticmethod(fake_get_balance)
    )
    mocker.patch.object(CreditManager, "update_balance", staticmethod(fake_update))
    mocker.patch.object(
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
async def test_consume_credits_from_tokens_limited_by_balance(mocker: MockFixture):
    """Test consuming credits from tokens limited by balance"""
    calls = {}

    async def fake_get_balance(user_id):
        return CreditBalance(balance=1.5, updated_at="now")

    async def fake_consume(user_id, amount, description, meta):
        calls["amount"] = amount
        return 0.0

    mocker.patch.object(
        CreditManager, "get_credit_balance", staticmethod(fake_get_balance)
    )
    mocker.patch.object(
        CreditManager, "consume_credits", staticmethod(fake_consume)
    )

    remaining = await CreditManager.consume_credits_from_tokens("user-10", tokens=10000)

    assert calls["amount"] == 1.5  # capped to balance
    assert remaining == 0.0


@pytest.mark.asyncio
async def test_consume_credits_from_tokens_regular(mocker: MockFixture):
    """Test consuming credits from tokens normally"""
    calls = {}

    async def fake_get_balance(user_id):
        return CreditBalance(balance=5.0, updated_at="now")

    async def fake_consume(user_id, amount, description, meta):
        calls["amount"] = amount
        calls["description"] = description
        calls["meta"] = meta
        return 4.8

    mocker.patch.object(
        CreditManager, "get_credit_balance", staticmethod(fake_get_balance)
    )
    mocker.patch.object(
        CreditManager, "consume_credits", staticmethod(fake_consume)
    )

    remaining = await CreditManager.consume_credits_from_tokens("user-11", tokens=1000)

    assert pytest.approx(calls["amount"], rel=1e-5) == 0.2
    assert "1000 tokens" in calls["description"]
    assert calls["meta"]["tokens_consumed"] == 1000
    assert remaining == 4.8


@pytest.mark.asyncio
async def test_get_user_by_email_success(mocker: MockFixture):
    """Test getting user by email successfully"""
    from types import SimpleNamespace
    
    mock_admin = MockSupabaseAdmin()
    mock_user = SimpleNamespace(id="user-12", email="test@example.com")
    mock_response = SimpleNamespace(
        error=None,
        users=[mock_user]
    )
    mock_admin.auth.admin.list_users.return_value = mock_response
    mocker.patch('app.lib.credit_manager.supabase_admin', mock_admin)

    result = await CreditManager.get_user_by_email("test@example.com")

    assert result.email == "test@example.com"
    assert result.id == "user-12"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(mocker: MockFixture):
    """Test getting user by email when not found"""
    from types import SimpleNamespace
    
    mock_admin = MockSupabaseAdmin()
    mock_user = SimpleNamespace(id="other", email="other@example.com")
    mock_response = SimpleNamespace(
        error=None,
        users=[mock_user]
    )
    mock_admin.auth.admin.list_users.return_value = mock_response
    mocker.patch('app.lib.credit_manager.supabase_admin', mock_admin)

    with pytest.raises(Exception) as exc:
        await CreditManager.get_user_by_email("missing@example.com")

    assert "Cannot find user with email missing@example.com" in str(exc.value)


@pytest.mark.asyncio
async def test_get_user_by_email_error(mocker: MockFixture):
    """Test getting user by email when error occurs"""
    from types import SimpleNamespace
    
    mock_admin = MockSupabaseAdmin()
    mock_error = SimpleNamespace(message="boom")
    mock_response = SimpleNamespace(
        error=mock_error,
        users=[]
    )
    mock_admin.auth.admin.list_users.return_value = mock_response
    mocker.patch('app.lib.credit_manager.supabase_admin', mock_admin)

    with pytest.raises(Exception) as exc:
        await CreditManager.get_user_by_email("foo@example.com")

    assert "Error occurred while querying user: boom" in str(exc.value)


@pytest.mark.asyncio
async def test_credit_balance_creation():
    """Test CreditBalance object creation"""
    balance = CreditBalance(balance=10.5, updated_at="2024-01-01")
    assert balance.balance == 10.5
    assert balance.updated_at == "2024-01-01"


@pytest.mark.asyncio
async def test_credit_transaction_creation():
    """Test CreditTransaction object creation"""
    transaction = CreditTransaction(
        id="txn-1",
        type="recharge",
        amount=5.0,
        description="Test recharge",
        meta_data={"source": "test"},
        created_at="2024-01-01T00:00:00Z"
    )
    assert transaction.id == "txn-1"
    assert transaction.type == "recharge"
    assert transaction.amount == 5.0
    assert transaction.description == "Test recharge"
    assert transaction.meta_data == {"source": "test"}
    assert transaction.created_at == "2024-01-01T00:00:00Z"


@pytest.mark.asyncio
async def test_consume_credits_exact_balance(mocker: MockFixture):
    """Test consuming credits with exact balance"""
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

    mocker.patch.object(
        CreditManager, "get_credit_balance", staticmethod(fake_get_balance)
    )
    mocker.patch.object(CreditManager, "update_balance", staticmethod(fake_update))
    mocker.patch.object(
        CreditManager, "add_transaction", staticmethod(fake_add_transaction)
    )

    new_balance = await CreditManager.consume_credits("user-13", 5.0)

    assert new_balance == 0.0
    assert calls["updated_balance"] == 0.0
    assert calls["transaction"]["amount"] == 5.0


@pytest.mark.asyncio
async def test_recharge_credits_zero_balance(mocker: MockFixture):
    """Test recharging credits when balance is zero"""
    calls = {}

    async def fake_get_balance(user_id):
        return CreditBalance(balance=0.0, updated_at="now")

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

    mocker.patch.object(
        CreditManager, "get_credit_balance", staticmethod(fake_get_balance)
    )
    mocker.patch.object(CreditManager, "update_balance", staticmethod(fake_update))
    mocker.patch.object(
        CreditManager, "add_transaction", staticmethod(fake_add_transaction)
    )

    updated = await CreditManager.recharge_credits("user-14", 10.0)

    assert updated == 10.0
    assert calls["updated_balance"] == 10.0
    assert calls["transaction"]["amount"] == 10.0