# Student Data Handling

## What ExamIQ AI stores

For each student account, the app stores the submitted name, email address, mobile number, NEET category, state or union territory, a salted PBKDF2 password hash, and account creation time. It also stores the student's own test responses, saved review markers, attempt timestamps, submitted results, and feedback.

The app does not store the plaintext password. A one-time verification code is not stored in the ExamIQ database; it is handled by the configured identity provider when email OTP is enabled.

## Where it is stored

Local development uses `database.db`, a SQLite file that is ignored by Git. On Streamlit Community Cloud, this local file can be replaced when an app instance restarts, so it is not suitable for real student accounts.

The production configuration uses `EXAMIQ_DATABASE_URL` to connect to a managed PostgreSQL database. Once that value is configured, registrations, attempts, feedback, and head-to-head rooms are stored in the managed database instead of the local file.

## Release requirements

Before inviting students, configure managed PostgreSQL backups, email OTP, request rate limits, monitoring, a privacy policy, and a support contact. The app shows its active storage mode rather than claiming that the local pilot database is persistent.

See [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md) for the required Streamlit and Supabase configuration.
