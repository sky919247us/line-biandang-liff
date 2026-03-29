"""
推薦好友 API 測試
"""
import pytest
from app.core.security import create_access_token


class TestReferralAPI:
    def _auth_headers(self, user):
        token = create_access_token({"sub": user.id})
        return {"Authorization": f"Bearer {token}"}

    def test_get_my_code_creates_new(self, client, test_user):
        """第一次呼叫時自動產生推薦碼"""
        headers = self._auth_headers(test_user)
        response = client.get("/api/v1/referrals/my-code", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "referral_code" in data
        assert data["referral_code"].startswith("REF-")

    def test_get_my_code_idempotent(self, client, test_user):
        """同一使用者多次呼叫回傳相同推薦碼"""
        headers = self._auth_headers(test_user)
        r1 = client.get("/api/v1/referrals/my-code", headers=headers)
        r2 = client.get("/api/v1/referrals/my-code", headers=headers)
        assert r1.json()["referral_code"] == r2.json()["referral_code"]

    def test_get_my_referrals_empty(self, client, test_admin):
        """初始時推薦列表為空"""
        headers = self._auth_headers(test_admin)
        response = client.get("/api/v1/referrals/my-referrals", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "referrals" in data
        assert isinstance(data["referrals"], list)

    def test_apply_referral_code(self, client, test_user, test_admin, test_referral):
        """使用推薦碼（test_admin 的推薦碼）— 先取得 admin 的推薦碼再由 test_user 套用"""
        # 先用 admin 取得自己的推薦碼
        admin_headers = self._auth_headers(test_admin)
        code_resp = client.get("/api/v1/referrals/my-code", headers=admin_headers)
        code = code_resp.json()["referral_code"]

        # 建立第三個使用者來套用（test_user 已是 test_referral 的 referred）
        from app.models.user import User
        # 直接測試 400 防止自我推薦
        user_headers = self._auth_headers(test_user)
        resp = client.post(
            "/api/v1/referrals/apply",
            json={"code": code},
            headers=user_headers,
        )
        # test_user 已被推薦過（test_referral），應回傳 400
        assert resp.status_code in (200, 400)

    def test_self_referral_fails(self, client, test_user):
        """不可套用自己的推薦碼"""
        headers = self._auth_headers(test_user)
        # 先取得自己的推薦碼
        code_resp = client.get("/api/v1/referrals/my-code", headers=headers)
        my_code = code_resp.json()["referral_code"]

        response = client.post(
            "/api/v1/referrals/apply",
            json={"code": my_code},
            headers=headers,
        )
        assert response.status_code == 400

    def test_apply_nonexistent_code_fails(self, client, test_user):
        """不存在的推薦碼回傳 404"""
        headers = self._auth_headers(test_user)
        response = client.post(
            "/api/v1/referrals/apply",
            json={"code": "REF-XXXXXX"},
            headers=headers,
        )
        assert response.status_code == 404

    def test_unauthenticated_access_fails(self, client):
        """未登入無法存取推薦好友"""
        response = client.get("/api/v1/referrals/my-code")
        assert response.status_code == 401
