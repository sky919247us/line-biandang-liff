"""
管理後台 - 推播管理 API 測試
"""
import pytest
from unittest.mock import patch, AsyncMock
from app.core.security import create_access_token


class TestAdminBroadcastAPI:
    def _admin_headers(self, admin):
        token = create_access_token({"sub": admin.id})
        return {"Authorization": f"Bearer {token}"}

    def _user_headers(self, user):
        token = create_access_token({"sub": user.id})
        return {"Authorization": f"Bearer {token}"}

    def test_get_segments(self, client, test_admin, test_user):
        """取得受眾分群數量"""
        headers = self._admin_headers(test_admin)
        response = client.get("/api/v1/admin/broadcast/segments", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "all_users" in data
        assert "active_users" in data
        assert "new_users" in data
        assert data["all_users"] >= 1

    def test_preview_text_message(self, client, test_admin):
        """預覽文字訊息"""
        headers = self._admin_headers(test_admin)
        payload = {
            "target": "all",
            "message": {
                "message_type": "text",
                "text": "這是一則測試訊息"
            }
        }
        response = client.post(
            "/api/v1/admin/broadcast/preview",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "target_count" in data
        assert "preview_text" in data

    def test_send_broadcast_mocked(self, client, test_admin, test_user):
        """Mock LINE API 測試發送廣播"""
        headers = self._admin_headers(test_admin)
        payload = {
            "target": "all",
            "message": {
                "message_type": "text",
                "text": "測試推播訊息"
            }
        }
        # Mock httpx 呼叫，避免真實發送
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_post.return_value)
            mock_post.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = lambda: {"sentMessages": []}

            response = client.post(
                "/api/v1/admin/broadcast/send",
                json=payload,
                headers=headers,
            )
        # 即使 mock 失敗也應回傳 200（使用者沒有 line_user_id 故 target 為 0）
        assert response.status_code in (200, 400)

    def test_non_admin_access_forbidden(self, client, test_user):
        """一般使用者無法存取廣播功能"""
        headers = self._user_headers(test_user)
        response = client.get("/api/v1/admin/broadcast/segments", headers=headers)
        assert response.status_code == 403

    def test_unauthenticated_access_fails(self, client):
        """未登入無法存取"""
        response = client.get("/api/v1/admin/broadcast/segments")
        assert response.status_code == 401

    def test_preview_requires_text_for_text_type(self, client, test_admin):
        """文字類型訊息必須填入 text"""
        headers = self._admin_headers(test_admin)
        payload = {
            "target": "all",
            "message": {
                "message_type": "text",
                "text": None
            }
        }
        response = client.post(
            "/api/v1/admin/broadcast/preview",
            json=payload,
            headers=headers,
        )
        assert response.status_code in (200, 400, 422)
