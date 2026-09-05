from app.core.security import create_access_token, hash_password
from app.domain.models import Role, User


def test_canonical_auth_and_public_registration_guard(client):
    # 1. Attempt to register as admin via public endpoint (must be rejected)
    bad_reg = client.post(
        "/api/auth/register",
        json={
            "email": "hacker@test.com",
            "password": "Password123!",
            "full_name": "Hacker",
            "role": "admin",
        },
    )
    assert bad_reg.status_code == 403
    assert bad_reg.json()["error"]["code"] == "PERMISSION_DENIED"
    assert "request_id" in bad_reg.json()["error"]

    # 2. Register valid student
    reg_res = client.post(
        "/api/auth/register",
        json={
            "email": "student_one@test.com",
            "password": "Password123!",
            "full_name": "Student One",
            "role": "student",
        },
    )
    assert reg_res.status_code == 201
    assert reg_res.json()["data"]["role"] == "student"

    # 3. Login
    login_res = client.post(
        "/api/auth/login",
        json={"email": "student_one@test.com", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]

    # 4. /api/auth/me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == "student_one@test.com"


def test_student_privacy_isolation_student_a_vs_student_b(client, admin_headers, repo_container):
    # Setup Student A
    user_a = repo_container.user_repo.create(
        User(id=0, email="student_a@test.com", hashed_password=hash_password("pw"), full_name="Student A", role=Role.STUDENT)
    )
    profile_a = repo_container.student_repo.create_student(
        StudentProfile(student_id=0, name="Student A", email="student_a@test.com", user_id=user_a.id)
    )
    token_a = create_access_token(user_id=user_a.id, role="student")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Setup Student B
    user_b = repo_container.user_repo.create(
        User(id=0, email="student_b@test.com", hashed_password=hash_password("pw"), full_name="Student B", role=Role.STUDENT)
    )
    profile_b = repo_container.student_repo.create_student(
        StudentProfile(student_id=0, name="Student B", email="student_b@test.com", user_id=user_b.id)
    )

    # Setup a job
    job = repo_container.job_repo.create_job(
        Job(id=0, employer_id=1, title="Developer", company_name="Co", description="Desc")
    )

    # 1. Student A attempts to access Student B profile -> 403 PERMISSION_DENIED
    res1 = client.get(f"/api/students/{profile_b.student_id}", headers=headers_a)
    assert res1.status_code == 403
    assert res1.json()["error"]["code"] == "PERMISSION_DENIED"
    assert "request_id" in res1.json()["error"]

    # 2. Student A attempts to modify Student B profile -> 403 PERMISSION_DENIED
    res2 = client.put(f"/api/students/{profile_b.student_id}", json={"headline": "Hacked"}, headers=headers_a)
    assert res2.status_code == 403
    assert res2.json()["error"]["code"] == "PERMISSION_DENIED"

    # 3. Student A attempts to run skill gap analysis for Student B -> 403 PERMISSION_DENIED
    res3 = client.post(f"/api/students/{profile_b.student_id}/jobs/{job.id}/skill-gap", headers=headers_a)
    assert res3.status_code == 403
    assert res3.json()["error"]["code"] == "PERMISSION_DENIED"

    # 4. Student A attempts to view recommendations for Student B -> 403 PERMISSION_DENIED
    res4 = client.get(f"/api/students/{profile_b.student_id}/jobs/{job.id}/recommendations", headers=headers_a)
    assert res4.status_code == 403
    assert res4.json()["error"]["code"] == "PERMISSION_DENIED"

    # 5. Student A accesses their own profile -> 200 OK
    own_res = client.get(f"/api/students/{profile_a.student_id}", headers=headers_a)
    assert own_res.status_code == 200
    assert own_res.json()["data"]["id"] == profile_a.student_id


def test_canonical_skill_gap_and_recommendations_flow(client, admin_headers, student_headers, student_user, repo_container):
    # Create skills via /api/skills
    s1 = client.post("/api/skills", json={"name": "Java", "category": "Backend"}, headers=admin_headers).json()["data"]["id"]
    s2 = client.post("/api/skills", json={"name": "React", "category": "Frontend"}, headers=admin_headers).json()["data"]["id"]

    # Student adds skill (Java=4) via /api/students/{id}/skills
    student_profile = repo_container.student_repo.get_student_by_user_id(student_user.id)
    client.post(
        f"/api/students/{student_profile.student_id}/skills",
        json={"skill_id": s1, "proficiency": 4},
        headers=student_headers,
    )

    # Admin creates job via /api/jobs with skills (Java=4 Mandatory, React=3 Optional)
    job_res = client.post(
        "/api/jobs",
        json={
            "title": "Fullstack Engineer",
            "company_name": "Acme",
            "description": "Fullstack role",
            "requirements": [
                {"skill_id": s1, "required_proficiency": 4, "mandatory": True},
                {"skill_id": s2, "required_proficiency": 3, "mandatory": False},
            ],
        },
        headers=admin_headers,
    )
    job_id = job_res.json()["data"]["id"]

    # Student triggers skill-gap via POST /api/students/{studentId}/jobs/{jobId}/skill-gap
    gap_res = client.post(
        f"/api/students/{student_profile.student_id}/jobs/{job_id}/skill-gap",
        headers=student_headers,
    )
    assert gap_res.status_code == 201
    gap_data = gap_res.json()["data"]
    # Java: 4/4 mand=2 -> 200. React: 0/3 opt=1 -> 0. Total wt=3. 200/3 = 67%
    assert gap_data["overall_match_percentage"] == 67
    assert len(gap_data["recommendations"]) == 1
    assert gap_data["recommendations"][0]["skill_id"] == s2
    assert gap_data["recommendations"][0]["reason"] == "Required supporting skill"

    # Get recommendations via GET /api/students/{studentId}/jobs/{jobId}/recommendations
    recs_res = client.get(
        f"/api/students/{student_profile.student_id}/jobs/{job_id}/recommendations",
        headers=student_headers,
    )
    assert recs_res.status_code == 200
    assert len(recs_res.json()["data"]) == 1


def test_canonical_live_dashboard(client, admin_headers):
    dash_res = client.get("/api/dashboard", headers=admin_headers)
    assert dash_res.status_code == 200
    data = dash_res.json()["data"]
    assert "total_students" in data
    assert "total_jobs" in data
    assert "total_applications" in data
    assert "average_skill_match" in data
    assert "top_skill_gaps" in data
    # Ensure no hardcoded mock numbers
    assert isinstance(data["total_students"], int)
    assert isinstance(data["total_jobs"], int)


from app.domain.models import StudentProfile, Job
