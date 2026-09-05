def test_employer_job_and_requirements_flow(client, admin_headers, employer_headers, student_headers):
    # 1. Admin creates skills
    s1 = client.post(
        "/api/v1/skills",
        json={"name": "Go", "category": "Backend"},
        headers=admin_headers,
    ).json()["data"]["id"]

    s2 = client.post(
        "/api/v1/skills",
        json={"name": "PostgreSQL", "category": "Database"},
        headers=admin_headers,
    ).json()["data"]["id"]

    # 2. Employer creates job
    create_job_res = client.post(
        "/api/v1/jobs",
        json={
            "title": "Senior Systems Engineer",
            "company_name": "CloudScale Inc",
            "description": "Distributed systems engineering",
            "department": "Infrastructure",
            "requirements": [
                {"skill_id": s1, "required_proficiency": 4, "mandatory": True},
            ],
        },
        headers=employer_headers,
    )
    assert create_job_res.status_code == 201
    job_id = create_job_res.json()["data"]["id"]

    # 3. Employer adds second requirement
    add_req_res = client.post(
        f"/api/v1/jobs/{job_id}/requirements",
        json={"skill_id": s2, "required_proficiency": 3, "mandatory": False},
        headers=employer_headers,
    )
    assert add_req_res.status_code == 201
    assert add_req_res.json()["data"]["mandatory"] is False

    # 4. Student can view the job
    view_job_res = client.get(f"/api/v1/jobs/{job_id}", headers=student_headers)
    assert view_job_res.status_code == 200
    assert len(view_job_res.json()["data"]["requirements"]) == 2

    # 5. Student cannot modify the job
    unauth_mod = client.put(
        f"/api/v1/jobs/{job_id}",
        json={"title": "Hacked Title"},
        headers=student_headers,
    )
    assert unauth_mod.status_code == 403

    # 6. Employer deletes requirement
    del_req_res = client.delete(
        f"/api/v1/jobs/{job_id}/requirements/{s2}",
        headers=employer_headers,
    )
    assert del_req_res.status_code == 200
    assert del_req_res.json()["data"]["deleted"] is True
