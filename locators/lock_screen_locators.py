from appium.webdriver.common.appiumby import AppiumBy


class LockScreenLocators:
    """Locators for the "Screen Locked" modal (opened via the dashboard's
    Lock Screen tile).

    Confirmed live 2026-10-20: a wrong PIN shows "Incorrect PIN. Please try
    again." and keeps the modal locked (no lockout counter observed) - the
    correct PIN unlocks normally, returning to the dashboard exactly as it
    was.
    """

    TITLE = (AppiumBy.XPATH, '//*[@text="Screen Locked"]')
    INCORRECT_PIN_ERROR = (AppiumBy.XPATH, '//*[@text="Incorrect PIN. Please try again."]')
    CLEAR_BUTTON = (AppiumBy.XPATH, '//*[@text="Clear"]')
    UNLOCK_BUTTON = (AppiumBy.XPATH, '//*[@text="Unlock"]')

    @staticmethod
    def digit(d: str):
        return (AppiumBy.ACCESSIBILITY_ID, d)

    @staticmethod
    def staff_name(name: str):
        return (AppiumBy.XPATH, f'//*[@text="{name}"]')
