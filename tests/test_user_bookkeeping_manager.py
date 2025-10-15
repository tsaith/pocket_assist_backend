import pytest
from pytest_mock import MockFixture

from app.core.constants import Constants
from app.lib.user_bookkeeping_manager import UserBookkeepingManager
from tests.mock_supabase_admin import MockSupabaseAdmin, create_mock_response


def test_create_bookkeeping_transaction_success(mocker: MockFixture):
    """Test creating a bookkeeping transaction successfully"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_categories", [
        create_mock_response(data=[{"id": "cat-123", "name": "食物", "type": "expense"}])  # Category exists
    ])
    mock_admin.set_responses("bookkeeping_transactions", [
        create_mock_response(data=[{"id": "trans-123", "amount": 100.0, "description": "Lunch"}])  # Insert
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440000")
    result = manager.create_bookkeeping_transaction("cat-123", 100.0, "Lunch")

    assert "成功添加記帳交易" in result
    assert "trans-123" in result
    
    # Verify insert was called
    last_insert = mock_admin.get_last_insert("bookkeeping_transactions")
    assert last_insert["payload"]["amount"] == 100.0
    assert last_insert["payload"]["description"] == "Lunch"
    assert last_insert["payload"]["category_id"] == "cat-123"


def test_create_bookkeeping_category_success(mocker: MockFixture):
    """Test creating a bookkeeping category successfully"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_categories", [
        create_mock_response(data=[]),  # Category doesn't exist
        create_mock_response(data=[{"id": "cat-456", "name": "薪資", "type": "income"}])  # Insert
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440001")
    result = manager.create_bookkeeping_category("薪資", "income")

    assert "成功添加記帳類別" in result
    assert "cat-456" in result
    
    # Verify insert was called
    last_insert = mock_admin.get_last_insert("bookkeeping_categories")
    assert last_insert["payload"]["name"] == "薪資"
    assert last_insert["payload"]["type"] == "income"


def test_create_bookkeeping_transaction_category_not_found(mocker: MockFixture):
    """Test creating transaction when category doesn't exist"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_categories", [
        create_mock_response(data=[])  # Category doesn't exist
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440002")
    result = manager.create_bookkeeping_transaction("non-existent-cat", 100.0, "Lunch")

    assert "找不到 ID non-existent-cat 的記帳類別" in result
    # Should not insert
    assert mock_admin.get_call_count("insert", "bookkeeping_transactions") == 0


def test_create_bookkeeping_category_invalid_type():
    """Test creating category with invalid type"""
    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440003")
    result = manager.create_bookkeeping_category("測試", "invalid_type")

    assert "類型必須是 'income' 或 'expense'" in result


def test_create_bookkeeping_category_duplicate(mocker: MockFixture):
    """Test creating duplicate category"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_categories", [
        create_mock_response(data=[{"id": "cat-1", "name": "食物", "type": "expense"}])  # Category exists
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440004")
    result = manager.create_bookkeeping_category("食物", "expense")

    assert "已存在相同的記帳類別" in result


def test_read_bookkeeping_transactions_success(mocker: MockFixture):
    """Test reading bookkeeping transactions successfully"""
    mock_data = [
        {
            "id": "record-1",
            "amount": 100.0,
            "description": "Lunch",
            "category_id": "cat-1",
            "created_at": "2024-01-01T12:00:00Z",
            "bookkeeping_categories": {"name": "食物", "type": "expense"}
        },
        {
            "id": "record-2",
            "amount": 5000.0,
            "description": "Salary",
            "category_id": "cat-2",
            "created_at": "2024-01-01T09:00:00Z",
            "bookkeeping_categories": {"name": "薪資", "type": "income"}
        }
    ]
    
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_transactions", [
        create_mock_response(data=mock_data)
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440005")
    result = manager.read_bookkeeping_transactions()

    assert "ID: record-1" in result
    assert "食物 (支出)" in result
    assert "Lunch" in result
    assert "ID: record-2" in result
    assert "薪資 (收入)" in result
    assert "Salary" in result


def test_read_bookkeeping_transactions_empty(mocker: MockFixture):
    """Test reading transactions when none exist"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_transactions", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440006")
    result = manager.read_bookkeeping_transactions()

    assert "No bookkeeping transactions found" in result


def test_read_bookkeeping_categories_success(mocker: MockFixture):
    """Test reading bookkeeping categories successfully"""
    mock_data = [
        {
            "id": "cat-1",
            "name": "食物",
            "type": "expense"
        },
        {
            "id": "cat-2",
            "name": "薪資",
            "type": "income"
        }
    ]
    
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_categories", [
        create_mock_response(data=mock_data)
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440007")
    result = manager.read_bookkeeping_categories()

    assert "ID: cat-1" in result
    assert "食物" in result
    assert "expense" in result
    assert "ID: cat-2" in result
    assert "薪資" in result
    assert "income" in result


def test_read_bookkeeping_categories_empty(mocker: MockFixture):
    """Test reading categories when none exist"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_categories", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440008")
    result = manager.read_bookkeeping_categories()

    assert "No bookkeeping categories found" in result


def test_read_single_bookkeeping_transaction_success(mocker: MockFixture):
    """Test reading a single transaction successfully"""
    mock_data = [{
        "id": "record-1",
        "amount": 100.0,
        "description": "Lunch",
        "category_id": "cat-1",
        "created_at": "2024-01-01T12:00:00Z",
        "bookkeeping_categories": {"name": "食物", "type": "expense"}
    }]
    
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_transactions", [
        create_mock_response(data=mock_data)
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440009")
    result = manager.read_bookkeeping_transaction("record-1")

    assert "ID: record-1" in result
    assert "食物 (支出)" in result
    assert "Lunch" in result


def test_read_single_bookkeeping_transaction_not_found(mocker: MockFixture):
    """Test reading a single transaction that doesn't exist"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_transactions", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440010")
    result = manager.read_bookkeeping_transaction("non-existent-id")

    assert "找不到 ID non-existent-id 的記帳交易" in result


def test_update_bookkeeping_transaction_success(mocker: MockFixture):
    """Test updating a transaction successfully"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_transactions", [
        create_mock_response(data=[{"id": "record-1"}]),  # Check existence
        create_mock_response(data=[{"id": "record-1", "amount": 120.0}])  # Update result
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440011")
    result = manager.update_bookkeeping_transaction("record-1", "cat-1", 120.0, "Updated Lunch")

    assert result == True
    
    # Check update was called
    last_update = mock_admin.get_last_update("bookkeeping_transactions")
    assert last_update["payload"]["amount"] == 120.0
    assert last_update["payload"]["description"] == "Updated Lunch"


def test_update_bookkeeping_transaction_not_found(mocker: MockFixture):
    """Test updating a transaction that doesn't exist"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_transactions", [
        create_mock_response(data=[])  # Not found
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440012")
    result = manager.update_bookkeeping_transaction("non-existent-id", "cat-1", 100.0, "Test")

    assert result == False


def test_delete_bookkeeping_transaction_success(mocker: MockFixture):
    """Test deleting a transaction successfully"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_transactions", [
        create_mock_response(data=[{"id": "record-1"}]),  # Check existence
        create_mock_response(data=[{"id": "record-1"}])  # Delete result
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440013")
    result = manager.delete_bookkeeping_transaction("record-1")

    assert "成功刪除記帳交易" in result
    assert mock_admin.get_call_count("delete", "bookkeeping_transactions") == 1


def test_delete_bookkeeping_transaction_not_found(mocker: MockFixture):
    """Test deleting a transaction that doesn't exist"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_transactions", [
        create_mock_response(data=[])  # Not found
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440014")
    result = manager.delete_bookkeeping_transaction("non-existent-id")

    assert "找不到 ID non-existent-id 的記帳交易" in result


def test_search_bookkeeping_transactions_success(mocker: MockFixture):
    """Test searching transactions by keyword successfully"""
    mock_data = [{
        "id": "record-1",
        "amount": 100.0,
        "description": "Lunch",
        "category_id": "cat-1",
        "created_at": "2024-01-01T12:00:00Z",
        "bookkeeping_categories": {"name": "食物", "type": "expense"}
    }]
    
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_transactions", [
        create_mock_response(data=mock_data)
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440015")
    result = manager.search_bookkeeping_transactions("lunch")

    assert "ID: record-1" in result
    assert "Lunch" in result


def test_search_bookkeeping_transactions_no_results(mocker: MockFixture):
    """Test searching transactions with no results"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_transactions", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440016")
    result = manager.search_bookkeeping_transactions("nonexistent")

    assert "沒有找到包含關鍵字 'nonexistent' 的記帳交易" in result


def test_search_bookkeeping_transactions_by_date_success(mocker: MockFixture):
    """Test searching transactions by date range successfully"""
    mock_data = [{
        "id": "record-1",
        "amount": 100.0,
        "description": "Lunch",
        "category_id": "cat-1",
        "date": "2024-01-15",
        "created_at": "2024-01-15T12:00:00Z",
        "bookkeeping_categories": {"name": "食物", "type": "expense"}
    }]
    
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_transactions", [
        create_mock_response(data=mock_data)
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440017")
    result = manager.search_bookkeeping_transactions_by_date("2024-01-01", "2024-01-31")

    assert "ID: record-1" in result
    assert "Lunch" in result


def test_search_bookkeeping_transactions_by_date_no_results(mocker: MockFixture):
    """Test searching transactions by date range with no results"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("bookkeeping_transactions", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.user_bookkeeping_manager.supabase_admin', mock_admin)

    manager = UserBookkeepingManager("550e8400-e29b-41d4-a716-446655440018")
    result = manager.search_bookkeeping_transactions_by_date("2024-01-01", "2024-01-31")

    assert "沒有找到在日期範圍 '2024-01-01' 到 '2024-01-31' 之間的記帳交易" in result