"""
管理後台 - 會員管理 API 測試
"""
import pytest
from app.core.security import create_access_token


class TestAdminMembersAPI:
    def _admin_headers(self, admin):
        token = create_access_token({"sub": admin.id})
        return {"Authorization": f"Bearer {token}"}

    def _user_headers(self, user):
        token = create_access_token({"sub": user.id})
        return {"Authorization": f"Bearer {token}"}

    def test_get_members_list(self, client, test_admin, test_user):
        """管理員可取得會員列表"""
        headers = self._admin_headers(test_admin)
        response = client.get("/api/v1/admin/members", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "members" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_get_members_with_search(self, client, test_admin, test_user):
        """搜尋會員名稱"""
        headers = self._admin_headers(test_admin)
        response = client.get(
            "/api/v1/admin/members",
            params={"search": "測試使用者"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_get_members_stats(self, client, test_admin, test_user):
        """取得會員統計"""
        headers = self._admin_headers(test_admin)
        response = client.get("/api/v1/admin/members/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_members" in data
        assert "new_members_this_month" in data
        assert "active_members" in data
        assert data["total_members"] >= 1

    def test_get_member_detail(self, client, test_admin, test_user):
        """取得單一會員詳情"""
        headers = self._admin_headers(test_admin)
        response = client.get(
            f"/api/v1/admin/members/{test_user.id}",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id

    def test_update_member_role(self, client, test_admin, test_user):
        """管理員可變更會員角色"""
        headers = self._admin_headers(test_admin)
        response = client.patch(
            f"/api/v1/admin/members/{test_user.id}/role",
            json={"role": "admin"},
            headers=headers,
        )
        assert response.status_code == 200

    def test_update_invalid_role_fails(self, client, test_admin, test_user):
        """無效角色回傳 400"""
        headers = self._admin_headers(test_admin)
        response = client.patch(
            f"/api/v1/admin/members/{test_user.id}/role",
            json={"role": "superuser"},
            headers=headers,
        )
        assert response.status_code == 400

    def test_export_members_csv(self, client, test_admin, test_user):
        """匯出會員 CSV"""
        headers = self._admin_headers(test_admin)
        response = client.get("/api/v1/admin/members/export", headers=headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_non_admin_access_forbidden(self, client, test_user):
        """一般使用者無法存取會員管理"""
        headers = self._user_headers(test_user)
        response = client.get("/api/v1/admin/members", headers=headers)
        assert response.status_code == 403

    def test_unauthenticated_access_fails(self, client):
        """未登入無法存取"""
        response = client.get("/api/v1/admin/members")
        assert response.status_code == 401
