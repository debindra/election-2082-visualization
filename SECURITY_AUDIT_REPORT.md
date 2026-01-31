# Security Audit Report — Election Visualization System

**Audit Date:** January 31, 2025  
**Scope:** Full system (FastAPI backend, React frontend, dependencies, configuration)  
**Standards:** OWASP Top 10, CWE Top 25, SANS Top 25

---

## Executive Summary

The Election Visualization System is a **read-only** data visualization platform with no authentication, no database, and no state-changing operations. The overall risk profile is **low to medium**. The audit identified dependency vulnerabilities, input validation concerns, information disclosure, and missing security hardening.

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 1 |
| Medium | 5 |
| Low | 6 |

---

## 1. Dependency Vulnerabilities

### 1.1 Frontend (npm)

**Severity: Medium**

| Package | Issue | CVE / Advisory | Fix |
|---------|-------|----------------|-----|
| **vite** (via esbuild) | Development server SSRF: any website can send requests to the dev server and read responses | [GHSA-67mh-4wv8-2f99](https://github.com/advisories/GHSA-67mh-4wv8-2f99) | Update esbuild when fix available; **only affects dev mode**, not production build |
| **@vitejs/plugin-react** | Transitive via vite | Same | Same |

**Impact:** Only affects local development when running `npm run dev`. Production builds (`vite build`) are not affected.

**Remediation:**
- Run `npm update vite @vitejs/plugin-react` periodically
- Monitor [Vite security advisories](https://github.com/vitejs/vite/security/advisories)
- Never expose dev server to untrusted networks

### 1.2 Backend (Python)

**Severity: Low**

`pip-audit` was not available in the environment; manual review of `requirements.txt`:

| Package | Current | Notes |
|---------|---------|-------|
| fastapi | 0.104.1 | Check for newer security patches |
| uvicorn | 0.24.0 | Check for newer releases |
| pandas | >=2.1.0 | No upper bound; consider pinning |
| python-dotenv | >=1.0.0 | No upper bound |

**Recommendation:** Add `pip-audit` to CI and run regularly:
```bash
pip install pip-audit
pip-audit
```

---

## 2. Code Vulnerabilities

### 2.1 ReDoS (Regular Expression Denial of Service)

**Severity: High**  
**CWE-1333** | **OWASP A04:2021 – Insecure Design**

**Affected locations:**

| File | Line | Code | Risk |
|------|------|------|------|
| `app/main.py` | 82–87, 253–256, 395–402, 475–476, 514–517 | `df[...].str.contains(value, ...)` | User-controlled `value` passed to regex engine |
| `app/api/routes/insights.py` | 267–273, 305–311 | Same pattern | Same |
| `app/services/map_service.py` | 85–90, 166 | Same pattern | Same |

Pandas `Series.str.contains()` uses **regex by default** (`regex=True`). User input in query params (`province`, `district`, `constituency`, `party`, `gender`, `education_level`) is passed directly. Malicious input such as `(a+)+$` or `.*.*.*` can cause catastrophic backtracking and CPU exhaustion (ReDoS).

**Example attack:**
```
GET /api/v1/elections/2022/candidates?province=(a+)+$
GET /api/v1/insights/year-insights?election_year=2022&party=.*.*.*
```

**Remediation:** Disable regex for user-controlled filters:

```python
# app/main.py, _match_col_or_en and similar
m = df[main_col].astype(str).str.contains(value, case=False, na=False, regex=False)
```

**Status: FIXED** — `regex=False` applied in `app/main.py`, `app/api/routes/insights.py`, and `app/services/map_service.py`.

---

### 2.2 Information Disclosure

**Severity: Medium**  
**CWE-200**

#### 2.2.1 Health Endpoint Exposes Internal Path

**Location:** `app/main.py:212–220`

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "available_elections": available_elections,
        "elections_dir": str(loader.elections_dir),  # ← Exposes filesystem path
    }
```

**Risk:** Reveals server filesystem layout (e.g., `/Users/deb/.../data/elections`).

**Remediation:** Remove `elections_dir` from production responses or restrict to internal/admin use.

**Status: FIXED** — `elections_dir` removed from `/health` response.

#### 2.2.2 Global Exception Handler Exposes Stack Trace

**Location:** `app/main.py:465–471`

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}  # ← Exposes exception text
    )
```

**Risk:** `str(exc)` can leak internal details (paths, data, logic) to clients.

**Remediation:**
```python
return JSONResponse(
    status_code=500,
    content={"detail": "Internal server error"},  # Generic message only
)
```

**Status: FIXED** — Exception details no longer returned to clients.

---

### 2.3 SQL Injection

**Severity: N/A**

No SQL or database usage. Data is loaded from CSV via pandas. **No SQL injection risk.**

---

### 2.4 XSS (Cross-Site Scripting)

**Severity: Low**

- No `dangerouslySetInnerHTML`, `innerHTML`, or `eval()` found in `frontend/src`.
- React escapes text by default.
- API returns JSON; no HTML rendering of user input on the server.

**Recommendation:** Continue avoiding raw HTML injection. When displaying API data, ensure components use safe rendering (e.g., avoid `dangerouslySetInnerHTML` with user data).

---

### 2.5 Authentication & Authorization

**Severity: Low (by design)**

- No authentication or authorization.
- API is read-only (no POST/PUT/DELETE).
- Data is public election information.

**Recommendation:** If the system is ever exposed beyond a trusted network or adds sensitive data:
- Add authentication (e.g., API keys, JWT).
- Implement rate limiting (e.g., `slowapi`).
- Restrict admin/debug endpoints.

---

### 2.6 Path Traversal

**Severity: Low**

**Location:** `app/data/loader.py`

Election year is validated (2000–2100) and used to build filenames from a fixed pattern (e.g., `election_2022.csv`). No user-controlled path segments. **Path traversal risk is minimal.**

---

## 3. Secret Detection

**Severity: Low**

| Finding | Location | Risk |
|---------|----------|------|
| `.env` usage | `app/core/settings.py` | Correct: env vars for config |
| `VITE_API_URL` | `frontend/src/services/api.js` | Correct: build-time env for API URL |
| `.env` in `.gitignore` | Yes | Good |
| Hardcoded secrets | None found | None |

**Recommendation:** Ensure `.env` and `.env.local` are never committed. Consider using a secret scanner (e.g., `gitleaks`, `trufflehog`) in CI.

---

## 4. Configuration Security

### 4.1 CORS

**Severity: Medium**  
**Current:** `app/core/settings.py:41–44`

```python
cors_origins: list[str] = [
    "http://localhost:3000", "http://127.0.0.1:3000",
    "http://localhost:5173", "http://127.0.0.1:5173"
]
cors_allow_credentials: bool = True
cors_allow_methods: list[str] = ["*"]
cors_allow_headers: list[str] = ["*"]
```

**Risk:** Defaults are suitable for development. In production, `CORS_ORIGINS` must be set to explicit domains (e.g., `https://your-domain.com`). Overly permissive origins with credentials can enable cross-origin abuse.

**Remediation:** Document production CORS setup and validate that `CORS_ORIGINS` is set in production.

---

### 4.2 Security Headers

**Severity: Medium**

FastAPI does not add security headers by default. Missing headers include:

| Header | Purpose |
|--------|---------|
| `X-Frame-Options` | Clickjacking protection |
| `X-Content-Type-Options` | MIME sniffing protection |
| `Strict-Transport-Security` | HTTPS enforcement |
| `Content-Security-Policy` | XSS mitigation |
| `X-XSS-Protection` | Legacy XSS filter (deprecated but still useful) |

**Remediation:** Add middleware:

```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

**Status: FIXED** — Security headers middleware added to `app/main.py`.

---

### 4.3 Production Server Configuration

**Severity: Medium**

**Location:** `run.sh`

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Risk:**
- `--reload` enables auto-restart on code changes; suitable only for development.
- `0.0.0.0` binds to all interfaces; ensure firewall rules restrict access in production.

**Remediation:** Use a production run script:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

### 4.4 Environment Variable Security

**Severity: Low**

- `.env.example` exists; actual `.env` is gitignored.
- `pydantic-settings` loads from `.env` with `case_sensitive = False`.

**Recommendation:** Ensure production secrets (if any) are stored in a secrets manager, not in `.env` files on disk.

---

## 5. Recommendations Summary

| Priority | Action | Status |
|----------|--------|--------|
| **High** | Fix ReDoS: use `regex=False` for all user input in `str.contains()` | Done |
| **Medium** | Remove `elections_dir` from `/health` response | Done |
| **Medium** | Stop returning `str(exc)` in global exception handler | Done |
| **Medium** | Add security headers (X-Frame-Options, X-Content-Type-Options, etc.) | Done |
| **Medium** | Document and enforce production CORS configuration | Pending |
| **Medium** | Remove `--reload` from production run script | Pending |
| **Low** | Add `pip-audit` to CI for Python dependencies |
| **Low** | Pin Python dependency versions where appropriate |
| **Low** | Consider rate limiting if API is public |

---

## 6. Security Best Practices

1. **Input validation:** Validate and sanitize all query parameters; use allowlists where possible.
2. **Rate limiting:** Add rate limiting for public endpoints to mitigate abuse.
3. **Logging:** Avoid logging sensitive data; ensure logs are not exposed.
4. **HTTPS:** Enforce HTTPS in production (via reverse proxy or load balancer).
5. **Dependency updates:** Run `npm audit` and `pip-audit` regularly and address findings.
6. **Least privilege:** Run the application with minimal required filesystem and network permissions.

---

*Report generated by security audit. Review and prioritize remediation based on your deployment context.*
