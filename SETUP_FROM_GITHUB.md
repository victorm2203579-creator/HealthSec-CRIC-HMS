# Setup HealthSec from GitHub

**Recommended Method** — Clone the latest code directly from GitHub and run on your system.

---

## Prerequisites

Before starting, make sure you have:

- ✅ **Python 3.12+** installed ([download here](https://www.python.org/downloads/))
- ✅ **Git** installed ([download here](https://git-scm.com/download/win))
- ✅ **Administrator access** to your computer
- ✅ **Internet connection** (to clone from GitHub)

---

## Step-by-Step Setup (10 minutes)

### Step 1: Clone the Repository

Open PowerShell and run:

```powershell
git clone https://github.com/victorm2203579-creator/HealthSec-CRIC-HMS.git
cd HealthSec-CRIC-HMS
```

**Expected output:**
```
Cloning into 'HealthSec-CRIC-HMS'...
remote: Enumerating objects...
... (will show progress)
```

---

### Step 2: Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Verify activation:**
You should see `(venv)` at the start of your PowerShell prompt.

---

### Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

**This will take 2-3 minutes.** You'll see:
```
Successfully installed django-4.2.30, ...
```

---

### Step 4: Configure Environment

Copy the example environment file:

```powershell
Copy-Item .env.example -Destination .env
```

Edit `.env` (optional — defaults work for development):

```powershell
# If you want to use PowerShell to edit:
notepad .env

# OR just leave defaults for development
```

**Minimum required (usually pre-configured):**
```
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DB_ENGINE=sqlite
```

---

### Step 5: Apply Database Migrations

```powershell
python manage.py migrate
```

**Expected output:**
```
Operations to perform:
  Apply all migrations: admin, auth, ...
Running migrations:
  Applying ... OK
  ...
Applied X migrations.
```

---

### Step 6: Create Admin Account

```powershell
python manage.py createsuperuser
```

**Follow the prompts:**
```
Username: admin
Email address: your-email@example.com
Password: (create secure password)
Password (again): (confirm password)
Superuser created successfully.
```

---

### Step 7: Start the Development Server

```powershell
python manage.py runserver
```

**Expected output:**
```
Watching for file changes with StatReloader
Performing system checks...
System check identified no issues (0 silenced).

Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

### Step 8: Access the System

1. **Open your browser** → Go to: `http://127.0.0.1:8000/`
2. **Login** with your admin username and password
3. **Explore the dashboard!**

You should see:
- ✅ Dashboard with 729 monitoring events
- ✅ 6 healthcare systems
- ✅ 55 alerts and 4 incidents
- ✅ Compliance frameworks (HIPAA, NDPR, NIST, ISO 27001)
- ✅ Real cybersecurity data

---

## Next Steps

### To Load More Data (Optional)

```powershell
python manage.py shell
```

Inside the shell:

```python
from tools.load_nslkdd_real import load_nslkdd_real
load_nslkdd_real()
```

### To Stop the Server

Press `CTRL+C` in the PowerShell window.

### To Restart Later

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start server
python manage.py runserver
```

---

## Troubleshooting

### "git is not recognized"

**Solution:** Install Git from https://git-scm.com/download/win

Then restart PowerShell and try again.

### "python is not recognized"

**Solution:** Install Python from https://www.python.org/downloads/

Make sure to check **"Add Python to PATH"** during installation.

Then restart PowerShell and try again.

### "(venv) is not showing in my prompt"

**Solution:** Run the activation script again:

```powershell
.\venv\Scripts\Activate.ps1
```

If you get a permission error, run PowerShell as Administrator.

### "No module named django"

**Solution:** Make sure virtual environment is activated (you should see `(venv)` in prompt).

Then reinstall dependencies:

```powershell
pip install -r requirements.txt
```

### "Port 8000 already in use"

**Solution:** Run on a different port:

```powershell
python manage.py runserver 8001
```

Then go to: `http://127.0.0.1:8001/`

### "Cannot login"

**Solution:** Create a new admin account:

```powershell
python manage.py createsuperuser
```

Then use the new username/password to login.

### "Cannot connect to database"

**Solution:** Make sure migrations were applied:

```powershell
python manage.py migrate
```

---

## What You Have

After setup, your system includes:

✅ **Threat Monitoring** — 729 real cybersecurity events  
✅ **Healthcare Systems** — 6 monitored systems  
✅ **Alert Management** — 55 alerts, 4 incidents  
✅ **Compliance Tracking** — HIPAA, NDPR, NIST, ISO 27001  
✅ **Risk Scoring** — 0-10 risk scale  
✅ **Audit Logging** — 246 immutable audit entries  
✅ **PDF Reports** — Generate compliance & risk reports  
✅ **Dark Theme UI** — Professional Bootstrap 5 interface  

---

## Documentation

For detailed information about using the system:

📖 **HOW_TO_USE.md** — Complete feature guide  
📖 **QUICK_REFERENCE.md** — Quick answers  
📖 **README.md** — Project overview  

---

## Getting Updates

To get the latest updates from GitHub:

```powershell
git pull origin master
pip install -r requirements.txt  # If dependencies changed
python manage.py migrate         # If database changed
```

---

## Need Help?

All answers are in:
- `HOW_TO_USE.md` (comprehensive guide)
- `QUICK_REFERENCE.md` (quick answers)
- This file's Troubleshooting section

---

**Total setup time: ~10 minutes**

**System ready for use: Immediately after Step 8** ✅

---

*Last updated: June 29, 2026*  
*GitHub: https://github.com/victorm2203579-creator/HealthSec-CRIC-HMS*
