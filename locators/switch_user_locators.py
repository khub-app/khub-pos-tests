from appium.webdriver.common.appiumby import AppiumBy


class SwitchUserLocators:
    # Longer subtitle text, not "Switch user" - the dashboard's own "Switch
    # user" list item has that exact text too and can still be present in
    # the tree underneath the open dialog, so it isn't a reliable marker.
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Select who you want to switch to, then enter their PIN."]')
    SWITCH_SUBMIT = (AppiumBy.ACCESSIBILITY_ID, "Switch")
    CANCEL_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Cancel")

    @staticmethod
    def user_option(name: str):
        return (AppiumBy.XPATH, f'(//*[contains(@content-desc, "{name}")])[last()]')

    @staticmethod
    def pin_digit(digit: str):
        # Unlike the clock-in modal's keypad (resource-id="clockin-num-X"),
        # this dialog's digit buttons carry no resource-id - only a plain
        # content-desc equal to the digit itself.
        return (AppiumBy.ACCESSIBILITY_ID, digit)
