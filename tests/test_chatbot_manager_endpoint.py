import pytest
from pytest_mock import MockFixture
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.chatbot_manager import router
from app.core import config
from tests.mock_supabase_admin import MockSupabaseAdmin, create_mock_response


def make_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_reset_chatbot_success(mocker: MockFixture):
    """Test successful chatbot reset"""
    client = make_client()
    mocker.patch.object(config.settings, "PRIVATE_ACCESS_TOKEN", "secret-token")
    called = {}

    def fake_reset(chatbot_id):
        called["id"] = chatbot_id
        return True

    mocker.patch(
        "app.api.v1.endpoints.chatbot_manager.chatbot_manager.reset_chatbot",
        side_effect=fake_reset,
    )

    response = client.post(
        "/api/v1/chatbot-manager/reset-chatbot",
        json={"chatbot_id": "bot-123"},
        headers={"Authorization": "Bearer secret-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "聊天機器人重設成功",
        "chatbot_id": "bot-123",
    }
    assert called["id"] == "bot-123"


def test_reset_chatbot_failure(mocker: MockFixture):
    """Test chatbot reset failure"""
    client = make_client()
    mocker.patch.object(config.settings, "PRIVATE_ACCESS_TOKEN", "secret-token")

    mocker.patch(
        "app.api.v1.endpoints.chatbot_manager.chatbot_manager.reset_chatbot",
        return_value=False,
    )

    response = client.post(
        "/api/v1/chatbot-manager/reset-chatbot",
        json={"chatbot_id": "bot-404"},
        headers={"Authorization": "Bearer secret-token"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["message"] == "聊天機器人重設失敗或不存在"


def test_reset_chatbot_missing_authorization():
    """Test missing authorization header"""
    client = make_client()
    response = client.post(
        "/api/v1/chatbot-manager/reset-chatbot",
        json={"chatbot_id": "bot-1"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "缺少 authorization header"


def test_reset_chatbot_invalid_authorization_format():
    """Test invalid authorization format"""
    client = make_client()
    response = client.post(
        "/api/v1/chatbot-manager/reset-chatbot",
        json={"chatbot_id": "bot-1"},
        headers={"Authorization": "Token abc"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "無效的 authorization 格式"


def test_reset_chatbot_invalid_token(mocker: MockFixture):
    """Test invalid JWT token"""
    client = make_client()
    mocker.patch.object(config.settings, "PRIVATE_ACCESS_TOKEN", "secret-token")

    response = client.post(
        "/api/v1/chatbot-manager/reset-chatbot",
        json={"chatbot_id": "bot-1"},
        headers={"Authorization": "Bearer wrong-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "無效的 JWT token"


def test_reset_chatbot_internal_error(mocker: MockFixture):
    """Test internal server error handling"""
    client = make_client()
    mocker.patch.object(config.settings, "PRIVATE_ACCESS_TOKEN", "secret-token")

    def boom(_):
        raise RuntimeError("炸掉了")

    mocker.patch(
        "app.api.v1.endpoints.chatbot_manager.chatbot_manager.reset_chatbot",
        side_effect=boom,
    )

    response = client.post(
        "/api/v1/chatbot-manager/reset-chatbot",
        json={"chatbot_id": "bot-1"},
        headers={"Authorization": "Bearer secret-token"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "重設聊天機器人失敗: 炸掉了"
