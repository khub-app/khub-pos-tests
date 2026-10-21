from appium.webdriver.common.appiumby import AppiumBy


class ShiftLocators:
    """"Start Shift" confirmation modal (Opening Cash + denomination count),
    reached from the dashboard's "Shift Controls" panel. Required before
    Start New Sale works - confirmed live 2026-10-19 against the v1.1.0
    build: a brand-new employee shows "SHIFT: Closed" and New Sale controls
    silently fail to render/respond until a shift is started, even though
    they're clocked in and switched to as the active user.
    """

    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Start New Shift"]')
    # The SAME text "Start Shift" labels both the dashboard's trigger tile
    # and the modal's own submit button - [last()] grabs whichever is
    # actually the live/topmost one at call time: exactly one match before
    # the modal opens (the trigger), two after (trigger + submit, submit
    # mounted later in document order) - same [last()] pattern already used
    # by ClockInLocators.user_option / SwitchUserLocators.user_option for
    # an identical summary-row-vs-list-option ambiguity.
    START_SHIFT_BUTTON = (AppiumBy.XPATH, '(//*[@text="Start Shift"])[last()]')
