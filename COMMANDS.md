# POS Automation — Command Reference

Quick reference for running the Android POS automation suite from scratch.
Project: `C:\Users\mzees\PycharmProjects\POSAutomation`

---

## One-time machine setup

Only needed once per machine (see `README.md` Section 1 for full detail):

```powershell
pip install -r requirements.txt
npm install -g appium
appium driver install uiautomator2
```

Set these as permanent User environment variables (System Properties → Environment
Variables), then open a **new** terminal for them to take effect:

| Variable | Value |
|---|---|
| `ANDROID_HOME` | `%LOCALAPPDATA%\Android\Sdk` |
| `ANDROID_SDK_ROOT` | `%LOCALAPPDATA%\Android\Sdk` |
| `Path` (append) | `%ANDROID_HOME%\platform-tools`, `%ANDROID_HOME%\emulator` |

---

## Every time: running the suite from scratch

**You need two PowerShell windows.**

### Window 1 — Appium server (leave running)

```powershell
appium
```
Wait for: `Appium REST http interface listener started on http://0.0.0.0:4723`

> If you get `EADDRINUSE: address already in use 0.0.0.0:4723`, a server is
> already running (maybe from an earlier session) — just skip this step,
> nothing more to do here.

**Not sure if a server is already running?** Check its `/status` endpoint instead of guessing:

```powershell
Invoke-RestMethod http://127.0.0.1:4723/status
```

- Appium runs a local web server on port `4723` while it's active.
- `/status` is a built-in endpoint every Appium server exposes — it responds with JSON describing whether it's ready to accept sessions.
- A response like `{"value":{"ready":true, ...}}` means the server is running and ready — skip starting a new one.
- If nothing responds (connection error instead of JSON), no server is running — go ahead and start one.

### Window 2 — emulator + test run

```powershell
# 1. Start the emulator
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd Pixel_Tablet
```
Wait for the tablet window to fully show the Android home screen. This same
PowerShell window stays usable for the next commands once it boots.

```powershell
# 2. Verify the device is visible
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" devices -l
```
Expect: `emulator-5554   device`

```powershell
# 3. Go to the project and activate the venv
cd C:\Users\mzees\PycharmProjects\POSAutomation
venv\Scripts\activate

# 4. Run the tests
pytest -v --env=emulator
```

> Note: you do **not** need to manually clear app data before running —
> every test automatically resets the app to a logged-out state via
> `adb shell pm clear` (see `conftest.py` / `DriverManager.reset_app_data()`).
> This guarantees each test is independent regardless of run order.

```powershell
# 5. Generate and open the Allure report
allure generate reports\allure-results -o reports\allure-report --clean
allure open reports\allure-report
```

---

## Running specific tests

```powershell
# One test file
pytest tests\login\test_login.py -v --env=emulator

# One specific test
pytest tests\shift\test_clock_in.py::test_clock_in_with_valid_pin -v --env=emulator

# By marker
pytest -m smoke --env=emulator
pytest -m regression --env=emulator
```

---

## Replacing the APK with a new build

Use this whenever a new build of the app is provided and needs to replace what's
currently installed on the emulator.

**Prerequisite:** the emulator must already be running and visible
(`adb devices -l` shows `emulator-5554   device`).

```powershell
# 1. Uninstall the existing app (full removal, not just an update)
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" uninstall com.anonymous.ititansapp
OUTPUT: it'll just say something like "Failure" or similar since there's nothing left to uninstall — that's fine, not an error to worry about.

# 2. Confirm it's actually gone (no output = uninstalled successfully)
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell pm list packages | Select-String ititansapp
OUTOUT: Will Return Empty
```

```
3. Copy the new APK file into the project, replacing the old one, at:
   C:\Users\mzees\PycharmProjects\POSAutomation\data\apk\app-release.apk
```

```
4. Install the new APK by dragging and dropping it onto the emulator window:
     - Open File Explorer to wherever the new APK file is
     - Drag the .apk file directly onto the emulator window and drop it
     - Android installs it automatically (a brief install notification appears)
```

**Verify the install landed** (timestamps should be current, and equal to each
other since it's a fresh install after an uninstall, not an upgrade):

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell dumpsys package com.anonymous.ititansapp | Select-String "versionCode|versionName|lastUpdateTime|firstInstallTime"
```

---

## ⚠️ Only run ONE emulator instance at a time

All tests target the same AVD (`Pixel_Tablet`). If two emulator windows (or
two people) are driving it at once, Appium sessions contend for the same
device and you'll see intermittent `NoSuchElementException` /
"instrumentation process cannot be initialized" errors that look like
locator bugs but are actually just device contention. If someone else needs
to drive the emulator, close your instance first.

---

## Troubleshooting quick reference

| Symptom | Cause | Fix |
|---|---|---|
| Emulator shows black screen / screenshots always show a frozen icon | GPU rendering failure (host can't do hardware GL passthrough) | Already fixed permanently in the AVD config (`hw.gpu.mode=swiftshader_indirect`, backed up at `%USERPROFILE%\.android\avd\Pixel_Tablet.avd\config.ini.bak`). Shouldn't recur. |
| `EADDRINUSE: 0.0.0.0:4723` when starting `appium` | A server is already running | Skip starting a new one — just run pytest directly |
| `NoSuchElementException` that's inconsistent / doesn't reproduce | Emulator/host under resource load | Retry; check Task Manager for other heavy processes (e.g. two emulators running) |
| `adbExecTimeout` / instrumentation timeout on session start | This app takes ~15-20s to draw its first frame | Already handled — `adbExecTimeout` is set to 60s in `driver_manager.py` |
| Test passes alone but fails when run with others | Stale app session from a previous test | Already handled — `pm clear` runs automatically before every test |

Full detail on all of the above: see `README.md` → "Troubleshooting notes learned the hard way".

---

## Where results go

| What | Where |
|---|---|
| Step-by-step log | `logs/automation.log` |
| Failure screenshots (auto-captured) | `screenshots/` |
| Raw Allure results | `reports/allure-results/` |
| Generated HTML report | `reports/allure-report/` |
