import pytest

from app.lib.user_subscription_manager import (
    SubscriptionFeature,
    UserSubscriptionManager,
)


def test_get_tier_caches_result(monkeypatch):
    call_count = {"count": 0}

    def fake_get_user_tier(received_user_id: str) -> str:
        call_count["count"] += 1
        assert received_user_id == "user-123"
        return "pro"

    monkeypatch.setattr(
        "app.lib.user_subscription_manager.get_user_tier",
        fake_get_user_tier,
    )

    manager = UserSubscriptionManager("user-123")

    assert manager.get_tier() == "pro"
    # Second call should reuse cached value without hitting helper again
    assert manager.get_tier() == "pro"
    assert call_count["count"] == 1


def test_refresh_tier_updates_cache(monkeypatch):
    tier_responses = iter(["free", "vip"])

    def fake_get_user_tier(_: str) -> str:
        return next(tier_responses)

    monkeypatch.setattr(
        "app.lib.user_subscription_manager.get_user_tier",
        fake_get_user_tier,
    )

    manager = UserSubscriptionManager("user-abc")

    assert manager.get_tier() == "free"
    # Refresh should fetch a new value from helper
    assert manager.refresh_tier() == "vip"
    # Cached tier should now reflect refreshed value
    assert manager.get_tier() == "vip"


def test_limit_helpers_delegate_to_subscription_limits(monkeypatch):
    captured_calls = []
    limit_results = {
        SubscriptionFeature.REMINDERS: 10,
        SubscriptionFeature.NOTES: 20,
        SubscriptionFeature.BOOKKEEPING: 30,
    }

    def fake_get_limit(feature: SubscriptionFeature, tier: str) -> int:
        captured_calls.append((feature, tier))
        return limit_results[feature]

    monkeypatch.setattr(
        "app.lib.user_subscription_manager.SubscriptionLimits.get_limit",
        fake_get_limit,
    )

    manager = UserSubscriptionManager("user-limit")
    manager.tier = "vip"

    assert manager.get_reminders_limit() == 10
    assert manager.get_notes_limit() == 20
    assert manager.get_bookkeeping_months_limit() == 30
    assert manager.get_feature_limit(SubscriptionFeature.NOTES) == 20
    assert captured_calls == [
        (SubscriptionFeature.REMINDERS, "vip"),
        (SubscriptionFeature.NOTES, "vip"),
        (SubscriptionFeature.BOOKKEEPING, "vip"),
        (SubscriptionFeature.NOTES, "vip"),
    ]


def test_is_limit_reached_uses_subscription_limits(monkeypatch):
    captured_calls = []

    def fake_is_limit_reached(
        feature: SubscriptionFeature, tier: str, current_count: int
    ) -> bool:
        captured_calls.append((feature, tier, current_count))
        return current_count >= 5

    monkeypatch.setattr(
        "app.lib.user_subscription_manager.SubscriptionLimits.is_limit_reached",
        fake_is_limit_reached,
    )

    manager = UserSubscriptionManager("user-limit-check")
    manager.tier = "free"

    assert manager.is_limit_reached(SubscriptionFeature.NOTES, 5) is True
    assert captured_calls == [
        (SubscriptionFeature.NOTES, "free", 5),
    ]


def test_get_limit_message_handles_unlimited_tier():
    manager = UserSubscriptionManager("vvip-user")
    manager.tier = "vvip"

    message = manager.get_limit_message(SubscriptionFeature.REMINDERS, current_count=999)

    assert "unlimited reminders" in message
    assert "VVIP" in message
