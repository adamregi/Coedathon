def test_full_auth_flow(client):
    # 1. Register student
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "student_flow@example.com",
            "password": "SecurePassword123!",
            "full_name": "Flow Student",
            "role": "student",
        },
    )
    assert reg_res.status_code == 201
    assert reg_res.json()["data"]["email"] == "student_flow@example.com"

    # 2. Duplicate registration fails with 409
    dup_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "student_flow@example.com",
            "password": "SecurePassword123!",
            "full_name": "Flow Student",
            "role": "student",
        },
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "RESOURCE_CONFLICT"

    # 3. Login with correct credentials
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "student_flow@example.com", "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()["data"]
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    assert token_data["token_type"] == "bearer"

    # 4. Access /auth/me
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == "student_flow@example.com"

    # 5. Rotate refresh token
    ref_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert ref_res.status_code == 200
    new_tokens = ref_res.json()["data"]
    new_refresh = new_tokens["refresh_token"]
    assert new_refresh != refresh_token

    # 6. Revoke token
    rev_res = client.post(
        "/api/v1/auth/revoke",
        json={"refresh_token": new_refresh},
    )
    assert rev_res.status_code == 200
    assert rev_res.json()["data"]["revoked"] is True
