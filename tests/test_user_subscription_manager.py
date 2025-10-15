import pytest
from pytest_mock import MockFixture

from app.lib.user_subscription_manager import (
    SubscriptionFeature,
    SubscriptionLimits,
    UserSubscriptionManager,
    get_user_tier,
)
from tests.mock_supabase_admin import MockSupabaseAdmin, create_mock_response


def test_get_user_tier_success(mocker: MockFixture):
    """Test getting user tier successfully"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("subscriptions", [
        create_mock_response(data=[{"tier": "pro"}])
    ])
    mocker.patch('app.lib.user_subscription_manager.supabase_admin', mock_admin)

    result = get_user_tier("user-123")
    assert result == "pro"


def test_get_user_tier_not_found(mocker: MockFixture):
    """Test getting user tier when profile not found"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("subscriptions", [
        create_mock_response(data=[])
    ])
    mocker.patch('app.lib.user_subscription_manager.supabase_admin', mock_admin)

    result = get_user_tier("user-456")
    assert result == "free"  # Default tier


def test_get_user_tier_database_error(mocker: MockFixture):
    """Test getting user tier when database error occurs"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("subscriptions", [
        create_mock_response(error="Database connection failed")
    ])
    mocker.patch('app.lib.user_subscription_manager.supabase_admin', mock_admin)

    result = get_user_tier("user-789")
    assert result == "free"  # Default tier on error


def test_subscription_limits_get_limit():
    """Test SubscriptionLimits.get_limit method"""
    # Test free tier limits
    assert SubscriptionLimits.get_limit(SubscriptionFeature.REMINDERS, "free") == 5
    assert SubscriptionLimits.get_limit(SubscriptionFeature.NOTES, "free") == 5
    assert SubscriptionLimits.get_limit(SubscriptionFeature.BOOKKEEPING, "free") == 3
    
    # Test pro tier limits
    assert SubscriptionLimits.get_limit(SubscriptionFeature.REMINDERS, "pro") == 30
    assert SubscriptionLimits.get_limit(SubscriptionFeature.NOTES, "pro") == 50
    assert SubscriptionLimits.get_limit(SubscriptionFeature.BOOKKEEPING, "pro") == 12
    
    # Test vip tier limits
    assert SubscriptionLimits.get_limit(SubscriptionFeature.REMINDERS, "vip") == 100
    assert SubscriptionLimits.get_limit(SubscriptionFeature.NOTES, "vip") == 200
    assert SubscriptionLimits.get_limit(SubscriptionFeature.BOOKKEEPING, "vip") == 36
    
    # Test vvip tier limits (unlimited)
    assert SubscriptionLimits.get_limit(SubscriptionFeature.REMINDERS, "vvip") == -1
    assert SubscriptionLimits.get_limit(SubscriptionFeature.NOTES, "vvip") == -1
    assert SubscriptionLimits.get_limit(SubscriptionFeature.BOOKKEEPING, "vvip") == -1


def test_subscription_limits_is_limit_reached():
    """Test SubscriptionLimits.is_limit_reached method"""
    # Test free tier limits
    assert SubscriptionLimits.is_limit_reached(SubscriptionFeature.REMINDERS, "free", 5) == True
    assert SubscriptionLimits.is_limit_reached(SubscriptionFeature.REMINDERS, "free", 4) == False
    
    # Test pro tier limits
    assert SubscriptionLimits.is_limit_reached(SubscriptionFeature.NOTES, "pro", 50) == True
    assert SubscriptionLimits.is_limit_reached(SubscriptionFeature.NOTES, "pro", 49) == False
    
    # Test vvip tier (unlimited)
    assert SubscriptionLimits.is_limit_reached(SubscriptionFeature.REMINDERS, "vvip", 999) == False


def test_subscription_limits_get_limit_message():
    """Test SubscriptionLimits.get_limit_message method"""
    # Test free tier message
    message = SubscriptionLimits.get_limit_message(SubscriptionFeature.REMINDERS, "free", 5)
    assert "FREE subscription" in message
    assert "5 reminders" in message
    
    # Test pro tier message
    message = SubscriptionLimits.get_limit_message(SubscriptionFeature.NOTES, "pro", 50)
    assert "PRO subscription" in message
    assert "50 notes" in message
    
    # Test vvip tier message
    message = SubscriptionLimits.get_limit_message(SubscriptionFeature.REMINDERS, "vvip", 999)
    assert "unlimited reminders" in message
    assert "VVIP" in message


def test_user_subscription_manager_get_tier_caches_result(mocker: MockFixture):
    """Test that get_tier caches the result from get_user_tier"""
    call_count = {"count": 0}

    def fake_get_user_tier(received_user_id: str) -> str:
        call_count["count"] += 1
        assert received_user_id == "user-123"
        return "pro"

    mocker.patch(
        "app.lib.user_subscription_manager.get_user_tier",
        side_effect=fake_get_user_tier,
    )

    manager = UserSubscriptionManager("user-123")

    assert manager.get_tier() == "pro"
    # Second call should reuse cached value without hitting helper again
    assert manager.get_tier() == "pro"
    assert call_count["count"] == 1


def test_user_subscription_manager_refresh_tier_updates_cache(mocker: MockFixture):
    """Test that refresh_tier updates the cached tier value"""
    tier_responses = iter(["free", "vip"])

    def fake_get_user_tier(_: str) -> str:
        return next(tier_responses)

    mocker.patch(
        "app.lib.user_subscription_manager.get_user_tier",
        side_effect=fake_get_user_tier,
    )

    manager = UserSubscriptionManager("user-abc")

    assert manager.get_tier() == "free"
    # Refresh should fetch a new value from helper
    assert manager.refresh_tier() == "vip"
    # Cached tier should now reflect refreshed value
    assert manager.get_tier() == "vip"


def test_user_subscription_manager_get_reminders_limit():
    """Test getting reminders limit for different tiers"""
    manager = UserSubscriptionManager("user-123")
    
    # Test free tier
    manager.tier = "free"
    assert manager.get_reminders_limit() == 5
    
    # Test pro tier
    manager.tier = "pro"
    assert manager.get_reminders_limit() == 30
    
    # Test vip tier
    manager.tier = "vip"
    assert manager.get_reminders_limit() == 100
    
    # Test vvip tier
    manager.tier = "vvip"
    assert manager.get_reminders_limit() == -1


def test_user_subscription_manager_get_notes_limit():
    """Test getting notes limit for different tiers"""
    manager = UserSubscriptionManager("user-123")
    
    # Test free tier
    manager.tier = "free"
    assert manager.get_notes_limit() == 5
    
    # Test pro tier
    manager.tier = "pro"
    assert manager.get_notes_limit() == 50
    
    # Test vip tier
    manager.tier = "vip"
    assert manager.get_notes_limit() == 200
    
    # Test vvip tier
    manager.tier = "vvip"
    assert manager.get_notes_limit() == -1


def test_user_subscription_manager_get_bookkeeping_months_limit():
    """Test getting bookkeeping months limit for different tiers"""
    manager = UserSubscriptionManager("user-123")
    
    # Test free tier
    manager.tier = "free"
    assert manager.get_bookkeeping_months_limit() == 3
    
    # Test pro tier
    manager.tier = "pro"
    assert manager.get_bookkeeping_months_limit() == 12
    
    # Test vip tier
    manager.tier = "vip"
    assert manager.get_bookkeeping_months_limit() == 36
    
    # Test vvip tier
    manager.tier = "vvip"
    assert manager.get_bookkeeping_months_limit() == -1


def test_user_subscription_manager_get_feature_limit():
    """Test getting feature limit for different features and tiers"""
    manager = UserSubscriptionManager("user-123")
    
    # Test reminders feature
    manager.tier = "pro"
    assert manager.get_feature_limit(SubscriptionFeature.REMINDERS) == 30
    
    # Test notes feature
    assert manager.get_feature_limit(SubscriptionFeature.NOTES) == 50
    
    # Test bookkeeping feature
    assert manager.get_feature_limit(SubscriptionFeature.BOOKKEEPING) == 12


def test_user_subscription_manager_is_limit_reached():
    """Test checking if limit is reached for different features and tiers"""
    manager = UserSubscriptionManager("user-123")
    
    # Test free tier limits
    manager.tier = "free"
    assert manager.is_limit_reached(SubscriptionFeature.REMINDERS, 5) == True
    assert manager.is_limit_reached(SubscriptionFeature.REMINDERS, 4) == False
    
    # Test pro tier limits
    manager.tier = "pro"
    assert manager.is_limit_reached(SubscriptionFeature.NOTES, 50) == True
    assert manager.is_limit_reached(SubscriptionFeature.NOTES, 49) == False
    
    # Test vvip tier (unlimited)
    manager.tier = "vvip"
    assert manager.is_limit_reached(SubscriptionFeature.REMINDERS, 999) == False


def test_user_subscription_manager_get_limit_message():
    """Test getting limit message for different features and tiers"""
    manager = UserSubscriptionManager("user-123")
    
    # Test free tier message
    manager.tier = "free"
    message = manager.get_limit_message(SubscriptionFeature.REMINDERS, 5)
    assert "FREE subscription" in message
    assert "5 reminders" in message
    
    # Test pro tier message
    manager.tier = "pro"
    message = manager.get_limit_message(SubscriptionFeature.NOTES, 50)
    assert "PRO subscription" in message
    assert "50 notes" in message
    
    # Test vvip tier message
    manager.tier = "vvip"
    message = manager.get_limit_message(SubscriptionFeature.REMINDERS, 999)
    assert "unlimited reminders" in message
    assert "VVIP" in message


def test_user_subscription_manager_integration_with_database(mocker: MockFixture):
    """Test UserSubscriptionManager integration with database"""
    mock_admin = MockSupabaseAdmin()
    mock_admin.set_responses("subscriptions", [
        create_mock_response(data=[{"tier": "vip"}])
    ])
    mocker.patch('app.lib.user_subscription_manager.supabase_admin', mock_admin)

    manager = UserSubscriptionManager("user-123")
    
    # Test that manager fetches tier from database
    assert manager.get_tier() == "vip"
    
    # Test that limits are calculated correctly based on fetched tier
    assert manager.get_reminders_limit() == 100
    assert manager.get_notes_limit() == 200
    assert manager.get_bookkeeping_months_limit() == 36  # Updated to match actual limits
    
    # Test limit checking
    assert manager.is_limit_reached(SubscriptionFeature.REMINDERS, 100) == True
    assert manager.is_limit_reached(SubscriptionFeature.REMINDERS, 99) == False