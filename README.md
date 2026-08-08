# POS Automation — Android (Appium + Python + Pytest)

Automation framework for the KHUB POS Android app (`com.anonymous.ititansapp`),
built with **Appium 2**, **Appium-Python-Client**, and **Pytest**, following the
Page Object Model. Sibling project to `khub-web-tests` (which covers the web app
with Playwright) — kept separate deliberately since the driver stack, dependency
set, and CI pipeline are unrelated.

---

## 1. Environment Setup

This machine already has: Python 3.10.7, Node v24, Java 17 (Temurin), and an
Android SDK at `%LOCALAPPDATA%\Android\Sdk` with a `Pixel_Tablet` AVD. Steps
below assume a similar starting point; skip what you already have.

### 1.1 Python
```powershell
python --version        # 3.10+ required
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 1.2 Node.js (required by Appium server)
Download the LTS installer from nodejs.org, then verify:
```powershell
node --version
npm --version
```

### 1.3 Appium 2 (server) + drivers
```powershell
npm install -g appium
appium --version                       # should print 2.x (installed here: 3.5.2, still Appium-2-line)
appium driver install uiautomator2
appium driver list --installed
```

### 1.4 Android Studio / SDK / Platform Tools
Install Android Studio (includes SDK Manager). Through
**Settings → Languages & Frameworks → Android SDK**, ensure these are checked:
- SDK Platform (matching your device's Android version)
- Android SDK Build-Tools
- Android SDK Platform-Tools
- Android Emulator (if using an emulator)

Set environment variables (Windows: System Properties → Environment Variables):
| Variable | Value |
|---|---|
| `ANDROID_HOME` | `C:\Users\<you>\AppData\Local\Android\Sdk` |
| `ANDROID_SDK_ROOT` | same as above |
| `Path` (append) | `%ANDROID_HOME%\platform-tools`, `%ANDROID_HOME%\emulator` |

> `setx PATH ...` is deliberately **not** used to append to PATH automatically —
> it truncates at 1024 characters and can silently corrupt an existing PATH.
> Add PATH entries through the GUI, or your shell profile, instead.

Verify:
```powershell
adb version
adb devices
emulator -list-avds
```

### 1.5 Appium Inspector
Appium Inspector is a separate desktop app (not an npm package) — download the
installer for your OS from the Appium Inspector GitHub Releases page and
install it. Used in Section 6 below.

### 1.6 Appium-Python-Client
Already listed in `requirements.txt`; installed via `pip install -r requirements.txt`.

**Verification checklist**
```powershell
python --version
node --version
java -version
adb version
appium --version
appium driver list --installed
pip show Appium-Python-Client
```

---

## 2. Verify the Android Device

**Emulator:**
```powershell
emulator -list-avds
emulator -avd Pixel_Tablet
```

**Real tablet:** enable Developer Options (tap Build Number 7×) → enable
USB Debugging → connect via USB → accept the RSA fingerprint prompt on the
tablet screen.

**Either way, confirm it's visible to adb:**
```powershell
adb devices -l
```

**Find the package name and launch activity from an APK** (no device needed):
```powershell
aapt dump badging app-release.apk | findstr "package: launchable-activity"
```
For this app that yields:
```
package: name='com.anonymous.ititansapp'
launchable-activity: name='com.anonymous.ititansapp.MainActivity'
```
(already filled into `config/config.yaml`)

**Find the package name/activity of an app already running on a connected device:**
```powershell
adb shell dumpsys window | findstr mCurrentFocus
```

**Verify the APK is installed on a device:**
```powershell
adb shell pm list packages | findstr ititansapp
```

---

## 3. Project Structure

```
POSAutomation/
│
├── config/                  # Environment definitions + the loader that reads them
│   ├── config.yaml          #   emulator / real_device capability blocks
│   └── config_reader.py     #   ConfigReader — resolves --env / POS_ENV into a dict
│
├── pages/                   # Page Object Model — one class per screen
│   ├── base_page.py         #   shared element interactions + mobile gestures
│   └── login_page.py        #   Login screen POM
│
├── locators/                # Locators kept separate from page logic
│   └── login_locators.py    #   (AppiumBy strategy, value) tuples for Login screen
│
├── tests/                   # Pytest test cases, one subfolder per feature
│   └── login/
│       └── test_login.py
│
├── utilities/                # Cross-cutting technical helpers (not page-specific)
│   ├── driver_manager.py    #   builds capabilities, starts/stops the Appium session
│   ├── wait_helper.py       #   explicit-wait wrapper (no hard sleeps)
│   ├── screenshot_helper.py #   saves PNGs to screenshots/
│   └── logger.py            #   file + console logging
│
├── data/                    # Test data (yaml) + the APK under test (gitignored)
│   ├── test_data.yaml
│   └── apk/app-release.apk
│
├── reports/                 # Allure results/report output (gitignored)
├── screenshots/             # Failure screenshots (gitignored)
├── logs/                    # automation.log (gitignored)
│
├── conftest.py               # `driver` fixture + failure-screenshot hook + --env option
├── pytest.ini                # test discovery, markers, Allure results dir
├── requirements.txt
└── README.md
```

Why this shape: `locators/` is separate from `pages/` so locator churn (which
happens constantly as the app changes) never touches interaction logic.
`utilities/` holds *technical* concerns (waits, driver lifecycle, logging) —
nothing here knows what a "Login screen" is. `pages/` holds *domain* concerns —
nothing here knows what `AppiumBy.ACCESSIBILITY_ID` is, only what "enter
username" means.

---

## 4. Framework Components

Already built (see files above):

- **DriverManager** (`utilities/driver_manager.py`) — reads a resolved config
  dict, builds a `UiAutomator2Options` capability set, opens/closes the
  Appium `webdriver.Remote` session.
- **BasePage** (`pages/base_page.py`) — `click`, `type_text`, `get_text`,
  `is_displayed`, plus mobile gestures (`scroll_down`, `scroll_up`,
  `scroll_into_view_by_text`, `hide_keyboard`).
- **WaitHelper** (`utilities/wait_helper.py`) — every interaction goes through
  an explicit `WebDriverWait`; there is no `time.sleep()` anywhere in the
  framework.
- **ConfigReader** (`config/config_reader.py`) — resolves `--env` CLI flag or
  `POS_ENV` env var to an environment block from `config.yaml`.
- **Logger** (`utilities/logger.py`) — writes to both console and
  `logs/automation.log`.
- **Screenshot helper** (`utilities/screenshot_helper.py`) — used automatically
  on test failure via the `pytest_runtest_makereport` hook in `conftest.py`,
  and attached to the Allure report.

---

## 5. Sample Login Automation

`pages/login_page.py` + `tests/login/test_login.py` implement:
launch app (via capabilities, handled by `DriverManager`) → enter username →
enter password → click Login → assert a post-login "home screen" marker is
displayed.

**The locators in `locators/login_locators.py` are placeholders** — they must
be replaced with real values from Appium Inspector (Section 6) before this
test can pass. Test credentials live in `data/test_data.yaml`
(`preprod` / `Password@123`).

---

## 6. Element Inspection (Appium Inspector)

1. Start the Appium server: `appium`
2. Start Appium Inspector, set **Remote Host** `127.0.0.1`, **Port** `4723`.
3. Under **Desired Capabilities**, paste JSON matching `config/config.yaml`'s
   `emulator` block, e.g.:
   ```json
   {
     "platformName": "Android",
     "appium:automationName": "UiAutomator2",
     "appium:deviceName": "emulator-5554",
     "appium:appPackage": "com.anonymous.ititansapp",
     "appium:appActivity": ".MainActivity",
     "appium:app": "C:\\...\\POSAutomation\\data\\apk\\app-release.apk",
     "appium:noReset": true
   }
   ```
4. Click **Start Session**. Tap an element in the screenshot pane — the
   right-hand panel shows its attributes:

   | Attribute | Where it shows | Use when |
   |---|---|---|
   | `resource-id` | e.g. `com.anonymous.ititansapp:id/username` | Present and stable — **preferred** |
   | `content-desc` (→ accessibility id) | RN `testID` / `accessibilityLabel` | Native `resource-id` absent, as is common in React Native apps — **preferred for this app** |
   | `text` | Visible label text | Only for static, non-localized labels; breaks if copy changes or app is localized |
   | `class` | e.g. `android.widget.EditText` | Never unique alone; combine with index only as a last resort |
   | full XPath | Computed from the tree | **Avoid** — brittle, breaks on any layout change, slowest strategy |

   **Preferred order for this app:** `resource-id` > `accessibility id`
   (content-desc) > `text` > XPath (last resort only).

   Given the `com.anonymous.*` package name, this app is very likely
   React Native/Expo — expect sparse `resource-id`s and richer
   `content-desc`/accessibility labels if the RN devs set `testID` props.
   Flag to the dev team if `testID` isn't set on interactive elements; it's
   the single highest-leverage ask for making this app automatable.

5. Copy the real values into `locators/login_locators.py`, replacing the
   `# TODO` placeholders.

---

## 7. Best Practices Already Enforced

- **POM** — locators, page logic, and tests are in three separate layers.
- **Explicit waits only** — `WaitHelper` wraps every lookup; no
  `time.sleep()` in the framework. If you're tempted to add one, add a
  proper `EC` condition to `wait_helper.py` instead.
- **Reusable locators** — one locator definition per element, imported
  wherever needed; never inlined in a test.
- **Independent tests** — the `driver` fixture is function-scoped: every
  test gets a fresh Appium session and teardown, no shared state. This app
  specifically persists its login session across app restarts (`noReset`
  keeps that data around), which would otherwise make a test's outcome
  depend on what ran before it — e.g. a Login test passing standalone but
  a later test failing because the app was already authenticated. To
  prevent that, `DriverManager.reset_app_data()` runs `adb shell pm clear`
  before every single test via the `driver` fixture, so every test always
  starts from a genuinely logged-out state regardless of run order. This
  costs a few extra seconds per test but is the only way to guarantee
  true independence with an app that persists auth state locally.
- **Easy to extend** — adding a new screen means: one locators file, one
  page object (subclassing `BasePage`), one test file under `tests/<feature>/`.

---

## 8. Reporting (Allure)

Install the Allure commandline (one-time):
```powershell
scoop install allure        # or: npm install -g allure-commandline
allure --version
```

`pytest.ini` already points results at `reports/allure-results` via
`addopts = --alluredir=reports/allure-results`.

Generate and open the report after a run:
```powershell
allure generate reports/allure-results -o reports/allure-report --clean --single-file
start reports/allure-report/index.html
```
or, for a quick local preview without a static build:
```powershell
allure serve reports/allure-results
```

---

## 9. Execution

```powershell
# one test
pytest tests/login/test_login.py::test_login_with_valid_credentials --env=emulator

# entire suite
pytest --env=emulator

# by marker
pytest -m smoke --env=emulator

# in parallel (pytest-xdist) — only safe once each worker gets its own
# systemPort/udid in config.yaml; see note below
pytest -n 2 --env=emulator

# generate + open Allure report
allure generate reports/allure-results -o reports/allure-report --clean --single-file
start reports/allure-report/index.html
```

> **Parallel execution caveat**: Appium/UiAutomator2 sessions are pinned to a
> single device. Running `-n 2` against one emulator will make both workers
> fight over the same device. True parallelism requires either multiple
> emulators (each its own `udid`/`systemPort` in `config.yaml`) or a device
> farm (BrowserStack App Automate, Sauce Labs, or a self-hosted Appium grid).
> Until then, keep `-n 1` (the default) for this single-emulator setup.

---

## 10. CI/CD Recommendation

Android UI automation cannot run on a plain GitLab/Jenkins Linux runner
without a device — recommended approach:

- **Self-hosted runner with KVM** (GitLab Runner or Jenkins agent on a Linux
  VM with nested virtualization) running a headless emulator
  (`emulator -no-window -no-audio`), Appium server, and this framework.
- Alternatively, target a **cloud device farm** (BrowserStack App Automate /
  Sauce Labs) from a standard runner — no local emulator needed, just point
  `appium_server` and capabilities in `config.yaml` at the cloud endpoint.
- Pipeline stages: `pip install -r requirements.txt` → start emulator/Appium
  server (or skip if using a cloud farm) → `pytest --env=<env> --alluredir=reports/allure-results`
  → `allure generate` → publish `reports/allure-report` as a build artifact
  (GitLab Pages or Jenkins HTML Publisher plugin).
- Gate merges on the `smoke` marker subset for fast feedback; run the full
  `regression` marker set on a nightly schedule (mirrors the existing
  `khub-web-tests` VM nightly regression pattern).

---

## Appium vs. Playwright — key differences

| | Playwright (web) | Appium (Android) |
|---|---|---|
| Protocol | Chrome DevTools Protocol / browser-native | WebDriver protocol over HTTP to an Appium server, which drives UiAutomator2 on-device |
| What it drives | A browser | A real or emulated device/app |
| Element model | DOM | Android view hierarchy (`resource-id`, `content-desc`, `class`, `bounds`) |
| Waiting | Playwright auto-waits on actionability | Must build explicit waits yourself (`WaitHelper` above) — no built-in auto-wait equivalent |
| "New tab" handling | `expect_page()` | Not applicable — instead: app switches (`adb shell am start`), permission dialogs, system UI (keyboard, notifications) |
| Locators | CSS/text/role selectors | `resource-id`, accessibility id, `UiSelector` (`AppiumBy.ANDROID_UIAUTOMATOR`), XPath |
| Session model | Lightweight browser context per test | Full app session per test — slower to spin up (app cold-start), so plan fixture scope accordingly |

## Troubleshooting notes learned the hard way

- **Emulator shows a black screen / screenshots are always the same frozen
  splash icon, regardless of what's actually on screen.** This is a graphics
  rendering failure, not an Appium bug — check the AVD's GPU mode:
  ```
  cat %USERPROFILE%\.android\avd\<AVD_NAME>.avd\config.ini | findstr gpu
  ```
  If `hw.gpu.mode=auto` isn't working on your host, force pure software
  rendering by launching with an explicit flag instead of editing the AVD
  permanently:
  ```powershell
  emulator -avd Pixel_Tablet -gpu swiftshader_indirect
  ```
  The accessibility tree (`driver.page_source`) is unaffected by this bug even
  while it's happening — you can still automate against it, you just can't
  see it. If a real screenshot is ever failing to look right, don't trust it
  blindly; cross-check with `adb exec-out screencap -p > file.png` (bypasses
  Appium entirely) before concluding it's a framework issue. Real hardware
  (a physical tablet) doesn't have this problem at all.

- **`AppiumBy.ID` silently fails to find elements that clearly have a
  `resource-id` in the page source.** This app sets resource-ids via React
  Native's `nativeID` prop without the usual `"package:id/name"` prefix
  Android normally requires, and UiAutomator2's `id` strategy doesn't resolve
  that format. Use `AppiumBy.ANDROID_UIAUTOMATOR` with
  `UiSelector().resourceId("...")` instead — see `locators/login_locators.py`
  for the working pattern.

- **The app re-renders shortly after its first paint** (icons/fonts pop in a
  beat late), which can invalidate element references obtained too early —
  a mistimed tap can land on the wrong element after a layout shift. Always
  let `WaitHelper` do the waiting (it already retries through this); avoid
  bare `driver.find_element()` calls with no wait wrapper in ad-hoc scripts.

- **`adb shell` commands can time out under host resource pressure**
  (observed: a plain `dumpsys window` call took over 20s). If you see
  intermittent `NoSuchElementException`/timeouts that don't reproduce
  consistently, suspect host performance before suspecting locators.

## Mobile-specific considerations baked into the framework from day one

- **Gestures**: `BasePage.scroll_down/scroll_up` use `mobile: swipeGesture`
  (the modern UiAutomator2 gesture API); `scroll_into_view_by_text` uses
  `UiScrollable`/`UiSelector` for list scrolling — both far more reliable on
  Android than manual coordinate swipes.
- **Keyboard**: `hide_keyboard()` before tapping buttons that the soft
  keyboard may be covering (e.g. Login button below a password field).
- **Permissions**: `autoGrantPermissions: true` is set in `config.yaml` so
  runtime permission dialogs (camera, storage, etc.) don't block tests. If a
  specific test needs to exercise the permission dialog itself, override this
  per-test rather than globally.
- **App state resets**: `noReset: true` by default (keeps app data between
  runs — faster, more realistic); flip to `fullReset: true` for a clean-install
  test when needed. This mirrors why real-device runs shouldn't set `app_path`
  — the app is already installed, so noReset skips reinstall entirely.
- **Device variability**: `config.yaml` keeps `emulator` and `real_device` as
  separate blocks precisely because tablet UDIDs, platform versions, and
  screen density affect swipe percentages/coordinates.
