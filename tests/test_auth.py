import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_auth_default_admin_login():
    """Default seeded admin should be able to log in."""
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@agent101.ai",
        "password": "admin123"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert "token" in data
    assert data["user"]["role"] == "admin"
    assert data["user"]["email"] == "admin@agent101.ai"


def test_auth_default_user_login():
    """Default seeded user should be able to log in."""
    res = client.post("/api/v1/auth/login", json={
        "email": "user@agent101.ai",
        "password": "user123"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert "token" in data
    assert data["user"]["role"] == "user"


def test_auth_login_invalid_credentials():
    """Bad credentials should return 401."""
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@agent101.ai",
        "password": "wrongpassword"
    })
    assert res.status_code == 401


def test_auth_register_and_me_flow():
    """Any new user should be able to register and access their profile."""
    # 1. Register new user
    res = client.post("/api/v1/auth/register", json={
        "username": "tester_bob",
        "email": "bob@example.com",
        "password": "supersecurepassword",
        "full_name": "Bob Tester",
        "role": "user"
    })
    assert res.status_code == 200, res.text
    reg_data = res.json()
    assert "token" in reg_data
    token = reg_data["token"]
    assert reg_data["user"]["role"] == "user"
    assert reg_data["user"]["username"] == "tester_bob"

    # 2. Get profile with Bearer token
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "bob@example.com"
    assert me_data["role"] == "user"

    # 3. Duplicate email registration rejected
    dup_res = client.post("/api/v1/auth/register", json={
        "username": "tester_bob2",
        "email": "bob@example.com",
        "password": "supersecurepassword",
    })
    assert dup_res.status_code == 400


def test_auth_rbac_admin_vs_user():
    """Regular user cannot access admin /users directory, but admin can."""
    # User token
    u_res = client.post("/api/v1/auth/login", json={
        "email": "user@agent101.ai",
        "password": "user123"
    })
    user_token = u_res.json()["token"]

    # Admin token
    a_res = client.post("/api/v1/auth/login", json={
        "email": "admin@agent101.ai",
        "password": "admin123"
    })
    admin_token = a_res.json()["token"]

    # User attempts to list users -> 403 Forbidden
    forbidden_res = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {user_token}"})
    assert forbidden_res.status_code == 403

    # Admin lists users -> 200 OK
    admin_res = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200
    users_list = admin_res.json()["users"]
    assert len(users_list) >= 2


def test_auth_logout():
    """Logging out should invalidate the session."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "user@agent101.ai",
        "password": "user123"
    })
    token = login_res.json()["token"]

    # Logout
    logout_res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200

    # Token no longer valid
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 401


def test_public_admin_registration_prevented():
    """Public registrations requesting admin role must be rejected."""
    res = client.post("/api/v1/auth/register", json={
        "username": "rogue_admin",
        "email": "rogue@example.com",
        "password": "password123",
        "role": "admin"
    })
    assert res.status_code == 400


def test_admin_analytics_and_health_access():
    """Admin can fetch system analytics & token metrics, while standard user cannot."""
    # User token
    u_res = client.post("/api/v1/auth/login", json={
        "email": "user@agent101.ai",
        "password": "user123"
    })
    user_token = u_res.json()["token"]

    # Admin token
    a_res = client.post("/api/v1/auth/login", json={
        "email": "admin@agent101.ai",
        "password": "admin123"
    })
    admin_token = a_res.json()["token"]

    # User forbidden
    u_analytics = client.get("/api/v1/auth/admin/analytics", headers={"Authorization": f"Bearer {user_token}"})
    assert u_analytics.status_code == 403

    # Admin allowed
    a_analytics = client.get("/api/v1/auth/admin/analytics", headers={"Authorization": f"Bearer {admin_token}"})
    assert a_analytics.status_code == 200
    data = a_analytics.json()
    assert "account_health" in data
    assert "metrics" in data
    assert "recent_events" in data
    assert data["metrics"]["total_tokens"] > 0


def test_admin_user_lifecycle_and_safety_checks():
    """Admin can provision users, update roles, reset passwords, and safety rules prevent self-destruction."""
    a_res = client.post("/api/v1/auth/login", json={
        "email": "admin@agent101.ai",
        "password": "admin123"
    })
    admin_token = a_res.json()["token"]
    admin_id = a_res.json()["user"]["id"]

    # 1. Admin creates user
    create_res = client.post("/api/v1/auth/admin/users", json={
        "username": "managed_dev",
        "email": "managed@agent101.ai",
        "password": "temporarypassword123",
        "full_name": "Managed Developer",
        "role": "user"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert create_res.status_code == 200
    dev_id = create_res.json()["id"]

    # 2. Admin promotes user to admin
    role_res = client.patch(f"/api/v1/auth/admin/users/{dev_id}/role", json={
        "role": "admin"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert role_res.status_code == 200
    assert role_res.json()["role"] == "admin"

    # 3. Admin self-demotion prevented
    self_demote = client.patch(f"/api/v1/auth/admin/users/{admin_id}/role", json={
        "role": "user"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert self_demote.status_code == 400

    # 4. Admin self-deletion prevented
    self_delete = client.delete(f"/api/v1/auth/admin/users/{admin_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert self_delete.status_code == 400

    # 5. Admin resets password
    reset_res = client.post(f"/api/v1/auth/admin/users/{dev_id}/reset-password", json={
        "new_password": "brandnewpassword999"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert reset_res.status_code == 200

    # 6. Admin deletes created user
    del_res = client.delete(f"/api/v1/auth/admin/users/{dev_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_res.status_code == 200

