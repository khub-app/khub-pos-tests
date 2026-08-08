from appium.webdriver.common.appiumby import AppiumBy


class ClockInLocators:
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Clock in to your Account"]')
    CLOCK_IN_SUBMIT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("clockin-submit")')

    @staticmethod
    def pin_digit(digit: str):
        return (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().resourceId("clockin-num-{digit}")')
