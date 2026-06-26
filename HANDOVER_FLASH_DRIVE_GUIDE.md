# HealthSec CRIC HMS — Flash Drive Handover Guide

**Complete Step-by-Step Process to Transfer System to Owner**

---

# PART 1: PREPARING YOUR SYSTEM (Before Copying to Flash)

## Step 1: Clean Up Project Directory

```powershell
cd "c:\Users\bigge\OneDrive\Documents\PROJECTS\HEALTH-SEC"

# 1.1 Remove virtual environment (owner will create new one)
Remove-Item -Recurse -Force venv -ErrorAction SilentlyContinue
echo "✓ Virtual environment removed"

# 1.2 Remove database (owner will create fresh)
Remove-Item -Force db.sqlite3 -ErrorAction SilentlyContinue
echo "✓ Database removed"

# 1.3 Remove cache and compiled files
Remove-Item -Recurse -Force __pycache__ -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .pytest_cache -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force staticfiles -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force media -ErrorAction SilentlyContinue
echo "✓ Cache and compiled files removed"

# 1.4 Verify .env is NOT included (secrets protection)
if (Test-Path .env) {
    Remove-Item -Force .env
    echo "✓ .env removed (kept .env.example)"
} else {
    echo "✓ .env already removed"
}

# 1.5 List what will be copied
Write-Host "Files to be copied:" -ForegroundColor Green
Get-ChildItem -Recurse -Force | Where-Object {
    $_.FullName -notmatch '(venv|\.git|__pycache__|\.pytest_cache|staticfiles|media|\.env$)' -and
    $_.FullName -notmatch '\.sqlite3$'
} | Measure-Object | Select-Object -ExpandProperty Count
```

---

## Step 2: Commit Final Changes to Git

```powershell
# 2.1 Check git status
git status

# 2.2 Add all changes
git add .

# 2.3 Commit with note about handover
git commit -m "Final version ready for handover to project owner

- All features verified and working
- 1,364 real NSL-KDD threat events
- 16 user accounts, 6 healthcare systems
- HIPAA/NDPR/ISO 27001 compliance frameworks
- Complete documentation provided
- Ready for flash drive transfer"

# 2.4 Verify commit
git log --oneline | head -5
```

---

## Step 3: Create Handover README for Flash Drive

```powershell
# Create a special README just for the owner
```

---

# PART 2: PREPARE FILES FOR FLASH DRIVE

## Step 4: Create Flash Drive Folder Structure

```powershell
# Create a temporary folder to prepare what goes on flash
mkdir "C:\Temp\HealthSec_Flash"
mkdir "C:\Temp\HealthSec_Flash\HealthSec"
mkdir "C:\Temp\HealthSec_Flash\SETUP_INSTRUCTIONS"
mkdir "C:\Temp\HealthSec_Flash\DOCUMENTATION"

echo "✓ Folder structure created"
```

---

## Step 5: Copy Project Files

```powershell
# 5.1 Navigate to your project
cd "c:\Users\bigge\OneDrive\Documents\PROJECTS\HEALTH-SEC"

# 5.2 Copy entire project (excluding git and pycache)
xcopy /E /I /Y . "C:\Temp\HealthSec_Flash\HealthSec" /EXCLUDE:"C:\Temp\exclude.txt"

# Note: First create exclude.txt with:
# venv
# .git
# __pycache__
# .pytest_cache
# staticfiles
# media
# db.sqlite3
# .env

# 5.3 Verify copy completed
Get-ChildItem "C:\Temp\HealthSec_Flash\HealthSec" | Measure-Object
echo "✓ Project files copied"
```

---

## Step 6: Copy Documentation Files

```powershell
# Copy all documentation to separate folder
Copy-Item "c:\Users\bigge\OneDrive\Documents\PROJECTS\HEALTH-SEC\README.md" "C:\Temp\HealthSec_Flash\DOCUMENTATION\"
Copy-Item "c:\Users\bigge\OneDrive\Documents\PROJECTS\HEALTH-SEC\HOW_TO_USE.md" "C:\Temp\HealthSec_Flash\DOCUMENTATION\"
Copy-Item "c:\Users\bigge\OneDrive\Documents\PROJECTS\HEALTH-SEC\SYSTEM_READINESS_VERIFICATION.md" "C:\Temp\HealthSec_Flash\DOCUMENTATION\"
Copy-Item "c:\Users\bigge\OneDrive\Documents\PROJECTS\HEALTH-SEC\PROJECT_SUMMARY_COMPLETE.md" "C:\Temp\HealthSec_Flash\DOCUMENTATION\"
Copy-Item "c:\Users\bigge\OneDrive\Documents\PROJECTS\HEALTH-SEC\THESIS_CHAPTERS_3-5.md" "C:\Temp\HealthSec_Flash\DOCUMENTATION\"
Copy-Item "c:\Users\bigge\OneDrive\Documents\PROJECTS\HEALTH-SEC\SYSTEM_GUIDE_SIMPLE.md" "C:\Temp\HealthSec_Flash\DOCUMENTATION\"
Copy-Item "c:\Users\bigge\OneDrive\Documents\PROJECTS\HEALTH-SEC\QUICK_REFERENCE.md" "C:\Temp\HealthSec_Flash\DOCUMENTATION\"
Copy-Item "c:\Users\bigge\OneDrive\Documents\PROJECTS\HEALTH-SEC\DATASET_SETUP.md" "C:\Temp\HealthSec_Flash\DOCUMENTATION\"
Copy-Item "c:\Users\bigge\OneDrive\Documents\PROJECTS\HEALTH-SEC\GITHUB_SETUP.md" "C:\Temp\HealthSec_Flash\DOCUMENTATION\"

echo "✓ Documentation copied"
```

---

## Step 7: Create Step-by-Step Setup Guide for Owner

Create file: `C:\Temp\HealthSec_Flash\SETUP_INSTRUCTIONS\00_START_HERE.txt`

```text
═══════════════════════════════════════════════════════════════════════
  HEALTHSEC CRIC HMS — QUICK START FOR OWNER
═══════════════════════════════════════════════════════════════════════

IMPORTANT: Read this file FIRST before doing anything!

This flash drive contains the complete HealthSec system ready to run
on your computer. Follow the steps below to get it working.

CONTENTS OF THIS FLASH DRIVE:
───────────────────────────────────────────────────────────────────────
1. HealthSec/              ← Main application code
2. SETUP_INSTRUCTIONS/     ← Setup guides
3. DOCUMENTATION/          ← Guides and references

SYSTEM REQUIREMENTS:
───────────────────────────────────────────────────────────────────────
✓ Windows 10/11 or Mac/Linux
✓ Python 3.11 or higher (download from python.org)
✓ Internet connection (to install packages)
✓ 2 GB free disk space
✓ Administrator access on your computer

QUICK START (10 MINUTES):
───────────────────────────────────────────────────────────────────────

STEP 1: Install Python (if not already installed)
  1. Go to https://www.python.org/
  2. Click "Downloads"
  3. Download Python 3.11 or 3.12
  4. Run installer
  5. ✓ CHECK: "Add Python to PATH"
  6. Click Install

STEP 2: Copy HealthSec to Your Computer
  1. Plug in this flash drive
  2. Copy the "HealthSec" folder to: C:\Projects\HealthSec
     (Create C:\Projects folder if it doesn't exist)
  3. Open PowerShell or Command Prompt
  4. Type: cd C:\Projects\HealthSec
  5. Verify you're in right folder (you should see "manage.py")

STEP 3: Create Virtual Environment
  1. In PowerShell, type:
     python -m venv venv
  2. Activate virtual environment:
     .\venv\Scripts\Activate.ps1
  3. You should see "(venv)" at start of command line

STEP 4: Install Dependencies
  1. Type:
     pip install -r requirements.txt
  2. Wait for installation to complete (2-3 minutes)

STEP 5: Configure Environment
  1. Copy .env.example to .env:
     copy .env.example .env
  2. Open .env in Notepad:
     notepad .env
  3. Set DJANGO_SECRET_KEY to random value (keep default for now)
  4. Save file

STEP 6: Create Database
  1. Type:
     python manage.py migrate
  2. Wait for database to be created

STEP 7: Create Admin Account
  1. Type:
     python manage.py createsuperuser
  2. Enter username: admin
  3. Enter email: admin@example.com
  4. Enter password: (choose your own, min 8 chars)
  5. Confirm password

STEP 8: Run Development Server
  1. Type:
     python manage.py runserver
  2. Wait for message: "Starting development server at http://127.0.0.1:8000/"
  3. Open web browser
  4. Go to: http://127.0.0.1:8000/
  5. Login with username "admin" and password you created

STEP 9: Load Sample Data (Optional but Recommended)
  1. Open new PowerShell window
  2. Go to project folder: cd C:\Projects\HealthSec
  3. Activate venv: .\venv\Scripts\Activate.ps1
  4. Open Django shell: python manage.py shell
  5. Type these commands:
     >>> from tools.load_nslkdd_real import load_nslkdd_real
     >>> load_nslkdd_real('tools/KDDTrain+.csv', limit=1000)
  6. Wait for "✓ SUCCESS" message
  7. Type: exit()

STEP 10: See the System Running
  1. Go back to browser showing http://127.0.0.1:8000/
  2. Refresh the page
  3. You should now see the Dashboard with real data!

═══════════════════════════════════════════════════════════════════════

TROUBLESHOOTING:
───────────────────────────────────────────────────────────────────────

Q: "Python is not recognized"
A: Python not installed or not in PATH. 
   - Go to python.org and install again
   - Make sure to CHECK "Add Python to PATH"

Q: "No module named django"
A: Dependencies not installed.
   - Make sure venv is activated (see "(venv)" in command line)
   - Run: pip install -r requirements.txt

Q: "Database error"
A: Run migrations:
   - python manage.py migrate

Q: "Port 8000 already in use"
A: Use different port:
   - python manage.py runserver 8001

Q: "Cannot login"
A: Create new admin:
   - python manage.py createsuperuser

Q: "NSL-KDD file not found"
A: Download from Kaggle:
   - Visit kaggle.com/search?q=NSL-KDD
   - Download KDDTrain+.csv
   - Put in HealthSec/tools/ folder
   - Try load command again

═══════════════════════════════════════════════════════════════════════

DOCUMENTATION:
───────────────────────────────────────────────────────────────────────

In the DOCUMENTATION folder, you'll find:

1. QUICK_REFERENCE.md
   - 2-minute overview of system
   - Print this for quick reference

2. HOW_TO_USE.md
   - Detailed guide for every page
   - What each feature does
   - How to operate the system

3. README.md
   - Setup guide with all commands
   - Feature list

4. SYSTEM_GUIDE_SIMPLE.md
   - Non-technical explanation
   - Good for explaining to others

5. PROJECT_SUMMARY_COMPLETE.md
   - Full technical reference
   - All features documented

6. THESIS_CHAPTERS_3-5.md
   - Academic format
   - For thesis chapters

═══════════════════════════════════════════════════════════════════════

NEXT STEPS:
───────────────────────────────────────────────────────────────────────

1. ✓ Read this file (you're doing it!)
2. ✓ Follow QUICK START steps above
3. ✓ Explore the system
4. ✓ Read HOW_TO_USE.md for detailed guides
5. ✓ Check QUICK_REFERENCE.md for features

NEED HELP?
───────────────────────────────────────────────────────────────────────

If you get stuck:
1. Check TROUBLESHOOTING section above
2. Read SETUP_INSTRUCTIONS/DETAILED_SETUP.md
3. Check DOCUMENTATION/README.md
4. Review HOW_TO_USE.md for your specific question

═══════════════════════════════════════════════════════════════════════

Good luck! The system is ready to use.

Setup time: ~15 minutes
First data load: ~2 minutes
Total: ~20 minutes to full working system

═══════════════════════════════════════════════════════════════════════
```

---

## Step 8: Create Detailed Setup Instructions

Create file: `C:\Temp\HealthSec_Flash\SETUP_INSTRUCTIONS\DETAILED_SETUP.md`

