def test_applications_lifecycle_flow(client, employer_headers, student_headers):
    # 1. Employer creates a job
    job_id = client.post(
        "/api/v1/jobs",
        json={
            "title": "Junior Python Engineer",
            "company_name": "DevWorks",
            "description": "Entry level Python dev",
            "requirements": [],
        },
        headers=employer_headers,
    ).json()["data"]["id"]

    # 2. Student applies
    app_res = client.post(
        "/api/v1/applications",
        json={"job_id": job_id},
        headers=student_headers,
    )
    assert app_res.status_code == 201
    app_data = app_res.json()["data"]
    app_id = app_data["id"]
    assert app_data["status"] == "submitted"
    assert app_data["match_percentage_snapshot"] == 100

    # 3. Duplicate application rejected with 409
    dup_app = client.post(
        "/api/v1/applications",
        json={"job_id": job_id},
        headers=student_headers,
    )
    assert dup_app.status_code == 409
    assert dup_app.json()["error"]["code"] == "RESOURCE_CONFLICT"

    # 4. Employer transitions: submitted -> reviewed
    t1 = client.patch(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "reviewed"},
        headers=employer_headers,
    )
    assert t1.status_code == 200
    assert t1.json()["data"]["status"] == "reviewed"

    # 5. Employer transitions: reviewed -> shortlisted
    t2 = client.patch(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "shortlisted"},
        headers=employer_headers,
    )
    assert t2.status_code == 200
    assert t2.json()["data"]["status"] == "shortlisted"

    # 6. Employer attempts invalid transition: shortlisted -> submitted (rejected)
    bad_t = client.patch(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "submitted"},
        headers=employer_headers,
    )
    assert bad_t.status_code == 400
    assert bad_t.json()["error"]["code"] == "INVALID_STATE_TRANSITION"

    # 7. List applications
    list_apps = client.get("/api/v1/applications", headers=employer_headers)
    assert list_apps.status_code == 200
    assert len(list_apps.json()["data"]) >= 1
