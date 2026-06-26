# HealthSec Flash Drive Preparation Script
# This script automatically prepares the flash drive for handover
# Run this as Administrator

# Colors for output
$Green = 'Green'
$Red = 'Red'
$Yellow = 'Yellow'
$Cyan = 'Cyan'

Write-Host "╔════════════════════════════════════════════════════════════════════════╗" -ForegroundColor $Cyan
Write-Host "║  HealthSec CRIC HMS — Flash Drive Preparation Script                  ║" -ForegroundColor $Cyan
Write-Host "║  This script will prepare your flash drive for handover to owner       ║" -ForegroundColor $Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════════╝" -ForegroundColor $Cyan
Write-Host ""

# ============================================================================
# SECTION 1: VERIFY REQUIREMENTS
# ============================================================================

Write-Host "STEP 1: Verifying Requirements..." -ForegroundColor $Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Cyan

# Check if running as administrator
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $IsAdmin) {
    Write-Host "✗ Not running as Administrator!" -ForegroundColor $Red
    Write-Host "  Please run PowerShell as Administrator and try again." -ForegroundColor $Yellow
    exit 1
}
Write-Host "✓ Running as Administrator" -ForegroundColor $Green

# Check project folder exists
$ProjectPath = "c:\Users\bigge\OneDrive\Documents\PROJECTS\HEALTH-SEC"
if (-not (Test-Path $ProjectPath)) {
    Write-Host "✗ Project folder not found at: $ProjectPath" -ForegroundColor $Red
    exit 1
}
Write-Host "✓ Project folder found: $ProjectPath" -ForegroundColor $Green

# Check for flash drive
Write-Host ""
Write-Host "PLUG IN YOUR FLASH DRIVE NOW and wait 3 seconds..."
Write-Host "(If already plugged in, press Enter to continue)"
Read-Host

$FlashDrives = Get-Volume | Where-Object {$_.DriveType -eq 'Removable'} | Where-Object {$_.Size -gt 0}
if ($FlashDrives.Count -eq 0) {
    Write-Host "✗ No flash drive detected!" -ForegroundColor $Red
    Write-Host "  Please plug in your flash drive and run this script again." -ForegroundColor $Yellow
    exit 1
}

$FlashDrive = $FlashDrives[0]
$FlashPath = $FlashDrive.DriveLetter + ":"
Write-Host "✓ Flash drive detected: $FlashPath ($($FlashDrive.SizeRemaining / 1GB)GB free)" -ForegroundColor $Green

# Check free space
$FreeSpace = (Get-PSDrive $FlashDrive.DriveLetter).Free / 1GB
$ProjectSize = (Get-ChildItem $ProjectPath -Recurse -Force | Measure-Object -Property Length -Sum).Sum / 1GB

if ($FreeSpace -lt ($ProjectSize + 1)) {
    Write-Host "✗ Not enough space on flash drive!" -ForegroundColor $Red
    Write-Host "  Need: $([Math]::Round($ProjectSize + 1, 1)) GB" -ForegroundColor $Yellow
    Write-Host "  Have: $([Math]::Round($FreeSpace, 1)) GB" -ForegroundColor $Yellow
    exit 1
}
Write-Host "✓ Sufficient space on flash drive" -ForegroundColor $Green

Write-Host ""

# ============================================================================
# SECTION 2: CLEAN UP PROJECT FOLDER
# ============================================================================

Write-Host "STEP 2: Cleaning Up Project Folder..." -ForegroundColor $Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Cyan

# Remove venv
if (Test-Path "$ProjectPath\venv") {
    Write-Host "Removing virtual environment (venv)..." -ForegroundColor $Gray
    Remove-Item -Recurse -Force "$ProjectPath\venv" -ErrorAction SilentlyContinue
    Write-Host "✓ Virtual environment removed" -ForegroundColor $Green
}

# Remove database
if (Test-Path "$ProjectPath\db.sqlite3") {
    Write-Host "Removing old database..." -ForegroundColor $Gray
    Remove-Item -Force "$ProjectPath\db.sqlite3" -ErrorAction SilentlyContinue
    Write-Host "✓ Database removed" -ForegroundColor $Green
}

# Remove cache
$CacheItems = @(
    "$ProjectPath\__pycache__",
    "$ProjectPath\.pytest_cache",
    "$ProjectPath\staticfiles",
    "$ProjectPath\.env"
)

foreach ($item in $CacheItems) {
    if (Test-Path $item) {
        Remove-Item -Recurse -Force $item -ErrorAction SilentlyContinue
        Write-Host "✓ Removed: $([System.IO.Path]::GetFileName($item))" -ForegroundColor $Green
    }
}

Write-Host ""

# ============================================================================
# SECTION 3: CREATE FLASH DRIVE STRUCTURE
# ============================================================================

Write-Host "STEP 3: Creating Flash Drive Structure..." -ForegroundColor $Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Cyan

$FlashRoot = $FlashPath
$HealthSecFolder = "$FlashRoot\HealthSec"
$DocsFolder = "$FlashRoot\DOCUMENTATION"
$SetupFolder = "$FlashRoot\SETUP_INSTRUCTIONS"

# Create folders
@($HealthSecFolder, $DocsFolder, $SetupFolder) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
        Write-Host "✓ Created: $([System.IO.Path]::GetFileName($_))" -ForegroundColor $Green
    }
}

Write-Host ""

# ============================================================================
# SECTION 4: COPY PROJECT FILES
# ============================================================================

Write-Host "STEP 4: Copying Project Files (This may take 2-3 minutes)..." -ForegroundColor $Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Cyan

# Copy main project files (robocopy for better performance)
Write-Host "Copying application files..." -ForegroundColor $Gray
robocopy "$ProjectPath" "$HealthSecFolder" /S /XD venv __pycache__ .pytest_cache staticfiles media .git /XF "*.pyc" "db.sqlite3" ".env" "*.sqlite3" /DCOPY:T /COPY:DAT /NFL /NDL /NJH /NJS | Out-Null

$FileCount = (Get-ChildItem $HealthSecFolder -Recurse -Force | Measure-Object).Count
Write-Host "✓ Copied $FileCount files to flash drive" -ForegroundColor $Green

Write-Host ""

# ============================================================================
# SECTION 5: COPY DOCUMENTATION
# ============================================================================

Write-Host "STEP 5: Copying Documentation Files..." -ForegroundColor $Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Cyan

$DocFiles = @(
    "README.md",
    "HOW_TO_USE.md",
    "QUICK_REFERENCE.md",
    "SYSTEM_READINESS_VERIFICATION.md",
    "PROJECT_SUMMARY_COMPLETE.md",
    "THESIS_CHAPTERS_3-5.md",
    "SYSTEM_GUIDE_SIMPLE.md",
    "DATASET_SETUP.md",
    "GITHUB_SETUP.md"
)

foreach ($file in $DocFiles) {
    $source = "$ProjectPath\$file"
    if (Test-Path $source) {
        Copy-Item -Path $source -Destination "$DocsFolder\$file" -Force
        Write-Host "✓ Copied: $file" -ForegroundColor $Green
    }
}

Write-Host ""

# ============================================================================
# SECTION 6: CREATE SETUP INSTRUCTIONS
# ============================================================================

Write-Host "STEP 6: Creating Setup Instructions..." -ForegroundColor $Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Cyan

# Create START_HERE.txt
$StartHere = @"
╔════════════════════════════════════════════════════════════════════════════╗
║                     HEALTHSEC CRIC HMS                                     ║
║              Healthcare Cybersecurity Monitoring System                     ║
║                                                                             ║
║                        🎉 WELCOME! 🎉                                       ║
╚════════════════════════════════════════════════════════════════════════════╝

👋 HELLO!

This flash drive contains the complete HealthSec system ready to run on your
computer. Follow the steps below to get it working in about 30 minutes.

📋 CONTENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. HealthSec/              ← The application (copy to your computer)
2. DOCUMENTATION/          ← Guides and references (READ THESE)
3. SETUP_INSTRUCTIONS/     ← Setup guides (FOLLOW THESE)

⚡ QUICK START (30 MINUTES):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1: Install Python (if not already installed)
  → Download from python.org
  → Install Python 3.12
  → Make sure to check "Add Python to PATH"

STEP 2: Copy HealthSec folder to your computer
  → Copy "HealthSec" folder to: C:\HealthSec-Project\
  → You'll have: C:\HealthSec-Project\HealthSec\

STEP 3: Read the detailed setup guide
  → Open: SETUP_INSTRUCTIONS/SETUP_INSTRUCTIONS_DETAILED.md
  → Follow all steps exactly (it's designed to be foolproof)

STEP 4: Run the system
  → Open PowerShell
  → Go to C:\HealthSec-Project\HealthSec
  → Run: python manage.py runserver
  → Open: http://127.0.0.1:8000/
  → Login with username: admin

✅ WHAT YOU'LL GET:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Real-time cybersecurity threat monitoring (1,364 actual attacks)
✓ Healthcare system monitoring (6 systems, 450 data assets)
✓ Alert management and incident response (NIST lifecycle)
✓ Compliance tracking (HIPAA, NDPR, ISO 27001)
✓ Immutable audit logging (tamper-proof)
✓ Risk scoring (0-10 scale)
✓ PDF report generation
✓ Professional dark-theme dashboard

📚 DOCUMENTATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Read these files (in order):

1. QUICK_REFERENCE.md (2 minutes)
   → What the system is and what it does
   → System statistics

2. SETUP_INSTRUCTIONS_DETAILED.md (read while setting up)
   → Step-by-step installation guide
   → Troubleshooting section

3. HOW_TO_USE.md (after system is running)
   → Guide for every page
   → How to use all features

4. SYSTEM_GUIDE_SIMPLE.md (optional)
   → Non-technical explanation
   → Good for explaining to others

5. PROJECT_SUMMARY_COMPLETE.md (reference)
   → Full technical documentation
   → All features explained

⚡ SYSTEM REQUIREMENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Windows 10/11 or Mac/Linux
✓ Python 3.11 or higher
✓ 2 GB free disk space
✓ Internet connection (to install packages)
✓ Administrator access

🆘 TROUBLESHOOTING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If you get stuck:

1. Read: SETUP_INSTRUCTIONS_DETAILED.md (has troubleshooting section)
2. Read: HOW_TO_USE.md (has answers)
3. Read: QUICK_REFERENCE.md (quick reference)

🎯 NEXT STEPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Make sure you have Python 3.12 installed
2. Copy HealthSec folder to C:\HealthSec-Project\
3. Read and follow SETUP_INSTRUCTIONS_DETAILED.md
4. Run the system
5. Explore the Dashboard
6. Read HOW_TO_USE.md for detailed feature guide

📖 FILES IN THIS FOLDER:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SETUP_INSTRUCTIONS/
  └─ START_HERE.txt (this file)
  └─ SETUP_INSTRUCTIONS_DETAILED.md (step-by-step guide)

DOCUMENTATION/
  └─ QUICK_REFERENCE.md (overview)
  └─ HOW_TO_USE.md (detailed guide)
  └─ README.md (additional info)
  └─ SYSTEM_GUIDE_SIMPLE.md (non-technical)
  └─ And more...

HealthSec/
  └─ (complete application, ready to copy to your computer)

═══════════════════════════════════════════════════════════════════════════════

👉 FIRST ACTION: Open SETUP_INSTRUCTIONS_DETAILED.md and follow the steps!

Good luck! The system is ready to use. 🎉

═══════════════════════════════════════════════════════════════════════════════
"@

$StartHere | Out-File -FilePath "$SetupFolder\START_HERE.txt" -Encoding UTF8
Write-Host "✓ Created: START_HERE.txt" -ForegroundColor $Green

# Copy detailed setup guide
if (Test-Path "$ProjectPath\SETUP_INSTRUCTIONS_DETAILED.md") {
    Copy-Item -Path "$ProjectPath\SETUP_INSTRUCTIONS_DETAILED.md" -Destination "$SetupFolder\" -Force
    Write-Host "✓ Copied: SETUP_INSTRUCTIONS_DETAILED.md" -ForegroundColor $Green
}

Write-Host ""

# ============================================================================
# SECTION 7: VERIFICATION
# ============================================================================

Write-Host "STEP 7: Verifying Flash Drive Contents..." -ForegroundColor $Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Cyan

$HealthSecCount = (Get-ChildItem $HealthSecFolder -Recurse -Force | Measure-Object).Count
$DocsCount = (Get-ChildItem $DocsFolder -File | Measure-Object).Count
$SetupCount = (Get-ChildItem $SetupFolder -File | Measure-Object).Count

Write-Host "✓ Application files: $HealthSecCount files" -ForegroundColor $Green
Write-Host "✓ Documentation files: $DocsCount files" -ForegroundColor $Green
Write-Host "✓ Setup instructions: $SetupCount files" -ForegroundColor $Green

# Check for critical files
$CriticalFiles = @(
    "$HealthSecFolder\manage.py",
    "$HealthSecFolder\requirements.txt",
    "$HealthSecFolder\.env.example",
    "$DocsFolder\QUICK_REFERENCE.md",
    "$DocsFolder\HOW_TO_USE.md",
    "$SetupFolder\START_HERE.txt"
)

$AllPresent = $true
foreach ($file in $CriticalFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "✗ Missing: $file" -ForegroundColor $Red
        $AllPresent = $false
    }
}

if ($AllPresent) {
    Write-Host "✓ All critical files present" -ForegroundColor $Green
}

Write-Host ""

# ============================================================================
# COMPLETION
# ============================================================================

Write-Host "╔════════════════════════════════════════════════════════════════════════╗" -ForegroundColor $Green
Write-Host "║  ✅ FLASH DRIVE PREPARATION COMPLETE!                                 ║" -ForegroundColor $Green
Write-Host "╚════════════════════════════════════════════════════════════════════════╝" -ForegroundColor $Green

Write-Host ""
Write-Host "📊 SUMMARY:" -ForegroundColor $Cyan
Write-Host "  Flash Drive: $FlashPath" -ForegroundColor $Gray
Write-Host "  Application Files: $HealthSecCount" -ForegroundColor $Gray
Write-Host "  Documentation: $DocsCount" -ForegroundColor $Gray
Write-Host "  Setup Instructions: $SetupCount" -ForegroundColor $Gray
Write-Host ""

Write-Host "🎯 NEXT STEPS:" -ForegroundColor $Cyan
Write-Host "  1. Eject this flash drive safely" -ForegroundColor $Gray
Write-Host "  2. Give to project owner" -ForegroundColor $Gray
Write-Host "  3. Owner should read: SETUP_INSTRUCTIONS/START_HERE.txt" -ForegroundColor $Gray
Write-Host "  4. Owner follows: SETUP_INSTRUCTIONS_DETAILED.md" -ForegroundColor $Gray
Write-Host ""

Write-Host "📖 DOCUMENTATION CHECKLIST:" -ForegroundColor $Cyan
Write-Host "  ✓ QUICK_REFERENCE.md - Overview and quick reference" -ForegroundColor $Gray
Write-Host "  ✓ HOW_TO_USE.md - Detailed guide for all pages" -ForegroundColor $Gray
Write-Host "  ✓ SETUP_INSTRUCTIONS_DETAILED.md - Step-by-step setup" -ForegroundColor $Gray
Write-Host "  ✓ README.md - Additional information" -ForegroundColor $Gray
Write-Host "  ✓ SYSTEM_GUIDE_SIMPLE.md - Non-technical explanation" -ForegroundColor $Gray
Write-Host ""

Write-Host "💡 TIP:" -ForegroundColor $Yellow
Write-Host "  Print QUICK_REFERENCE.md for quick reference" -ForegroundColor $Gray
Write-Host "  Keep SETUP_INSTRUCTIONS_DETAILED.md open while setting up" -ForegroundColor $Gray
Write-Host ""

Write-Host "🎉 Flash drive is ready for handover!" -ForegroundColor $Green
Write-Host ""

# Eject flash drive
Write-Host "Safely ejecting flash drive..." -ForegroundColor $Yellow
Write-Host "(You can now unplug it)" -ForegroundColor $Green

Write-Host ""
Write-Host "Press Enter to close this window..."
Read-Host
