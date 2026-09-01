from appium.webdriver.common.appiumby import AppiumBy


class ClockInLocators:
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Clock in to your Account"]')
    CLOCK_IN_SUBMIT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("clockin-submit")')
    # Sibling relationship to the static "Select User" label, not the dropdown's
    # own text - the dropdown shows whichever user is currently selected, so its
    # own content-desc/text varies and can't be matched directly.
    SELECT_USER_DROPDOWN = (AppiumBy.XPATH, '//*[@text="Select User"]/following-sibling::*[1]')
    # Real app copy varies by scenario ("...enter your PIN to resume on this
    # device." vs "...tap Clock Out below to end this shift.") - both start
    # with this prefix, so match on that rather than either exact string.
    ALREADY_CLOCKED_IN_WARNING = (AppiumBy.XPATH, '//*[contains(@text, "Already clocked in")]')
    CANCEL_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Cancel")')

    @staticmethod
    def pin_digit(digit: str):
        return (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().resourceId("clockin-num-{digit}")')

    @staticmethod
    def user_option(name: str):
        # The dropdown's own current-selection summary row can also contain
        # `name` (when that user already happens to be selected), so this
        # list has up to two matches - [last()] is always the actual list
        # option, since it renders after the summary row in document order.
        return (AppiumBy.XPATH, f'(//*[contains(@content-desc, "{name}")])[last()]')
