def test_health_success_envelope(client):
    response = client.get("/health", headers={"X-Correlation-ID": "test-corr-123"})
    assert response.status_code == 200

    json_body = response.json()
    assert "data" in json_body
    assert "meta" in json_body
    assert "error" in json_body
    assert json_body["error"] is None
    assert json_body["data"]["status"] == "ok"
    assert json_body["meta"]["correlation_id"] == "test-corr-123"

    assert response.headers.get("X-Correlation-ID") == "test-corr-123"
    assert "X-Process-Time" in response.headers


def test_unauthenticated_error_envelope(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

    json_body = response.json()
    assert json_body["data"] is None
    assert json_body["error"]["code"] == "UNAUTHENTICATED"
    assert "message" in json_body["error"]
    assert "correlation_id" in json_body["meta"]


def test_permission_denied_error_envelope(client, student_headers):
    # Student attempting to create a skill in admin catalog
    response = client.post(
        "/api/v1/skills",
        json={"name": "New Skill", "category": "General"},
        headers=student_headers,
    )
    assert response.status_code == 403

    json_body = response.json()
    assert json_body["data"] is None
    assert json_body["error"]["code"] == "PERMISSION_DENIED"


def test_resource_not_found_error_envelope(client, student_headers):
    response = client.get("/api/v1/jobs/99999", headers=student_headers)
    assert response.status_code == 404

    json_body = response.json()
    assert json_body["data"] is None
    assert json_body["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_validation_error_envelope(client):
    # Invalid registration request (short password, invalid email)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "short", "full_name": ""},
    )
    assert response.status_code == 422

    json_body = response.json()
    assert json_body["data"] is None
    assert json_body["error"]["code"] == "VALIDATION_ERROR"
    assert len(json_body["error"]["details"]) > 0
