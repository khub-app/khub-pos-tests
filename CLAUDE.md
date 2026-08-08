# khub-pos-tests — Project Guide for Claude

This file is loaded automatically by Claude Code at the start of every session.
Read it fully before making any changes to the project.

---

## What This Project Is

End-to-end automation for the **KHub POS** Android tablet app.
The POS app is a React Native app (`com.anonymous.ititansapp`) that runs on a physical Android tablet or emulator.
Built with **Python + Appium + pytest**.

This is a **sibling project** to `khub-web-tests` (the web automation suite). They share the same backend/tenant but test different surfaces — web vs. Android POS tablet.

---

## Tech Stack

| Component | Version/Detail |
|-----------|---------------|
| Python | 3.10+ |
| Appium | 3.5.x (global npm install) |
| Appium Driver | uiautomator2 8.x |
| Appium Python Client | 5.3.x |
| pytest | 9.1.x |
| Android SDK | API 35 (Android 15) |
| Emulator AVD | `Pixel_Tablet` (Pixel Tablet device profile) |
| Node.js | 24.x LTS (required for Appium) |
| Java | JDK 11 (required for Appium/uiautomator2) |

---

## Prerequisites — Must Be Running Before Tests

Tests will fail immediately if these are not running:

1. **Android Emulator** (`Pixel_Tablet` AVD) — or a real tablet connected via USB
2. **Appium server** — `appium` in a terminal
3. **KHub POS app installed** on the emulator/device

### Start emulator
```
& "$env:ANDROID_HOME\emulator\emulator.exe" -avd Pixel_Tablet
```
Or open Android Studio → Device Manager → Play button on Pixel_Tablet.

### Start Appium
```
appium
```
Appium must be running at `http://127.0.0.1:4723` before any test runs.

### Install APK (first time only)
```
adb install data\apk\app-release.apk
```

---

## How to Run Tests

### All tests
```
python -m pytest tests/ -v
```

### Specific module
```
python -m pytest tests/login/ -v
python -m pytest tests/sale_order/ -v
python -m pytest tests/shift/ -v
```

### Against real device instead of emulator
```
python -m pytest tests/ -v --env=real_device
```
(Edit `config/config.yaml` with the device's `udid` and `platform_version` first.)

---

## Project Structure

```
POSAutomation/
├── config/
│   ├── config.yaml          # Appium capabilities + environment config
│   └── config_reader.py     # Loads config.yaml, resolves active env
├── data/
│   ├── test_data.yaml       # Test input values (credentials, product SKUs, etc.)
│   ├── test_data.xlsx       # Excel version of test data (backup/reference)
│   └── apk/                 # APK files (gitignored) — get from dev team
├── locators/
│   ├── login_locators.py
│   ├── dashboard_locators.py
│   ├── sale_order_locators.py
│   ├── sale_return_locators.py
│   ├── sales_history_locators.py
│   └── clockin_locators.py
├── pages/
│   ├── base_page.py         # BasePage with common Appium helpers
│   ├── login_page.py
│   ├── dashboard_page.py
│   ├── sale_order_page.py
│   ├── cash_payment_page.py
│   ├── discount_page.py
│   ├── age_verification_page.py
│   ├── sale_return_page.py
│   ├── return_payment_page.py
│   ├── sales_history_page.py
│   └── clockin_page.py
├── tests/
│   ├── base_test.py         # BaseTest — sets up/tears down Appium driver
│   ├── login/
│   │   └── test_login.py
│   ├── sale_order/
│   │   └── test_create_sale_order.py
│   └── shift/
│       └── test_clock_in.py
├── utilities/
│   ├── driver_manager.py    # Creates Appium WebDriver from config
│   ├── api_client.py        # REST API calls to KHub backend
│   ├── wait_helper.py       # Explicit waits / element wait helpers
│   ├── screenshot_helper.py # Capture screenshots on failure
│   ├── currency.py          # Parse/format currency strings
│   └── logger.py            # Test logger setup
├── conftest.py              # pytest hooks
├── pytest.ini
├── requirements.txt
└── setup_pos_new_laptop.ps1 # One-shot new machine setup script
```

---

## config/config.yaml — The Main Config

```yaml
default_environment: emulator   # change to "real_device" for physical tablet

backend_api:
  preprod:
    url: https://preprod.ikhub.biz
    username: preprod
    password: Password@123

environments:
  emulator:
    platform_name: Android
    automation_name: UiAutomator2
    device_name: emulator-5554    # adb device name when emulator is running
    platform_version: "15"        # Android 15 = API 35
    app_package: com.anonymous.ititansapp
    app_activity: .MainActivity
    app_path: null                # null = app already installed; set path for fresh install
    no_reset: true
    appium_server: http://127.0.0.1:4723

  real_device:
    device_name: KHUB_Tablet
    udid: null        # fill in from: adb devices -l
    platform_version: null  # fill in from: adb shell getprop ro.build.version.release
    ...
```

To run against a real tablet:
1. Enable USB debugging on the tablet
2. Connect via USB, run `adb devices -l` to get the `udid`
3. Run `adb shell getprop ro.build.version.release` to get Android version
4. Fill both values into `config.yaml` under `real_device`
5. Change `default_environment: real_device`

---

## data/test_data.yaml — Test Inputs

Contains login credentials, product SKUs, customer names, and other values used by tests.
Example structure:
```yaml
preprod:
  username: preprod
  password: Password@123
  product_sku: "123456"
  customer_name: "Test Customer"
```

**Important:** The POS app runs against the **`preprod` tenant** — NOT `automation_preprod`. These are different tenants with different product catalogs. Do not use `automation_preprod` SKUs for POS tests.

---

## Page Object Pattern

All tests use Page Objects. Pages inherit from `BasePage`:

```python
class BasePage:
    def __init__(self, driver):
        self.driver = driver

    def find(self, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def tap(self, locator):
        self.find(locator).click()

    def type_text(self, locator, text):
        el = self.find(locator)
        el.clear()
        el.send_keys(text)
```

Tests instantiate page objects and chain actions:
```python
def test_login(self):
    login = LoginPage(self.driver)
    login.enter_username("preprod")
    login.enter_password("Password@123")
    login.tap_login()
    assert DashboardPage(self.driver).is_loaded()
```

---

## Locator Pattern

Locators are kept in separate `locators/` files, separate from page logic:

```python
# locators/login_locators.py
from appium.webdriver.common.appiumby import AppiumBy

class LoginLocators:
    USERNAME_FIELD = (AppiumBy.ACCESSIBILITY_ID, "username")
    PASSWORD_FIELD = (AppiumBy.ACCESSIBILITY_ID, "password")
    LOGIN_BUTTON   = (AppiumBy.ACCESSIBILITY_ID, "login-button")
```

### Locator strategy priority (most reliable first)
1. `ACCESSIBILITY_ID` — use when the element has a `testID` prop in React Native
2. `XPATH` — fallback; use `//android.widget.TextView[@text='...']` patterns
3. `ANDROID_UIAUTOMATOR` — for complex scrolling/dynamic content

### Finding locators
When the app UI changes and locators break:
1. Start the emulator and Appium
2. Use `adb exec-out uiautomator dump /dev/tty` to dump the current screen XML
3. Or save page source in a test: `self.driver.page_source` → inspect the XML
4. Look for `content-desc` (maps to ACCESSIBILITY_ID) or `resource-id` attributes

---

## utilities/api_client.py — Backend API

The POS tests use the KHub REST API to verify data that the app UI doesn't surface directly (e.g. confirming the exact order number after checkout).

```python
client = KHubApiClient(env="preprod")
order = client.get_latest_order(customer_id=123)
assert order["status"] == "paid"
```

The API credentials come from `config.yaml` under `backend_api.preprod`.

---

## What Is Automated

| Module | Tests |
|--------|-------|
| **Login** | Successful login with valid credentials |
| **Clock In / Shift** | Clock in flow, verify shift started |
| **Sale Order** | Create sale order — add product by SKU, apply discount, complete with cash payment, verify receipt |
| **Sale Return** | Find order in Sales History, initiate return, complete return payment |

### What is NOT yet automated (future work)
- Card payment flow
- Multiple products in one order
- Customer selection / walk-in vs account customer
- Age verification bypass
- Void order
- Split payments

---

## Known Appium Gotchas

### GPU crash fix (emulator)
If the emulator crashes on startup with GPU errors, add to AVD config:
```
hw.gpu.enabled=no
hw.gpu.mode=off
```
Or launch with: `emulator -avd Pixel_Tablet -gpu off`

### Slow element interactions
React Native apps on Appium can be slow. Always use explicit waits via `wait_helper.py` — never use `time.sleep()` except as a last resort for animation delays.

### Keyboard covering elements
The on-screen keyboard sometimes obscures input fields. After typing, dismiss the keyboard before tapping the next element:
```python
self.driver.hide_keyboard()
```

### `no_reset: true`
The config uses `no_reset: true` meaning the app state is NOT cleared between test runs. Tests must handle pre-existing state (e.g. a shift that was already clocked in). Use the API client or teardown steps to reset state when needed.

### Emulator vs real device timing
Emulator is slower than a real tablet. If tests pass on real device but fail on emulator, increase timeouts in `wait_helper.py`.

---

## Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `ANDROID_HOME` | `C:\Users\<user>\AppData\Local\Android\Sdk` | Android SDK root |
| `ANDROID_SDK_ROOT` | same as ANDROID_HOME | Required by some tools |
| `JAVA_HOME` | `C:\Program Files\Java\jdk-11` | Required by Appium/uiautomator2 |

Both `ANDROID_HOME` and `JAVA_HOME` must be set and pointing to valid directories, or Appium will fail to start the uiautomator2 driver.

---

## Developing New Tests

### Step-by-step
1. Identify the flow to automate
2. Run the flow manually on the emulator, taking note of each screen
3. Dump page source at each step to find locators: `self.driver.page_source`
4. Add locators to the appropriate `locators/` file
5. Add page methods to the appropriate `pages/` file
6. Write the test in `tests/<module>/test_<feature>.py`
7. Inherit from `BaseTest` in `tests/base_test.py`

### Test template
```python
import pytest
from tests.base_test import BaseTest
from pages.sale_order_page import SaleOrderPage
from pages.dashboard_page import DashboardPage

class TestMyFlow(BaseTest):
    def test_my_scenario(self):
        # Navigate
        dashboard = DashboardPage(self.driver)
        dashboard.tap_new_sale()

        # Act
        sale = SaleOrderPage(self.driver)
        sale.add_product_by_sku("123456")

        # Assert
        assert sale.cart_item_count() == 1
```

### BaseTest sets up the driver
`BaseTest` in `tests/base_test.py` handles `setup_method` / `teardown_method` — creates the Appium driver from config and quits it after each test. You do not need to manage the driver lifecycle in individual tests.

---

## Relationship to khub-web-tests

Both projects automate KHub but at different layers:

| | khub-web-tests | khub-pos-tests |
|---|---|---|
| Surface | Web browser (Chromium) | Android POS tablet app |
| Framework | Playwright | Appium + uiautomator2 |
| Test data | automation_preprod tenant | preprod tenant |
| Runner | pytest + run_tests.ps1 | pytest |
| Reports | Allure (auto-generated) | Allure (manual for now) |

They are separate repos and separate Python venvs. Do not mix their dependencies.
