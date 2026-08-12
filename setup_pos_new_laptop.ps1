# setup_pos_new_laptop.ps1
# One-shot setup for khub-pos-tests (Appium + Android emulator) on a new machine.
# Run as Administrator for best results.
# Usage: Right-click -> "Run as Administrator"
#
# Safe to re-run: every step is idempotent and skips work that's already done.
# Two things this script CANNOT do for you:
#   1. Android Studio's first-run wizard is a GUI flow (license + SDK download) -
#      the script installs Android Studio, then asks you to launch it once and
#      re-run the script afterwards.
#   2. The KHub POS APK is gitignored and not fetchable by this script - get
#      app-release.apk from the dev team and drop it at data\apk\app-release.apk.

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

# 0. Force known install locations onto THIS session's PATH up front.
#    winget/npm installs update the User/Machine PATH in the registry, but a
#    PowerShell process that was already running (or spawned by a host that
#    cached its own environment block) will not pick that up until a new
#    process reads the registry fresh. Rather than rely on that, just prepend
#    every location this script installs into - idempotent, and makes every
#    Get-Command check below reliable regardless of session history.
Write-Step "Refreshing session PATH for known tool locations"
$knownPaths = @(
    "C:\Program Files\nodejs",
    "$env:APPDATA\npm",
    "$sdkPath\platform-tools",
    "$sdkPath\emulator",
    "$sdkPath\cmdline-tools\latest\bin"
)
foreach ($p in $knownPaths) {
    if ((Test-Path $p) -and ($env:PATH -notlike "*$p*")) {
        $env:PATH = "$p;$env:PATH"
    }
}
Write-OK "Session PATH refreshed"

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
    if ($env:PATH -notlike "*$javaHome\bin*") { $env:PATH = "$javaHome\bin;" + $env:PATH }
    Write-OK "JAVA_HOME = $javaHome (any JDK 11+ works fine - uiautomator2 doesn't require exactly 11)"
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
        # Installer runs an elevated MSI - expect a UAC prompt if not already Administrator.
        if ($env:PATH -notlike "*C:\Program Files\nodejs*") { $env:PATH = "C:\Program Files\nodejs;" + $env:PATH }
        Write-OK "Node.js installed"
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
    if ($env:PATH -notlike "*$env:APPDATA\npm*") { $env:PATH = "$env:APPDATA\npm;" + $env:PATH }
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
    $recheck = appium driver list --installed 2>&1
    if ($recheck -match "uiautomator2") { Write-OK "uiautomator2 driver installed" }
    else { Write-Fail "uiautomator2 driver install did not verify - re-run this script" }
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
    Write-Warn "After Android Studio finishes its first-run setup wizard (GUI - this script can't drive it), re-run this script to continue."
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

# 8. Android SDK command-line tools (sdkmanager / avdmanager)
#    Android Studio's first-run wizard does NOT reliably install these - it
#    only guarantees platform-tools/build-tools/emulator. Without cmdline-tools
#    there's no sdkmanager/avdmanager, so download it directly the same way
#    Android Studio itself would (official Google-hosted zip, checksum verified).
Write-Step "Checking Android SDK command-line tools (sdkmanager / avdmanager)"
$sdkManager = "$sdkPath\cmdline-tools\latest\bin\sdkmanager.bat"
if (-not (Test-Path $sdkManager)) {
    $found = Get-ChildItem "$sdkPath\cmdline-tools" -Recurse -Filter "sdkmanager.bat" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { $sdkManager = $found.FullName } else { $sdkManager = $null }
}

if (-not $sdkManager) {
    Write-Info "cmdline-tools not found - downloading directly from dl.google.com..."
    # If this specific build 404s (Google rotates these periodically), grab the
    # current one from https://developer.android.com/studio#command-line-tools-only
    # and update the URL/hash below.
    $cmdToolsUrl  = "https://dl.google.com/android/repository/commandlinetools-win-15859902_latest.zip"
    $expectedHash = "90AE805D20434428BFFCB699C290860F19BB5F66A67E6B330067E3DE801FB04A"
    $zipPath = "$env:TEMP\cmdline-tools.zip"
    try {
        Invoke-WebRequest -Uri $cmdToolsUrl -OutFile $zipPath
        $actualHash = (Get-FileHash $zipPath -Algorithm SHA256).Hash
        if ($actualHash -ne $expectedHash) {
            Write-Fail "Checksum mismatch for cmdline-tools zip (got $actualHash) - not installing. Download manually from https://developer.android.com/studio#command-line-tools-only"
        } else {
            $extractDir = "$env:TEMP\cmdline-tools-extract"
            Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force
            New-Item -ItemType Directory -Force -Path "$sdkPath\cmdline-tools" | Out-Null
            if (Test-Path "$sdkPath\cmdline-tools\latest") { Remove-Item "$sdkPath\cmdline-tools\latest" -Recurse -Force }
            Move-Item "$extractDir\cmdline-tools" "$sdkPath\cmdline-tools\latest"
            Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
            $sdkManager = "$sdkPath\cmdline-tools\latest\bin\sdkmanager.bat"
            if ($env:PATH -notlike "*cmdline-tools\latest\bin*") { $env:PATH = "$sdkPath\cmdline-tools\latest\bin;" + $env:PATH }
            Write-OK "cmdline-tools installed (checksum verified)"
        }
    } catch {
        Write-Fail "Failed to download cmdline-tools: $_"
        Write-Warn "Install manually: Android Studio -> SDK Manager -> SDK Tools -> Android SDK Command-line Tools (latest)"
    }
} else {
    Write-OK "cmdline-tools already present"
}

# 9. Accept SDK licenses, then install API 35 platform + system image
Write-Step "Checking Android SDK components (API 35 / Android 15)"
if ($sdkManager) {
    Write-Info "Accepting SDK licenses..."
    $licenseAnswers = (1..10 | ForEach-Object { "y" }) -join "`n"
    $licenseAnswers | & $sdkManager --licenses *> $null

    $installed = & $sdkManager --list_installed 2>&1
    if ($installed -match "android-35") {
        Write-OK "Android 35 platform/system image already installed"
    } else {
        Write-Info "Downloading Android 15 (API 35) platform + system image (large - may take several minutes)..."
        & $sdkManager "platform-tools" "platforms;android-35" "system-images;android-35;google_apis;x86_64" "emulator" 2>&1 |
            Where-Object { $_ -match "\[|\bDone\b" }
        Write-OK "SDK components installed"
    }
} else {
    Write-Warn "sdkmanager not found - install API 35 manually in Android Studio:"
    Write-Warn "  SDK Manager -> SDK Platforms -> Android 15 (API 35)"
    Write-Warn "  SDK Manager -> SDK Tools -> Android Emulator, Platform-Tools, Command-line Tools"
}

# 10. Create Pixel_Tablet AVD
Write-Step "Checking Pixel_Tablet emulator (Android 15)"
$avdManager  = "$sdkPath\cmdline-tools\latest\bin\avdmanager.bat"
if (-not (Test-Path $avdManager)) {
    $found2 = Get-ChildItem "$sdkPath\cmdline-tools" -Recurse -Filter "avdmanager.bat" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found2) { $avdManager = $found2.FullName } else { $avdManager = $null }
}
$emulatorExe = "$sdkPath\emulator\emulator.exe"
$avdCreatedNow = $false

if (Test-Path $emulatorExe) {
    $avds = & $emulatorExe -list-avds 2>&1
    if ($avds -match "Pixel_Tablet") {
        Write-OK "Pixel_Tablet AVD already exists"
    } elseif ($avdManager) {
        Write-Info "Creating Pixel_Tablet AVD..."
        "no" | & $avdManager create avd --name "Pixel_Tablet" --package "system-images;android-35;google_apis;x86_64" --device "pixel_tablet" --force 2>&1
        Write-OK "Pixel_Tablet AVD created"
        $avdCreatedNow = $true
    } else {
        Write-Warn "avdmanager not found - create the AVD manually in Android Studio:"
        Write-Warn "  Device Manager -> Create Virtual Device -> Pixel Tablet -> Android 15"
        Write-Warn "  Name it exactly: Pixel_Tablet"
    }
} else {
    Write-Warn "Emulator exe not found - install Android Emulator via Android Studio SDK Manager"
}

# 11. Prepare the emulator for automation (one-time device settings)
#     Two Android system dialogs will otherwise silently break every test:
#       - "Viewing full screen" immersive-mode confirmation, shown the first
#         time an app goes full-screen. It's a separate system-level overlay
#         window that covers the app and makes Appium's element search fail
#         with NoSuchElementError, even though the app rendered fine.
#       - "Try out your stylus" handwriting tip. The Pixel Tablet profile
#         reports stylus support, so Android 15 treats every touch as if it
#         came from a stylus (see debug.input.simulate_stylus_with_touch) and
#         shows this tip the first time a text field is focused, swallowing
#         the tap that was meant for whatever's underneath it.
#     Both are one-time-per-AVD-data settings, so this only needs to run once
#     per machine - but it's cheap and idempotent, so it just runs every time.
Write-Step "Preparing emulator for automation (suppressing one-time system dialogs)"
$adbExe = "$sdkPath\platform-tools\adb.exe"
if ((Test-Path $emulatorExe) -and (Test-Path $adbExe)) {
    $avds = & $emulatorExe -list-avds 2>&1
    if ($avds -match "Pixel_Tablet") {
        Write-Info "Booting Pixel_Tablet headlessly to apply device settings..."
        $emuProc = Start-Process -FilePath $emulatorExe -ArgumentList "-avd Pixel_Tablet -gpu off -no-window -no-audio" -PassThru
        & $adbExe wait-for-device
        $bootedOk = $false
        for ($i = 0; $i -lt 60; $i++) {
            $booted = (& $adbExe shell getprop sys.boot_completed 2>$null).Trim()
            if ($booted -eq "1") { $bootedOk = $true; break }
            Start-Sleep -Seconds 3
        }
        if ($bootedOk) {
            & $adbExe shell settings put secure immersive_mode_confirmations confirmed
            & $adbExe shell setprop debug.input.simulate_stylus_with_touch false
            Write-OK "Applied immersive_mode_confirmations + disabled stylus-touch simulation"
        } else {
            Write-Warn "Emulator did not report boot_completed within 180s - settings not applied, re-run this script"
        }
        & $adbExe emu kill 2>$null | Out-Null
        Start-Sleep -Seconds 3
        if (-not $emuProc.HasExited) { Stop-Process -Id $emuProc.Id -Force -ErrorAction SilentlyContinue }
    } else {
        Write-Warn "Pixel_Tablet AVD not found - skipping (create it first, see step above)"
    }
} else {
    Write-Warn "emulator.exe or adb.exe not found - skipping device-settings step"
}

# 12. Python venv
Write-Step "Setting up Python virtual environment"
# Bare `python`/`py` can resolve to the Windows Store's execution-alias stub
# (prints an install prompt and exits, no error) instead of a real interpreter
# if Python was installed standalone rather than via the Store. Detect and
# route around that explicitly rather than trusting Get-Command alone.
$pyExe = $null
$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pyCmd -and ($pyCmd.Source -notlike "*WindowsApps*")) {
    $pyExe = $pyCmd.Source
} else {
    $pyCandidate = Get-ChildItem "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1
    if ($pyCandidate) { $pyExe = $pyCandidate.FullName }
}

if (-not $pyExe) {
    Write-Fail "Python not found. Download from https://python.org (NOT the Microsoft Store version - it can cause PATH issues)"
} else {
    Write-OK "$(& $pyExe --version 2>&1) at $pyExe"
    if (-not (Test-Path "venv\Scripts\python.exe")) {
        & $pyExe -m venv venv
        Write-OK "venv created"
    } else {
        Write-OK "venv already exists"
    }
    & "venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
    & "venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet
    Write-OK "Python dependencies installed"
}

# 13. Quick validation
Write-Step "Validating Python imports"
if (Test-Path "venv\Scripts\python.exe") {
    $check = & "venv\Scripts\python.exe" -c "import appium; import pytest; import yaml; import openpyxl; print('imports OK')" 2>&1
    if ($check -match "imports OK") { Write-OK $check } else { Write-Warn $check }
} else {
    Write-Warn "venv not created - skipping import check"
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete"                          -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
Write-Host "  Installed / configured:" -ForegroundColor White
Write-Host "    Java JDK             -> JAVA_HOME" -ForegroundColor White
Write-Host "    Node.js + Appium 3   -> uiautomator2 driver" -ForegroundColor White
Write-Host "    Android SDK API 35   -> ANDROID_HOME + PATH" -ForegroundColor White
Write-Host "    Pixel_Tablet AVD     -> Android 15" -ForegroundColor White
Write-Host "    Emulator settings    -> immersive-mode + stylus-tip dialogs suppressed" -ForegroundColor White
Write-Host "    Python venv          -> requirements installed" -ForegroundColor White

Write-Host "`n  To run POS tests:" -ForegroundColor White
Write-Host "  1. Start emulator : & `"`$env:ANDROID_HOME\emulator\emulator.exe`" -avd Pixel_Tablet -gpu off" -ForegroundColor White
Write-Host "  2. Start Appium   : appium" -ForegroundColor White
Write-Host "  3. Run tests      : venv\Scripts\python.exe -m pytest tests/ -v" -ForegroundColor White
Write-Host ""
Write-Host "  NOTE: Install the KHub POS APK on the emulator before first run:" -ForegroundColor Yellow
Write-Host "  adb install data\apk\app-release.apk" -ForegroundColor Yellow
Write-Host "  (app-release.apk is gitignored - get it from the dev team; this script cannot fetch it)" -ForegroundColor Yellow
Write-Host ""
