# setup_pos_new_laptop.ps1
# One-shot setup for khub-pos-tests (Appium + Android emulator) on a new machine.
# Run as Administrator for best results.
# Usage: Right-click -> "Run as Administrator"

$ErrorActionPreference = "Continue"

function Write-Step { param($msg) Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-OK   { param($msg) Write-Host "  [OK]   $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "  [FAIL] $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "  [INFO] $msg" -ForegroundColor White }

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  khub-pos-tests - New Laptop Setup"     -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$sdkPath = "C:\Users\$env:USERNAME\AppData\Local\Android\Sdk"

# 1. winget
Write-Step "Checking winget"
$winget = Get-Command winget -ErrorAction SilentlyContinue
if ($winget) { Write-OK "winget found" }
else {
    Write-Warn "winget not found. Install App Installer from Microsoft Store, then re-run."
}

# 2. Java JDK
Write-Step "Checking Java JDK 11+"
$javaCmd  = Get-Command java -ErrorAction SilentlyContinue
$javaHome = $null

if ($javaCmd) {
    $javaHome = Split-Path (Split-Path (Resolve-Path $javaCmd.Source))
    Write-OK "Java already installed at $javaHome"
} else {
    foreach ($root in @("C:\Program Files\Java","C:\Program Files\Eclipse Adoptium","C:\Program Files\Microsoft","C:\Program Files\Zulu")) {
        if (Test-Path $root) {
            $jdk = Get-ChildItem $root | Sort-Object Name -Descending | Select-Object -First 1
            if ($jdk -and (Test-Path "$($jdk.FullName)\bin\java.exe")) {
                $javaHome = $jdk.FullName
                Write-OK "Java found at $javaHome"
                break
            }
        }
    }
}

if (-not $javaHome) {
    Write-Warn "Java not found - installing JDK 11 via winget..."
    if ($winget) {
        winget install EclipseAdoptium.Temurin.11.JDK --silent --accept-package-agreements --accept-source-agreements
        $jdk = Get-ChildItem "C:\Program Files\Eclipse Adoptium" -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
        if ($jdk) { $javaHome = $jdk.FullName }
    } else {
        Write-Fail "Download JDK 11 from https://adoptium.net"
    }
}

if ($javaHome) {
    $env:JAVA_HOME = $javaHome
    [System.Environment]::SetEnvironmentVariable("JAVA_HOME", $javaHome, "User")
    $env:PATH = "$javaHome\bin;" + $env:PATH
    Write-OK "JAVA_HOME = $javaHome"
}

# 3. Node.js
Write-Step "Checking Node.js (required for Appium)"
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCmd) {
    Write-OK "Node.js $(node --version) already installed"
} else {
    Write-Warn "Node.js not found - installing via winget..."
    if ($winget) {
        winget install OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
        $env:PATH = "C:\Program Files\nodejs;" + $env:PATH
        Write-OK "Node.js installed - restart PowerShell if next steps fail"
    } else {
        Write-Fail "Download Node.js LTS from https://nodejs.org"
    }
}

# 4. Appium
Write-Step "Checking Appium"
$appiumCmd = Get-Command appium -ErrorAction SilentlyContinue
if ($appiumCmd) {
    Write-OK "Appium $(appium --version 2>&1) already installed"
} else {
    Write-Info "Installing Appium globally via npm..."
    npm install -g appium
    Write-OK "Appium installed"
}

# 5. UiAutomator2 driver
Write-Step "Checking Appium UiAutomator2 driver"
$driverList = appium driver list --installed 2>&1
if ($driverList -match "uiautomator2") {
    Write-OK "uiautomator2 driver already installed"
} else {
    Write-Info "Installing uiautomator2 driver..."
    appium driver install uiautomator2
    Write-OK "uiautomator2 driver installed"
}

# 6. Android Studio
Write-Step "Checking Android Studio"
if (Test-Path "C:\Program Files\Android\Android Studio") {
    Write-OK "Android Studio found"
} else {
    Write-Warn "Android Studio not found."
    if ($winget) {
        Write-Info "Installing Android Studio via winget (may take several minutes)..."
        winget install Google.AndroidStudio --silent --accept-package-agreements --accept-source-agreements
        Write-OK "Android Studio installed - launch it once to finish SDK setup, then re-run this script"
    } else {
        Write-Fail "Download Android Studio from https://developer.android.com/studio"
    }
    Write-Warn "After Android Studio finishes its first-run setup, re-run this script to continue."
    exit 0
}

# 7. Android SDK env vars
Write-Step "Setting Android SDK environment variables"
if (Test-Path $sdkPath) {
    $env:ANDROID_HOME     = $sdkPath
    $env:ANDROID_SDK_ROOT = $sdkPath
    [System.Environment]::SetEnvironmentVariable("ANDROID_HOME",     $sdkPath, "User")
    [System.Environment]::SetEnvironmentVariable("ANDROID_SDK_ROOT", $sdkPath, "User")

    $currentPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
    $newPaths = @()
    if ($currentPath -notlike "*platform-tools*") { $newPaths += "$sdkPath\platform-tools" }
    if ($currentPath -notlike "*\emulator*")       { $newPaths += "$sdkPath\emulator" }
    if ($newPaths.Count -gt 0) {
        [System.Environment]::SetEnvironmentVariable("PATH", ($newPaths -join ";") + ";" + $currentPath, "User")
        $env:PATH = ($newPaths -join ";") + ";" + $env:PATH
        Write-OK "Added to PATH: $($newPaths -join ', ')"
    }
    Write-OK "ANDROID_HOME = $sdkPath"
} else {
    Write-Warn "Android SDK not found at $sdkPath"
    Write-Warn "Launch Android Studio first, complete the first-run wizard, then re-run this script."
    exit 0
}

# 8. Android SDK components (API 35 / Android 15)
Write-Step "Checking Android SDK components (API 35 / Android 15)"
$sdkManager = "$sdkPath\cmdline-tools\latest\bin\sdkmanager.bat"
if (-not (Test-Path $sdkManager)) {
    $found = Get-ChildItem "$sdkPath\cmdline-tools" -Recurse -Filter "sdkmanager.bat" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { $sdkManager = $found.FullName } else { $sdkManager = $null }
}

if ($sdkManager) {
    $installed = & $sdkManager --list_installed 2>&1
    if ($installed -match "android-35") {
        Write-OK "Android 35 system image already installed"
    } else {
        Write-Info "Downloading Android 35 system image (may take several minutes)..."
        "y" | & $sdkManager "system-images;android-35;google_apis;x86_64" "platforms;android-35" "platform-tools" 2>&1 |
            Where-Object { $_ -match "\[|\bDone\b" }
        Write-OK "SDK components installed"
    }
} else {
    Write-Warn "sdkmanager not found - install API 35 manually in Android Studio:"
    Write-Warn "  SDK Manager -> SDK Platforms -> Android 15 (API 35)"
    Write-Warn "  SDK Manager -> SDK Tools -> Android Emulator, Platform-Tools, Command-line Tools"
}

# 9. Create Pixel_Tablet AVD
Write-Step "Checking Pixel_Tablet emulator (Android 15)"
$avdManager  = "$sdkPath\cmdline-tools\latest\bin\avdmanager.bat"
if (-not (Test-Path $avdManager)) {
    $found2 = Get-ChildItem "$sdkPath\cmdline-tools" -Recurse -Filter "avdmanager.bat" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found2) { $avdManager = $found2.FullName } else { $avdManager = $null }
}
$emulatorExe = "$sdkPath\emulator\emulator.exe"

if (Test-Path $emulatorExe) {
    $avds = & $emulatorExe -list-avds 2>&1
    if ($avds -match "Pixel_Tablet") {
        Write-OK "Pixel_Tablet AVD already exists"
    } elseif ($avdManager) {
        Write-Info "Creating Pixel_Tablet AVD..."
        "no" | & $avdManager create avd --name "Pixel_Tablet" --package "system-images;android-35;google_apis;x86_64" --device "pixel_tablet" --force 2>&1
        Write-OK "Pixel_Tablet AVD created"
    } else {
        Write-Warn "avdmanager not found - create the AVD manually in Android Studio:"
        Write-Warn "  Device Manager -> Create Virtual Device -> Pixel Tablet -> Android 15"
        Write-Warn "  Name it exactly: Pixel_Tablet"
    }
} else {
    Write-Warn "Emulator exe not found - install Android Emulator via Android Studio SDK Manager"
}

# 10. Python venv
Write-Step "Setting up Python virtual environment"
$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pyCmd) {
    Write-Fail "Python not found. Download from https://python.org"
} else {
    Write-OK "$(python --version 2>&1)"
    if (-not (Test-Path "venv\Scripts\activate.ps1")) {
        python -m venv venv
        Write-OK "venv created"
    } else {
        Write-OK "venv already exists"
    }
    & "venv\Scripts\Activate.ps1"
    pip install -r requirements.txt --quiet
    Write-OK "Python dependencies installed"
}

# 11. Quick validation
Write-Step "Validating Python imports"
$check = python -c "import appium; import pytest; import yaml; import openpyxl; print('imports OK')" 2>&1
if ($check -match "imports OK") { Write-OK $check } else { Write-Warn $check }

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete"                          -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
Write-Host "  Installed / configured:" -ForegroundColor White
Write-Host "    Java JDK 11         -> JAVA_HOME" -ForegroundColor White
Write-Host "    Node.js + Appium 3  -> uiautomator2 driver" -ForegroundColor White
Write-Host "    Android SDK API 35  -> ANDROID_HOME + PATH" -ForegroundColor White
Write-Host "    Pixel_Tablet AVD    -> Android 15" -ForegroundColor White
Write-Host "    Python venv         -> requirements installed" -ForegroundColor White

Write-Host "`n  To run POS tests:" -ForegroundColor White
Write-Host "  1. Start emulator : & `"`$env:ANDROID_HOME\emulator\emulator.exe`" -avd Pixel_Tablet" -ForegroundColor White
Write-Host "  2. Start Appium   : appium" -ForegroundColor White
Write-Host "  3. Run tests      : python -m pytest tests/ -v" -ForegroundColor White
Write-Host ""
Write-Host "  NOTE: Install the KHub POS APK on the emulator before first run:" -ForegroundColor Yellow
Write-Host "  adb install data\apk\app-release.apk" -ForegroundColor Yellow
Write-Host ""
