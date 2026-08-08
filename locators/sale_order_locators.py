from appium.webdriver.common.appiumby import AppiumBy


class SaleOrderLocators:
    """
    Locators for the Start New Sale / cart screen.

    NOTE on the product search box: it starts disabled with hint "Search
    products…"; a single tap flips the hint to "Tap again to type…" and only
    a SECOND tap actually enables it (enabled="false" -> "true"). This is a
    genuine two-tap interaction in the app, not a flake — always tap twice.

    NOTE on search result rows: they render with NO accessible node at all
    (no resource-id, no content-desc, no text in the accessibility tree) —
    confirmed by an exhaustive dump showing zero occurrences of the product
    name/SKU/price anywhere in the tree while the screenshot clearly shows
    them. This is the one place in the app where a coordinate-based tap is
    unavoidable rather than a shortcut around inspection.
    """
    SEARCH_PRODUCTS_FIELD = (AppiumBy.ACCESSIBILITY_ID, "Search products")
    # Single result row position when exactly one match is returned (a UPC
    # search always returns 0 or 1 result). Coordinates are relative to the
    # 2560x1600 viewport — this app's checkout screens render landscape by
    # default (matches real POS tablet usage), no orientation forcing needed.
    FIRST_RESULT_ROW_COORDS = {"x": 896, "y": 397}

    ADDITIONAL_DISCOUNT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Additional Discount")')
    GO_TO_MENU_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Go to Menu")')
    CASH_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Cash")
    CARD_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Card")

    # The cart summary (Total Quantity / Sub Total / Total / Tax / Additional
    # Discount) lives in a bottom drawer that renders COLLAPSED by default —
    # confirmed live: it's absent from the tree entirely until this handle
    # is tapped. The handle itself has no accessible node (empty text and
    # content-desc, like the search result row), so it's a coordinate tap.
    # Bounds were [0,1512][1960,1600] on the 2560x1600 landscape viewport.
    TOTALS_DRAWER_HANDLE_COORDS = {"x": 980, "y": 1556}

    # Once expanded, each label and its value are plain sibling TextViews
    # (NOT nested in a ViewGroup like CashPaymentLocators.AMOUNT_DUE_VALUE) —
    # confirmed live via page source dump. Exact text match on "Total" (not
    # descriptionContains) so it doesn't also match "Total Quantity"/"Total
    # Products".
    TOTAL_QUANTITY_VALUE = (
        AppiumBy.XPATH,
        '//*[@text="Total Quantity"]/following-sibling::android.widget.TextView[1]',
    )
    SUB_TOTAL_VALUE = (
        AppiumBy.XPATH,
        '//*[@text="Sub Total"]/following-sibling::android.widget.TextView[1]',
    )
    GRAND_TOTAL_VALUE = (
        AppiumBy.XPATH,
        '//*[@text="Total"]/following-sibling::android.widget.TextView[1]',
    )


class AgeVerificationLocators:
    """
    Locators for the "Age Verification Required" modal.

    NOTE on the DOB field: it is NOT a standard EditText (there is none in
    the tree at all). Tapping the "MM, /, DD, /, YYYY" control focuses a
    hidden native input (the on-screen keyboard appears) that accepts
    keystrokes via Appium's `mobile: type` (which targets whatever is
    currently focused, independent of any accessible element reference).

    NOTE on layout: "Check age" and "Confirm & Proceed" render below the
    visible viewport fold and require a swipe-up gesture within the modal's
    own bounds before they appear in the tree — this is a real modal-content
    overflow in the app, not a bug in the framework.
    """
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Age Verification Required"]')
    DOB_FIELD = (AppiumBy.ACCESSIBILITY_ID, "MM, /, DD, /, YYYY")
    CHECK_AGE_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Check age")
    CONFIRM_AND_PROCEED_BUTTON = (AppiumBy.XPATH, '//*[@text="Confirm & Proceed"]')
    VERIFIED_LABEL = (AppiumBy.XPATH, '//*[@text="Verified"]')

    # region within the modal to swipe (not the whole screen — the app
    # letterboxes this screen, and swiping outside the real content area
    # is a silent no-op)
    MODAL_SWIPE_REGION = {"left": 450, "top": 900, "width": 700, "height": 350}


class DiscountLocators:
    """Locators for the "Add Discount" modal (opened via Additional Discount)."""
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Add Discount"]')
    CONFIRM_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Confirm")
    CANCEL_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Cancel")')

    @staticmethod
    def digit(d: str):
        return (AppiumBy.ACCESSIBILITY_ID, d)


class CashPaymentLocators:
    """
    Locators for the "Total Cash Recieved" modal (opened via the Cash button).

    NOTE on Amount Due: the value has no resource-id/content-desc of its own
    (just a bare text node) — but it sits in a structurally stable spot: the
    "Amount Due" label's next-sibling ViewGroup contains it. That's more
    robust than matching on the number itself, which changes every run.

    NOTE on digit entry: there's no "." key on this pad (unlike the Discount
    modal) — amounts are entered right-to-left, cents-style (typing "1980"
    displays as $19.80), matching how real cash registers work.
    """
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Total Cash Recieved"]')
    AMOUNT_DUE_VALUE = (
        AppiumBy.XPATH,
        '//*[@text="Amount Due"]/following-sibling::android.view.ViewGroup[1]/android.widget.TextView',
    )
    CONFIRM_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Confirm")
    CANCEL_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Cancel")')

    @staticmethod
    def digit(d: str):
        return (AppiumBy.ACCESSIBILITY_ID, d)


class ReceiptPromptLocators:
    """Locators for the post-payment receipt prompt."""
    NO_RECEIPT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("No Receipt")')
