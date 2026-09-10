# Production Student Data and OTP Setup

The public preview runs with local SQLite unless `EXAMIQ_DATABASE_URL` is set. Local SQLite is not durable on Streamlit Community Cloud and must not be described as persistent student storage.

## 1. Provision Managed PostgreSQL

Create a managed PostgreSQL database. Supabase Postgres is a suitable option because it can also provide email OTP authentication. Copy its direct PostgreSQL connection string into Streamlit Community Cloud Secrets as `EXAMIQ_DATABASE_URL`.

## 2. Configure Email OTP

Create a Supabase project and add these values to Streamlit Community Cloud Secrets:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_your_key"
```

In Supabase Authentication settings, configure the email template to contain `{{ .Token }}`. This sends a six-digit code rather than only a magic link. Configure the ExamIQ public URL as an allowed redirect URL.

## 3. Configure Phone OTP Only When Ready

Phone OTP needs an SMS provider and compliance with the regulations for every country served. For India, confirm TRAI DLT requirements before enabling it. Do not set `SUPABASE_PHONE_OTP_ENABLED` until the provider and compliance review are complete.

## 4. Before Inviting a Large Cohort

1. Enable database backups and a retention policy.
2. Restrict database access to the application only.
3. Set rate limits for login, OTP requests, registration, and test submission.
4. Add monitoring and error alerts.
5. Run security and concurrent-user load tests.
6. Publish a privacy policy and support contact.
