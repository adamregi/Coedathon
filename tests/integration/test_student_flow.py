def test_student_profile_and_skills_flow(client, admin_headers, student_headers, student_user):
    # 1. Admin creates a skill in catalog
    skill_res = client.post(
        "/api/v1/skills",
        json={"name": "FastAPI Framework", "category": "Backend"},
        headers=admin_headers,
    )
    assert skill_res.status_code == 201
    skill_id = skill_res.json()["data"]["id"]

    # 2. Student views their own profile
    me_profile = client.get("/api/v1/students/me", headers=student_headers)
    assert me_profile.status_code == 200

    # 3. Student updates profile
    upd_res = client.put(
        "/api/v1/students/me",
        json={"headline": "Aspiring Backend Engineer", "graduation_year": 2026},
        headers=student_headers,
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["data"]["headline"] == "Aspiring Backend Engineer"

    # 4. Student adds skill with valid proficiency (1-5)
    add_skill_res = client.post(
        "/api/v1/students/me/skills",
        json={"skill_id": skill_id, "proficiency": 4},
        headers=student_headers,
    )
    assert add_skill_res.status_code == 201
    assert add_skill_res.json()["data"]["proficiency"] == 4
    assert add_skill_res.json()["data"]["skill_name"] == "FastAPI Framework"

    # 5. Invalid proficiency (> 5 or < 1) rejected
    bad_skill_res = client.post(
        "/api/v1/students/me/skills",
        json={"skill_id": skill_id, "proficiency": 6},
        headers=student_headers,
    )
    assert bad_skill_res.status_code == 422

    # 6. Student deletes skill
    del_skill_res = client.delete(
        f"/api/v1/students/me/skills/{skill_id}",
        headers=student_headers,
    )
    assert del_skill_res.status_code == 200
    assert del_skill_res.json()["data"]["deleted"] is True


def test_student_ownership_and_admin_listing(client, admin_headers, student_headers):
    # Admin can list student profiles
    list_res = client.get("/api/v1/students", headers=admin_headers)
    assert list_res.status_code == 200
    assert "data" in list_res.json()

    # Student cannot list student profiles
    forbidden_res = client.get("/api/v1/students", headers=student_headers)
    assert forbidden_res.status_code == 403
