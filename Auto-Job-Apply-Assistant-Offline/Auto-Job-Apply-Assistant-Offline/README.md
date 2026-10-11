# Auto Job Apply Assistant — Offline Edition

Professional Streamlit career workspace. All job listings are static, synthetic records in `data/jobs.csv`; **no external API is used**. User accounts, preferences, resume metadata/text, saved jobs, applications and drafts are stored in MySQL database `auto_job_assistant_offline`. Passwords are hashed with Argon2. Resume files are stored in `private_uploads`.

## Setup (Windows, VS Code, Python 3.13)

### 1. In MySQL Workbench
Connect as your administrator and execute the following, changing the example password to your own strong password:

```sql
CREATE DATABASE IF NOT EXISTS auto_job_assistant_offline CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'auto_job_app'@'localhost' IDENTIFIED BY 'Choose-A-Strong-Local-Password-42!';
ALTER USER 'auto_job_app'@'localhost' IDENTIFIED BY 'Choose-A-Strong-Local-Password-42!';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES ON auto_job_assistant_offline.* TO 'auto_job_app'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Open extracted folder in VS Code terminal

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
If `.env` already exists, edit it instead of overwriting it. If activation is blocked, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again.

### 3. Configure `.env`
Edit the real `.env` file, not `.env.example`:

```dotenv
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=auto_job_assistant_offline
MYSQL_USER=auto_job_app
MYSQL_PASSWORD=Choose-A-Strong-Local-Password-42!
```
The username/password must exactly match the SQL you ran in Workbench. Ensure MySQL Server is running.

### 4. Initialize and launch

```powershell
python -m scripts.init_db
streamlit run app.py
```

Register a new account on the app. No API keys are needed. The 120 included listings and company names are fictional demo data, not live vacancies; no apply links are supplied. Applications are user-reviewed and tracked manually. Resume matching is a text similarity heuristic, not a hiring probability. Scanned image-only PDFs need OCR, which is not included.

## Features
- Dark professional interface, dashboard and search filters
- Registration/login/logout and Argon2 password hashing
- MySQL user data isolation by `user_id`
- Static dataset of 120 jobs across 20 roles/categories
- PDF/DOCX resume extraction and keyword similarity
- Saved jobs, notes, application statuses, follow-up dates, CSV export
- Cover-letter template generation and saved drafts
- Preferences and password change

## Security note
This is a local starter, not a production security certification. Keep `.env` private, don't commit credentials or resumes to Git, and add a production-grade email reset, rate limiting, backups and a security review before public deployment.
