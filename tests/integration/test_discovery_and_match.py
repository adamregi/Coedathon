def test_discovery_matching_and_gated_profile_access(
    client, admin_headers, employer_headers, student_headers, student_user
):
    # 1. Admin creates skills
    skill_py = client.post(
        "/api/v1/skills",
        json={"name": "Python Language", "category": "Backend"},
        headers=admin_headers,
    ).json()["data"]["id"]

    skill_aws = client.post(
        "/api/v1/skills",
        json={"name": "AWS Cloud", "category": "Cloud"},
        headers=admin_headers,
    ).json()["data"]["id"]

    # 2. Student sets their skills: Python=4, AWS missing (0)
    client.post(
        "/api/v1/students/me/skills",
        json={"skill_id": skill_py, "proficiency": 4},
        headers=student_headers,
    )

    # 3. Employer creates a job:
    # Python: required 4, mandatory=True (weight 2) -> ratio = 4/4 = 1.0 -> 200
    # AWS: required 4, mandatory=False (weight 1) -> ratio = 0/4 = 0.0 -> 0
    # Total weight = 3, sum = 200 -> overall = round(200/3) = 67%
    job_id = client.post(
        "/api/v1/jobs",
        json={
            "title": "Cloud Backend Engineer",
            "company_name": "SkyTech",
            "description": "Backend services on AWS",
            "requirements": [
                {"skill_id": skill_py, "required_proficiency": 4, "mandatory": True},
                {"skill_id": skill_aws, "required_proficiency": 4, "mandatory": False},
            ],
        },
        headers=employer_headers,
    ).json()["data"]["id"]

    # 4. Student triggers match analysis
    analysis_res = client.post(
        f"/api/v1/analysis/jobs/{job_id}",
        headers=student_headers,
    )
    assert analysis_res.status_code == 201
    analysis_data = analysis_res.json()["data"]
    run_id = analysis_data["id"]
    assert analysis_data["overall_match_percentage"] == 67
    assert len(analysis_data["recommendations"]) == 1  # 1 recommendation for unmet AWS
    assert analysis_data["recommendations"][0]["skill_id"] == skill_aws

    # 5. Fetch recommendations via dedicated recommendations endpoint
    recs_res = client.get(
        f"/api/v1/recommendations/analysis/{run_id}",
        headers=student_headers,
    )
    assert recs_res.status_code == 200
    assert len(recs_res.json()["data"]) == 1

    # 6. Employer views candidate rankings for their job
    candidates_res = client.get(
        f"/api/v1/analysis/jobs/{job_id}/candidates",
        headers=employer_headers,
    )
    assert candidates_res.status_code == 200
    ranking = candidates_res.json()["data"]
    assert len(ranking) >= 1
    assert ranking[0]["student_id"] == student_user.id
    assert ranking[0]["overall_match_percentage"] == 67

    # 7. Gated profile access: Employer can view full student profile for candidate
    cand_profile_res = client.get(
        f"/api/v1/analysis/jobs/{job_id}/candidates/{student_user.id}/profile",
        headers=employer_headers,
    )
    assert cand_profile_res.status_code == 200
    assert cand_profile_res.json()["data"]["user_id"] == student_user.id
