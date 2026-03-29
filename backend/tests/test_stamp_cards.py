"""
集點卡 API 測試
"""
import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token


class TestStampCardTemplatesAPI:
    def test_get_templates_public(self, client, test_stamp_template):
        """公開 API 可取得集點卡模板列表"""
        response = client.get("/api/v1/stamp-cards/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == "測試集點卡"

    def test_get_templates_empty(self, client):
        """無模板時回傳空陣列"""
        response = client.get("/api/v1/stamp-cards/templates")
        assert response.status_code == 200
        assert response.json() == []


class TestMyStampCardsAPI:
    def _auth_headers(self, user):
        token = create_access_token({"sub": user.id})
        return {"Authorization": f"Bearer {token}"}

    def test_get_my_cards_empty(self, client, test_user):
        """使用者尚無集點卡時回傳空陣列"""
        headers = self._auth_headers(test_user)
        response = client.get("/api/v1/stamp-cards/my", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_my_cards_with_data(self, client, test_user, test_stamp_card):
        """取得使用者的集點卡列表"""
        headers = self._auth_headers(test_user)
        response = client.get("/api/v1/stamp-cards/my", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["stamps_collected"] == 3

    def test_start_stamp_card(self, client, test_user, test_stamp_template):
        """成功開始新集點卡"""
        headers = self._auth_headers(test_user)
        response = client.post(
            "/api/v1/stamp-cards/start",
            json={"template_id": test_stamp_template.id},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stamps_collected"] == 0
        assert data["is_completed"] is False

    def test_start_duplicate_card_fails(self, client, test_user, test_stamp_card):
        """同一模板不可重複開始"""
        headers = self._auth_headers(test_user)
        response = client.post(
            "/api/v1/stamp-cards/start",
            json={"template_id": test_stamp_card.template_id},
            headers=headers,
        )
        assert response.status_code == 400

    def test_claim_completed_card(self, client, test_user, test_completed_stamp_card):
        """成功兌換已集滿的集點卡獎勵"""
        headers = self._auth_headers(test_user)
        response = client.post(
            f"/api/v1/stamp-cards/{test_completed_stamp_card.id}/claim",
            headers=headers,
        )
        assert response.status_code == 200

    def test_claim_incomplete_card_fails(self, client, test_user, test_stamp_card):
        """未集滿的集點卡不可兌換"""
        headers = self._auth_headers(test_user)
        response = client.post(
            f"/api/v1/stamp-cards/{test_stamp_card.id}/claim",
            headers=headers,
        )
        assert response.status_code == 400

    def test_unauthenticated_access_fails(self, client):
        """未登入無法存取集點卡"""
        response = client.get("/api/v1/stamp-cards/my")
        assert response.status_code == 401
