# ExamIQ AI - NEET Student Pilot

ExamIQ AI is a NEET-first practice and performance platform. A student can register, select a verified previous-year paper, take a timed test inside the app, submit it, review a real score calculation, view subject analytics, and explore practice rank and college-planning data.

## Current Scope

- PBKDF2 password-hash based pilot registration and login
- Per-student attempts; one student cannot see or overwrite another student's answers
- Verified NEET UG 2025 Code 45, NEET UG 2024 Code T3, and NEET UG 2023 Solved Paper, rendered from the uploaded source PDFs
- Persistent test timer, answer palette, mark-for-review, clear response, automatic timeout submission
- NEET +4/-1 evaluation and correct 2024 Section B selection rule
- Result report download, performance analytics, feedback, and NEET-only rank and college planning pages
- Private two-student NEET challenges, enabled only after persistent cloud storage is configured
- Restricted admin panel through `EXAMIQ_ADMIN_EMAIL`

## Technology

| Area | Technology |
| --- | --- |
| Application | Python and Streamlit |
| Student data | SQLite with WAL mode |
| Question rendering | PyMuPDF generated source-image fragments |
| Source data | PDF, JSON, CSV |
| Automated checks | Python `unittest` |

## Run Locally

```bash
cd "/Users/waizi/Documents/Codex/2026-06-22/today-s-goal-build-the-login/Exam_Benchmarking_System"
python3 -m streamlit run app.py --server.port 8526
```

For local admin access:

```bash
EXAMIQ_ADMIN_EMAIL="your-registered-email@example.com" python3 -m streamlit run app.py --server.port 8526
```

## Test

```bash
python3 -m unittest discover -s tests -v
```

## Project Flow

```text
Register / Login
  -> NEET Paper Repository
  -> Timed NEET Test
  -> Submit
  -> Result Dashboard
  -> Performance Analytics
  -> Rank Estimate
  -> College Explorer
  -> Feedback
```

## Data Notes

The source filenames were verified against the PDF headers before being added to the NEET catalogue. The rank estimate and college explorer are planning tools based on the datasets currently included in this repository; they are not NTA scores, counselling outcomes, or admission guarantees.

Read [DATA_HANDLING.md](DATA_HANDLING.md) for the fields stored by the app and the difference between local pilot storage and a managed production database.

## Production Scale

This repository is appropriate for a controlled pilot, not an untested 5,000-concurrent-student launch. Read [DEPLOYMENT.md](DEPLOYMENT.md) before deploying publicly.
