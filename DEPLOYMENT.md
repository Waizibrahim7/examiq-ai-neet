# ExamIQ AI Deployment Guide

## Release Modes

### Public preview

Use Streamlit Community Cloud only for a mentor demo or a small supervised preview. It requires a GitHub repository and an account at `share.streamlit.io`. Select `app.py` as the entrypoint and Python 3.12 in Advanced settings. The platform runs the repository root, reads `requirements.txt`, and serves the app over HTTPS.

The default SQLite database is local to one application instance. Student records can be lost on restart and cannot safely support a real public examination service. Do not collect sensitive student data or promise persistent accounts on this mode.

### Production student platform

Do not claim 5,000 concurrent students until all of these are complete:

1. Move students, attempts, feedback, and admin records to managed PostgreSQL.
2. Store PDF files and question images in private object storage with a CDN.
3. Run multiple application instances behind a load balancer.
4. Add verified email, password reset, role-based admin access, rate limiting, audit logs, backups, and monitoring.
5. Complete peak-load, security, recovery, and accessibility testing.
6. Obtain written permission to publish every PYQ, answer key, and college-cutoff dataset.

The included `Dockerfile` is a repeatable starting point for a managed container host. It is not a replacement for the production changes above.

## Local Pilot Run

```bash
cd "/Users/waizi/Documents/Codex/2026-06-22/today-s-goal-build-the-login/Exam_Benchmarking_System"
EXAMIQ_ADMIN_EMAIL="your-registered-email@example.com" python3 -m streamlit run app.py --server.port 8526
```

Open `http://localhost:8526`. Students should each register their own account and never share passwords.
