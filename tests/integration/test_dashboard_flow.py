def test_dashboard_aggregates_and_role_permissions(
    client, admin_headers, employer_headers, student_headers
):
    # 1. Student dashboard access
    student_dash = client.get("/api/v1/dashboard/student", headers=student_headers)
    assert student_dash.status_code == 200
    s_data = student_dash.json()["data"]
    assert "total_applications" in s_data
    assert "average_match_percentage" in s_data
    assert "top_skill_gaps" in s_data

    # 2. Employer dashboard access
    emp_dash = client.get("/api/v1/dashboard/employer", headers=employer_headers)
    assert emp_dash.status_code == 200
    e_data = emp_dash.json()["data"]
    assert "total_jobs" in e_data
    assert "active_jobs" in e_data
    assert "total_candidates" in e_data

    # 3. Admin dashboard access
    admin_dash = client.get("/api/v1/dashboard/admin", headers=admin_headers)
    assert admin_dash.status_code == 200
    a_data = admin_dash.json()["data"]
    assert "total_users" in a_data
    assert "total_students" in a_data
    assert "total_employers" in a_data
    assert "platform_average_match" in a_data
    assert "top_demanded_skills" in a_data

    # 4. Role enforcement / cross-role rejection
    # Student cannot view admin or employer dashboard
    assert client.get("/api/v1/dashboard/admin", headers=student_headers).status_code == 403
    assert client.get("/api/v1/dashboard/employer", headers=student_headers).status_code == 403

    # Employer cannot view admin dashboard
    assert client.get("/api/v1/dashboard/admin", headers=employer_headers).status_code == 403
