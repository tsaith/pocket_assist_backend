import pytest
from pytest_mock import MockFixture

from app.core.constants import Constants
from app.lib.user_note_manager import UserNoteManager
from tests.mock_supabase_admin import MockSupabaseAdmin, create_mock_response


def test_create_note_success(mocker: MockFixture):
    """Test creating a note successfully"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("notes", [
        create_mock_response(count=5),  # Current count
        create_mock_response(data=[]),  # No duplicate title
        create_mock_response(data=[{"id": "note-123", "title": "Test Note", "content": "Test content"}])  # Insert
    ])
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440000")
    result = manager.create_note("Test Note", "Test content")

    assert "Successfully created note" in result
    assert "note-123" in result
    
    # Verify insert was called
    last_insert = mock_admin.get_last_insert("notes")
    assert last_insert["payload"]["title"] == "Test Note"
    assert last_insert["payload"]["content"] == "Test content"


def test_create_note_exceeds_limit(mocker: MockFixture):
    """Test creating note when exceeding limit"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("notes", [
        create_mock_response(count=Constants.NOTES_MAX)  # At max limit
    ])
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440001")
    result = manager.create_note("Test Note", "Test content")

    assert "Cannot create note: maximum notes limit" in result
    # Should not insert
    assert mock_admin.get_call_count("insert", "notes") == 0


def test_create_note_duplicate_title(mocker: MockFixture):
    """Test creating note with duplicate title"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("notes", [
        create_mock_response(count=5),  # Current count
        create_mock_response(data=[{"id": "note-1", "title": "Test Note", "content": "Existing content"}])  # Duplicate title
    ])
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440002")
    result = manager.create_note("Test Note", "New content")

    assert "Note with same title already exists: Test Note" in result


def test_read_notes_success(mocker: MockFixture):
    """Test reading notes successfully"""
    mock_data = [
        {
            "id": "note-1",
            "title": "Note 1",
            "content": "Content 1",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z"
        },
        {
            "id": "note-2", 
            "title": "Note 2",
            "content": "Content 2",
            "created_at": "2024-01-02T10:00:00Z",
            "updated_at": "2024-01-02T10:00:00Z"
        }
    ]
    
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("notes", [
        create_mock_response(data=mock_data)
    ])
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440003")
    result = manager.read_notes()

    assert "ID: note-1" in result
    assert "Note 1" in result
    assert "ID: note-2" in result
    assert "Note 2" in result


def test_read_notes_empty(mocker: MockFixture):
    """Test reading notes when none exist"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("notes", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440004")
    result = manager.read_notes()

    assert "No notes found" in result


def test_read_single_note_success(mocker: MockFixture):
    """Test reading a single note successfully"""
    mock_data = [{
        "id": "note-1",
        "title": "Single Note",
        "content": "Single Content",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
    }]
    
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("notes", [
        create_mock_response(data=mock_data)
    ])
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440005")
    result = manager.read_note("note-1")

    assert "ID: note-1" in result
    assert "Single Note" in result
    assert "Single Content" in result


def test_read_single_note_not_found(mocker: MockFixture):
    """Test reading a single note that doesn't exist"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("notes", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440006")
    result = manager.read_note("non-existent-id")

    assert "Note with ID non-existent-id not found" in result


def test_update_note_success(mocker: MockFixture):
    """Test updating a note successfully"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("notes", [
        create_mock_response(data=[{"id": "note-1"}]),  # Check existence
        create_mock_response(data=[{"id": "note-1", "title": "Updated Title"}])  # Update result
    ])
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440007")
    result = manager.update_note("note-1", "Updated Title", "Updated Content")

    assert result == True
    
    # Check update was called
    last_update = mock_admin.get_last_update("notes")
    assert last_update["payload"]["title"] == "Updated Title"
    assert last_update["payload"]["content"] == "Updated Content"


def test_update_note_not_found(mocker: MockFixture):
    """Test updating a note that doesn't exist"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("notes", [
        create_mock_response(data=[])  # Not found
    ])
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440008")
    result = manager.update_note("non-existent-id", "Title", "Content")

    assert result == False


def test_delete_note_success(mocker: MockFixture):
    """Test deleting a note successfully"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("notes", [
        create_mock_response(data=[{"id": "note-1"}]),  # Check existence
        create_mock_response(data=[{"id": "note-1"}])  # Delete result
    ])
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440009")
    result = manager.delete_note("note-1")

    assert "Successfully deleted note" in result
    assert mock_admin.get_call_count("delete", "notes") == 1


def test_delete_note_not_found(mocker: MockFixture):
    """Test deleting a note that doesn't exist"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("notes", [
        create_mock_response(data=[])  # Not found
    ])
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440010")
    result = manager.delete_note("non-existent-id")

    assert "Note with ID non-existent-id not found" in result


def test_search_notes_success(mocker: MockFixture):
    """Test searching notes by keyword successfully"""
    mock_data = [{
        "id": "note-1",
        "title": "Meeting Notes",
        "content": "Important discussion points",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
    }]
    
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("notes", [
        create_mock_response(data=mock_data)
    ])
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440011")
    result = manager.search_notes("meeting")

    assert "ID: note-1" in result
    assert "Meeting Notes" in result


def test_search_notes_no_results(mocker: MockFixture):
    """Test searching notes by keyword with no results"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("notes", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440012")
    result = manager.search_notes("nonexistent")

    assert "No notes found containing keyword 'nonexistent'" in result


def test_search_notes_by_time_success(mocker: MockFixture):
    """Test searching notes by time range successfully"""
    mock_data = [{
        "id": "note-1",
        "title": "Time Note",
        "content": "Content created in time range",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
    }]
    
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("notes", [
        create_mock_response(data=mock_data)
    ])
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)
    
    # Mock the time conversion functions
    mocker.patch('app.lib.user_note_manager.convert_user_local_to_utc_time', 
                 side_effect=[("2024-01-01T02:00:00Z", {}), ("2024-01-31T02:00:00Z", {})])

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440013")
    result = manager.search_notes_by_time("2024-01-01 10:00:00", "2024-01-31 10:00:00")

    assert "ID: note-1" in result
    assert "Time Note" in result


def test_search_notes_by_time_no_results(mocker: MockFixture):
    """Test searching notes by time range with no results"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("notes", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)
    
    # Mock the time conversion functions
    mocker.patch('app.lib.user_note_manager.convert_user_local_to_utc_time', 
                 side_effect=[("2024-01-01T02:00:00Z", {}), ("2024-01-31T02:00:00Z", {})])

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440014")
    result = manager.search_notes_by_time("2024-01-01 10:00:00", "2024-01-31 10:00:00")

    assert "No notes found in time range '2024-01-01 10:00:00' to '2024-01-31 10:00:00'" in result


def test_search_notes_by_time_conversion_error(mocker: MockFixture):
    """Test searching notes by time range with conversion error"""
    mock_admin = MockSupabaseAdmin()
    mocker.patch('app.lib.user_note_manager.supabase_admin', mock_admin)
    
    # Mock the time conversion functions to return error
    mocker.patch('app.lib.user_note_manager.convert_user_local_to_utc_time', 
                 side_effect=[("", {"error": "Invalid time format"}), ("", {})])

    manager = UserNoteManager("550e8400-e29b-41d4-a716-446655440015")
    result = manager.search_notes_by_time("invalid-time", "2024-01-31 10:00:00")

    assert "Time conversion failed" in result