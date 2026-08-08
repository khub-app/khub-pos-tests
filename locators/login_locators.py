from appium.webdriver.common.appiumby import AppiumBy


class LoginLocators:
    """
    Real locators captured from the live app (com.anonymous.ititansapp) on a
    cleared-data fresh install. The app sets no resource-id on most elements
    (no testID/accessibilityLabel from the RN devs) except these two fields.
    """
    # NOTE: AppiumBy.ID does not match these — this app's resource-ids are set via
    # React Native's `nativeID` without the usual "package:id/" prefix, which the
    # UiAutomator2 "id" strategy doesn't resolve. UiSelector().resourceId() does.
    USERNAME_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("login-username")')
    PASSWORD_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("login-password")')
    LOGIN_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Login")         # no resource-id; content-desc="Login"
    HOME_SCREEN_MARKER = (AppiumBy.ACCESSIBILITY_ID, "Start New Sale")  # dashboard-only element
