# POS Automation — Command Reference

Project: `C:\Users\mzees\KhubAutomation\khub-pos-tests`

## One-time setup

```powershell
.\setup_pos_new_laptop.ps1
```

Installs Java, Node.js, Appium, Android SDK/AVD, and the Python venv. Idempotent — safe to re-run.

**The APK is not in the repo.** Get `app-release.apk` from the dev team and place it at `data\apk\app-release.apk`.

---

## Running the suite (3 commands, 2 windows)

**Window 1 — Appium (leave running):**

```powershell
appium --allow-insecure uiautomator2:chromedriver_autodownload
```

**Window 2 — emulator, then tests:**

```powershell
& "$env:ANDROID_HOME\emulator\emulator.exe" -avd Pixel_Tablet -gpu off
```

Wait for the home screen to fully load, then:

```powershell
.\run_tests.ps1
```

This reads `data\test_data.xlsx`'s `RunConfig` sheet (environment + Smoke/Regression toggle) and runs the matching tests. The Allure HTML report (`reports\allure-report\index.html`) regenerates automatically when it finishes — nothing else to run.

---

## Adding a new APK build

1. In File Explorer, replace `data\apk\app-release.apk` with the new build — same filename.
2. With the emulator running, one command:
   ```powershell
   & "$env:ANDROID_HOME\platform-tools\adb.exe" install -r data\apk\app-release.apk
   ```

`-r` reinstalls in place (keeps app data, matching how the suite normally runs) — no uninstall, no dragging onto the emulator window needed.

**Edge case:** if the new build is signed with a different key than the old one, that command fails with `INSTALL_FAILED_UPDATE_INCOMPATIBLE`. If so, run this once, then the install command again:
```powershell
& "$env:ANDROID_HOME\platform-tools\adb.exe" uninstall com.anonymous.ititansapp
```

Verify it landed:

```powershell
& "$env:ANDROID_HOME\platform-tools\adb.exe" shell dumpsys package com.anonymous.ititansapp | Select-String "versionCode|versionName|lastUpdateTime"
```

---

## ⚠️ Only run ONE emulator instance at a time

Two sessions driving the same AVD causes device contention that looks like broken locators but isn't.

---

Full troubleshooting notes: see `README.md` → "Troubleshooting notes learned the hard way".
