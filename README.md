# Versioned FastAPI Backend Integration (v1.0)

A modular, production-ready FastAPI backend implementing role-based access control (`admin`, `student`, `employer`), MySQL-shaped repository contracts, an immutable matching engine (`v1.0`), an application lifecycle state machine, and standardized `{data, meta, error}` envelopes.

---

## Key Features

1. **Role-Based Access Control**:
   - `admin`: Full system access, skill catalog management, global platform analytics.
   - `student`: Manage own profile and skills (proficiency 1–5), browse jobs, run immutable match analyses, submit/withdraw applications.
   - `employer`: Manage company jobs and requirements, review candidate rankings, view full student profile exclusively for matching candidates, and govern application state transitions.

2. **Standardized Response Envelope**:
   - Consistent JSON format for all endpoints:
     ```json
     {
       "data": { ... } | [ ... ] | null,
       "meta": {
         "timestamp": "2026-09-05T11:30:00Z",
         "correlation_id": "req-123e4567-e89b",
         "page": 1,
         "per_page": 20,
         "total": 100
       },
       "error": {
         "code": "RESOURCE_NOT_FOUND",
         "message": "Human-readable description",
         "details": []
       } | null
     }
     ```

3. **Authentication & Token Management**:
   - Argon2id password hashing (`argon2-cffi`).
   - Short-lived JWT access tokens (15 minutes).
   - Rotating single-use refresh tokens (7 days) with revocation tracking.

4. **Skill Catalog Normalization**:
   - Admin-curated catalog.
   - Names trimmed, consecutive whitespace collapsed to single space, case-insensitive collision prevention.
   - Categorized skills (e.g. `Backend`, `Frontend`, `Database`, `DevOps`, `Data Science`).

5. **Matching & Recommendations Engine (v1.0)**:
   - Gap calculation: `gap = max(required_proficiency - current_proficiency, 0)` (missing skills default to level `0`).
   - Match calculation: Weighted average of `min(current / required, 1.0) * 100`.
   - Requirement weights: `mandatory = 2.0`, `optional = 1.0`.
   - Rounded to the nearest whole percentage.
   - Immutable analysis run snapshot preserving inputs, timestamp, and results.
   - Prioritized recommendations: 1 per unmet requirement, sorted by mandatory gaps first, then descending by gap magnitude.

6. **Application Workflow State Machine**:
   - Captures match snapshot at submission time.
   - Rejects duplicate active applications for the same student and job.
   - Student can submit or withdraw.
   - Employer transitions: `submitted` → `reviewed` → `shortlisted` | `rejected` → `closed`.

7. **Observability & Security**:
   - Correlation ID middleware (`X-Correlation-ID`).
   - Request timing middleware (`X-Process-Time`).
   - Endpoint rate limiting.
   - Structured audit logging for login attempts, token revocation, job updates, application status changes, and candidate profile access.
   - `/health` probe.

8. **Deferred Architecture Documents**:
   - [SQLAlchemy 2.0 Mapping & Alembic Migration Sequence](docs/persistence_and_migrations.md)
   - [Enterprise Backup & Disaster Recovery Runbook](docs/backup_and_recovery_strategy.md)

---

## Installation & Running the Server

Because this project resides in a synced OneDrive folder (`OneDrive\Desktop`), Windows Defender/OneDrive locks binary `.exe` creation inside local `.venv` folders. The virtual environment is installed at `C:\Users\vigne\.venvs\codethon`.

### Option 1: Direct Execution (Recommended)
```powershell
& "C:\Users\vigne\.venvs\codethon\Scripts\uvicorn.exe" app.main:app --reload --port 8000
```

### Option 2: Activate in PowerShell
```powershell
C:\Users\vigne\.venvs\codethon\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### Option 3: Using `uv run`
```powershell
$env:UV_PROJECT_ENVIRONMENT="C:\Users\vigne\.venvs\codethon"
uv run uvicorn app.main:app --reload --port 8000
```

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.
