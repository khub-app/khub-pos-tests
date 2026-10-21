from appium.webdriver.common.appiumby import AppiumBy


class CashMovementLocators:
    """Locators shared by the Cash In and Cash Out modals (identical
    structure - Amount / Current Drawer / New Drawer, quick-amount
    buttons, digit pad, Confirm; only the title and arithmetic direction
    differ)."""
    CONFIRM_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Confirm")
    CANCEL_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Cancel")')

    @staticmethod
    def quick_amount(amount: str):
        return (AppiumBy.ACCESSIBILITY_ID, amount)
