from appium.webdriver.common.appiumby import AppiumBy


class DashboardLocators:
    START_NEW_SALE = (AppiumBy.ACCESSIBILITY_ID, "Start New Sale")
    # descriptionContains rather than an exact accessibility id match: this
    # element's content-desc has a trailing ", " that exact ACCESSIBILITY_ID
    # matching has proven unreliable against (see login_locators.py notes).
    TIME_CLOCK_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Time Clock")')
    CLOCKED_IN_MARKER = (AppiumBy.ACCESSIBILITY_ID, "Clocked In")
    CLOCK_OUT_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Clock Out")
    SALES_HISTORY_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Sales History")')
