# AptitudeLearner — Full-stack placement preparation

## Features
- Student registration, login and logout (passwords are hashed)
- Premium responsive dashboard
- Topic-wise practice for aptitude, reasoning, verbal, programming and interview preparation
- Timed 10-question mock tests and untimed practice
- Instant scoring and explanations
- Per-account progress history, accuracy and category summaries
- Question bookmarking (browser cookie in this starter version)
- Flask backend with MySQL support; SQLite is the default for a quick first run

## 1. Open in VS Code
1. Extract `AptitudeLearner_FullStack.zip`.
2. In VS Code choose **File → Open Folder** and select `AptitudeLearner_FullStack`.
3. Open **Terminal → New Terminal**.

## 2. Create and activate a virtual environment (Windows PowerShell)
```powershell
py -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```
If `py` is not recognised, try `python -m venv venv`.

## 3. Install packages
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. First run (no MySQL setup needed)
The starter defaults to SQLite so you can verify the app immediately:
```powershell
python app.py
```
Open http://127.0.0.1:5000 in Chrome. Register a new account.

The database file `aptitudelearner.db` is created automatically. Sample questions are inserted only once:
```powershell
flask --app app seed
```
Run that command once after installing packages, then refresh the site.

## 5. Switch to MySQL
1. Install and start MySQL Server (or start it in XAMPP).
2. In MySQL Workbench or phpMyAdmin run:
```sql
CREATE DATABASE aptitudelearner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
3. Copy `.env.example` to `.env`.
4. Edit `.env` and set your MySQL username/password and a strong SECRET_KEY.
5. Install python-dotenv is already in requirements. Add these two lines near the top of `app.py`, before `app.config["SECRET_KEY"]`:
```python
from dotenv import load_dotenv
load_dotenv()
```
6. Stop the running server (Ctrl+C), then start it again:
```powershell
python app.py
flask --app app seed
```
If you use XAMPP, make sure its MySQL service is running. The database name must match the URL.

## 6. Main folders
- `app.py` — Flask routes, database models, login, quiz scoring and progress
- `templates/` — HTML pages
- `static/css/style.css` — responsive premium theme
- `static/js/app.js` — quiz and bookmark interactions

## Notes
- This is a learning project starter, not a production deployment. Before public deployment, set a strong SECRET_KEY, turn off debug mode, add CSRF protection, server-side bookmark storage, rate limiting, email verification and backups.
- The included question bank is a small original sample set. Add more questions in the `SEED` list or create an admin question-management module.
- Do not use real passwords from other accounts while testing.
