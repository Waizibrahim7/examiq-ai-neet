# ExamIQ AI - NEET Pilot Test Report

| Check | Status | Evidence |
| --- | --- | --- |
| Python compilation | Pass | `python3 -m py_compile` across application modules |
| Per-student persistence | Pass | Automated SQLite isolation test |
| NEET UG 2025 Code 45 question bank | Pass | 180 source-image questions and 180 key entries |
| NEET UG 2024 Code T3 question bank | Pass | 200 source-image questions and 200 key entries |
| NEET 2024 score rule | Pass | Automated 200-question response evaluates 180 questions / 720 marks |
| Submitted attempt immutability | Pass | Automated attempt update rejection after submission |
| Login | Pass | Browser test with a temporary student account |
| Exact paper selection | Pass | Browser test: repository selection opened the correct 2024 200-question paper |
| Test timer | Pass | Browser test observed a live countdown from 03:00:00 to 02:59:34 |
| Answer saving and palette | Pass | Browser test saved Option 2 and changed Question 1 to Answered |
| Test submission and result | Pass | Browser test produced a real 4/720 result from the saved response |
| Performance and rank links | Pass | Browser navigation reached linked analytics and rank estimate pages |
| Registration form | Manual browser check required | Data-layer registration and password handling are covered; submit the UI form in pilot acceptance |
| Automatic timeout submission | Manual browser check required | Requires a shortened test-duration staging run |
| PDF report download | Manual browser check required | Requires a browser download check |
| College explorer | Pass | NEET-only dataset page opened without browser errors |

## Pilot Acceptance Rule

Do not invite students until manual browser checks pass for registration, timer, answer saving, submission, result display, and logout. Do not advertise 5,000+ concurrent capacity until the production work in `DEPLOYMENT.md` is complete.
