from appium.webdriver.common.appiumby import AppiumBy


class ParkedOrdersLocators:
    """Locators for the "Hold / Resume" (Parked Orders) screen, reached from
    the dashboard's Operations column via descriptionContains("Hold / Resume").

    Confirmed live 2026-10-19: rows are a paginated data table sorted by
    Date/Time descending (most recently parked order first). Tapping an
    order's ORDER NUMBER cell selects that row (confirmed via its
    content-desc gaining a "Bulk Delete, N" selection count) - there is no
    separate checkbox element, the text cell itself is the tap target.
    RESUME_ORDER_BUTTON is a single global action (not per-row) that acts
    on whichever row is currently selected.

    Resuming navigates back to the Start New Sale / cart screen with the
    exact product(s)/qty/price that were parked, and briefly shows a toast
    reading "Order <ORDER-NUMBER> resumed with <N> product(s)" - matched
    here with contains() rather than the exact text, since the order
    number is server-generated and not known ahead of time.
    """

    TITLE = (AppiumBy.XPATH, '//*[@text="Parked Orders"]')
    # [1] = topmost row in the table = most recently parked order, since the
    # table sorts Date/Time descending (confirmed live).
    TOP_ROW_ORDER_NUMBER = (AppiumBy.XPATH, '(//*[starts-with(@text, "PARKED-SO-")])[1]')
    RESUME_ORDER_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Resume Order")')
    RESUME_TOAST = (AppiumBy.XPATH, '//*[contains(@text, "resumed with")]')
