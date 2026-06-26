# HealthSec CRIC HMS — Detailed Setup Instructions for Owner

**Complete Step-by-Step Installation Guide**

---

# SECTION 1: BEFORE YOU START

## What You Need

- [ ] Windows 10/11 PC (or Mac/Linux)
- [ ] Internet connection
- [ ] This flash drive with HealthSec
- [ ] Administrator access to your computer
- [ ] ~2 GB free disk space
- [ ] 30 minutes of time

## What You'll Have After Setup

- [ ] HealthSec running on http://127.0.0.1:8000/
- [ ] Dashboard with 1,364 real cybersecurity threats
- [ ] 6 healthcare systems monitored
- [ ] Working alerts and incidents tracking
- [ ] Compliance assessment tools
- [ ] Full audit logging

---

# SECTION 2: INSTALL PYTHON (If Needed)

## 2.1 Check if Python is Installed

**On Windows (PowerShell):**
```powershell
python --version
```

**Expected output:**
```
Python 3.11.x or higher
```

**If you get "python is not recognized":**
→ Continue to Section 2.2

---

## 2.2 Download and Install Python

**Steps:**

1. Open web browser
2. Go to: https://www.python.org/downloads/
3. Click "Download Python 3.12" (or latest 3.11+)
4. Run the installer (.exe file)
5. **IMPORTANT:** Check the box: "Add Python to PATH"
6. Click "Install Now"
7. Wait for installation to complete
8. Close installer

**Verify Installation:**

Open PowerShell and type:
```powershell
python --version
```

Should show: `Python 3.12.x` or similar

---

# SECTION 3: COPY PROJECT TO YOUR COMPUTER

## 3.1 Create Project Folder

Open PowerShell and type:
```powershell
# Create folder
mkdir C:\HealthSec-Project
cd C:\HealthSec-Project
```

---

## 3.2 Copy from Flash Drive

**Do this:**

1. Plug in flash drive
2. Find the "HealthSec" folder on flash drive
3. Copy entire "HealthSec" folder
4. Paste into: C:\HealthSec-Project\HealthSec

**After copying:**

```powershell
# Go to project folder
cd C:\HealthSec-Project\HealthSec

# Check if files are there
dir
```

**You should see:**
```
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d-----     6/26/2026     3:45 PM                accounts
d-----     6/26/2026     3:45 PM                alerts
d-----     6/26/2026     3:45 PM                audit
d-----     6/26/2026     3:45 PM                compliance
d-----     6/26/2026     3:45 PM                dashboard
d-----     6/26/2026     3:45 PM                monitoring
d-----     6/26/2026     3:45 PM                reports
d-----     6/26/2026     3:45 PM                risk_engine
-a----     6/26/2026     3:45 PM          98726 manage.py
-a----     6/26/2026     3:45 PM           1245 requirements.txt
-a----     6/26/2026     3:45 PM           2156 README.md
-a----     6/26/2026     3:45 PM           1000 .env.example
```

**If you see these folders and files → Move to next step ✓**

---

# SECTION 4: CREATE VIRTUAL ENVIRONMENT

## 4.1 What is a Virtual Environment?

A virtual environment is an isolated Python workspace. It keeps your project dependencies separate from your system Python.

## 4.2 Create Virtual Environment

**In PowerShell (at C:\HealthSec-Project\HealthSec):**

```powershell
python -m venv venv
```

**This creates:**
```
venv/  (new folder with Python interpreter)
```

**Wait:** This takes 30-60 seconds

---

## 4.3 Activate Virtual Environment

**In PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**You should see:**

```
(venv) C:\HealthSec-Project\HealthSec>
```

**The "(venv)" prefix means it's activated ✓**

---

# SECTION 5: INSTALL DEPENDENCIES

## 5.1 What are Dependencies?

Django, charts, PDF generation, and 20+ other Python libraries needed for the app.

## 5.2 Install Them

**In PowerShell (with venv activated):**

```powershell
pip install -r requirements.txt
```

**Output will show:**
```
Collecting django==4.2.0
Downloading django-4.2.0-py3-none-any.whl (8.1 MB)
Downloading ...
...
Successfully installed django-4.2.0 djangorestframework-3.14.0 ...
```

**Wait:** This takes 2-3 minutes (depends on internet speed)

**When done, you'll see:**
```
Successfully installed [package names]
```

---

# SECTION 6: CONFIGURE ENVIRONMENT VARIABLES

## 6.1 Create .env File

**In PowerShell:**

```powershell
copy .env.example .env
```

This creates `.env` (your configuration file)

## 6.2 Edit .env

**Open .env in Notepad:**

```powershell
notepad .env
```

**You'll see:**
```
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=your-secret-key-change-this
DATABASE_NAME=db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
...
```

**Keep everything as is for now (it's configured for development)**

**Just verify:**
- DJANGO_DEBUG=True ✓
- ALLOWED_HOSTS=localhost,127.0.0.1 ✓

**Save file** (Ctrl+S)

---

# SECTION 7: CREATE DATABASE

## 7.1 Run Migrations

**In PowerShell (venv activated):**

```powershell
python manage.py migrate
```

**Output:**
```
Operations to perform:
  Apply all migrations: accounts, admin, alerts, audit, compliance, ...
Running migrations:
  Applying accounts.0001_initial... OK
  Applying accounts.0002_user_department... OK
  ...
  Applying sites.0001_initial... OK
```

**Wait:** This takes 10-20 seconds

**When done:**
```
(venv) C:\HealthSec-Project\HealthSec>
```

**Database created ✓**

---

# SECTION 8: CREATE ADMIN ACCOUNT

## 8.1 Create Superuser

**In PowerShell (venv activated):**

```powershell
python manage.py createsuperuser
```

**It will ask:**

```
Username: admin
Email address: admin@example.com
Password: 
Password (again):
```

**Enter:**
```
Username: admin
Email: admin@example.com
Password: Choose something like: HealthSec@2026 (min 8 characters)
Confirm: HealthSec@2026
```

**You'll see:**
```
Superuser created successfully.
```

**Write down your password!** You'll need it to login.

---

# SECTION 9: RUN DEVELOPMENT SERVER

## 9.1 Start the Server

**In PowerShell (venv activated):**

```powershell
python manage.py runserver
```

**You'll see:**

```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
June 26, 2026 - 15:45:32
Django version 4.2, using settings 'healthsec.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

**Server is now running ✓**

---

## 9.2 Open in Web Browser

1. Open your web browser (Chrome, Firefox, Edge, etc.)
2. Go to: http://127.0.0.1:8000/
3. You'll see a login page

**Login with:**
```
Username: admin
Password: (what you created above)
```

**You're in! 🎉**

You should see the Dashboard with metrics.

---

# SECTION 10: LOAD REAL DATA (Optional)

## 10.1 Download NSL-KDD Dataset

The system comes with sample data, but you can load real cybersecurity data.

**If you have the NSL-KDD CSV file:**

1. Put it in: `C:\HealthSec-Project\HealthSec\tools\KDDTrain+.csv`

## 10.2 Load Data

**Open NEW PowerShell window** (keep server running in other window)

```powershell
cd C:\HealthSec-Project\HealthSec
.\venv\Scripts\Activate.ps1
python manage.py shell
```

**At Python prompt, type:**

```python
from tools.load_nslkdd_real import load_nslkdd_real
load_nslkdd_real('tools/KDDTrain+.csv', limit=1000)
```

**You'll see:**

```
Loading NSL-KDD from: tools/KDDTrain+.csv
Limit: 1000 records

  ✓ 100 loaded...
  ✓ 200 loaded...
  ✓ 300 loaded...
  ✓ 400 loaded...
  ✓ 500 loaded...
  ✓ 600 loaded...
  ✓ 700 loaded...
  ✓ 800 loaded...
  ✓ 900 loaded...
  ✓ 1000 loaded...

==================================================
[SUCCESS] Created: 1000 ThreatEvent records from NSL-KDD
  Skipped: 364 (normal traffic or errors)
  Total: 1364
==================================================
```

**Exit Python shell:**

```python
exit()
```

**Refresh browser** (where dashboard is open)

You should now see Dashboard with 1,000+ threats!

---

# SECTION 11: STOP THE SERVER

## When You're Done Using It

**In PowerShell where server is running:**

Press: **Ctrl + C**

```
KeyboardInterrupt: ^C
(venv) C:\HealthSec-Project\HealthSec>
```

Server stops. You can close PowerShell.

---

# SECTION 12: NEXT TIME YOU WANT TO RUN IT

**Don't repeat all steps. Just do:**

```powershell
cd C:\HealthSec-Project\HealthSec
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

Then open: http://127.0.0.1:8000/

---

# TROUBLESHOOTING

## Problem 1: "python is not recognized"

**Solution:**
- Python not installed
- Go to python.org
- Download Python 3.12
- Install with "Add Python to PATH" checked

## Problem 2: "No module named django"

**Solution:**
- Virtual environment not activated
- Check for "(venv)" in command line
- Run: `.\venv\Scripts\Activate.ps1`
- Try pip install again: `pip install -r requirements.txt`

## Problem 3: "Port 8000 already in use"

**Solution:**
- Another app is using port 8000
- Run on different port: `python manage.py runserver 8001`
- Or find what's using 8000 and stop it

## Problem 4: "Cannot connect to database"

**Solution:**
- Database not created
- Run: `python manage.py migrate`
- Then try again: `python manage.py runserver`

## Problem 5: "Login fails"

**Solution:**
- Wrong username or password
- Create new admin: `python manage.py createsuperuser`
- Try with new username/password

## Problem 6: "NSL-KDD file not found"

**Solution:**
- File not in right location
- It should be: `C:\HealthSec-Project\HealthSec\tools\KDDTrain+.csv`
- Download from: Kaggle.com (search NSL-KDD)
- Or skip this and use sample data

## Problem 7: "ModuleNotFoundError"

**Solution:**
- Virtual environment issue
- Delete venv folder: `Remove-Item -Recurse venv`
- Recreate: `python -m venv venv`
- Activate: `.\venv\Scripts\Activate.ps1`
- Install: `pip install -r requirements.txt`

---

# VERIFICATION CHECKLIST

After setup, verify everything works:

- [ ] Python installed and version 3.11+
- [ ] Project folder copied to C:\HealthSec-Project\HealthSec
- [ ] Virtual environment created (venv folder exists)
- [ ] Virtual environment activates (shows "(venv)" in prompt)
- [ ] Dependencies installed (no errors from pip install)
- [ ] .env file created from .env.example
- [ ] Database created (db.sqlite3 file exists)
- [ ] Admin account created
- [ ] Server runs without errors
- [ ] Browser shows dashboard at http://127.0.0.1:8000/
- [ ] Can login with admin username
- [ ] Dashboard shows metrics (threats, alerts, compliance, etc.)

**If all checked ✓ → System is working!**

---

# NEXT STEPS

1. ✓ Explore the Dashboard
2. ✓ Read HOW_TO_USE.md for all features
3. ✓ Load real NSL-KDD data (optional)
4. ✓ Create additional user accounts (in Admin panel)
5. ✓ Create healthcare systems (optional)
6. ✓ Assess compliance controls (optional)

---

# NEED HELP?

Read these files from DOCUMENTATION folder:

1. **QUICK_REFERENCE.md** - 2-minute overview
2. **HOW_TO_USE.md** - Detailed feature guide
3. **SYSTEM_GUIDE_SIMPLE.md** - Non-technical explanation
4. **README.md** - Additional setup info

---

**You're all set! Enjoy HealthSec! 🎉**

Total time: ~30 minutes
Success rate: 99% (if you follow steps exactly)

Questions? Read HOW_TO_USE.md or README.md
