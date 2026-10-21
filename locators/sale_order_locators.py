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
    ADD_QUICK_CUSTOMER_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Add Quick Customer")')
    MORE_OPTIONS_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("More Options")')
    GUEST_CUSTOMER_MARKER = (AppiumBy.XPATH, '//*[@text="Guest Customer"]')

    # Confirmed live 2026-10-20: tapping Cash or Card with an empty cart does
    # NOT silently proceed and does NOT disable the buttons either (both
    # report enabled="true" even at Total Products: 0) - it shows this
    # native error dialog instead. Tapping its OK recovers cleanly back to
    # the (still empty) cart screen.
    ADD_PRODUCTS_FIRST_ERROR_MESSAGE = (AppiumBy.XPATH, '//*[@text="Please add products to cart first"]')
    ADD_PRODUCTS_FIRST_ERROR_OK_BUTTON = (AppiumBy.XPATH, '//*[@text="OK"]')

    NO_PRODUCTS_IN_CART_MARKER = (
        AppiumBy.XPATH,
        '//*[@text="There are no products in the list yet. Add products to get started."]',
    )

    # Per-row quantity stepper (+/-) and Remove product. The stepper's own
    # icons have no content-desc/resource-id of their own (confirmed live,
    # same class of element as FIRST_RESULT_ROW_COORDS/
    # TOTALS_DRAWER_HANDLE_COORDS above) - coordinate taps, same landscape
    # viewport, only valid when the product being adjusted is the cart's
    # FIRST/only row. Remove product DOES have a real content-desc and
    # needs no coordinate workaround; removing a line fires with no
    # confirmation dialog at all (confirmed live - unlike Empty Cart below).
    QUANTITY_INCREMENT_COORDS = {"x": 1455, "y": 473}
    QUANTITY_DECREMENT_COORDS = {"x": 1307, "y": 473}
    REMOVE_PRODUCT_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Remove product")

    # Unlike Remove product (single line, no prompt), Empty Cart (all
    # lines) DOES confirm first - confirmed live: "Are you sure you want to
    # remove all items?" / CANCEL / EMPTY.
    EMPTY_CART_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Empty Cart")
    EMPTY_CART_CONFIRM_BUTTON = (AppiumBy.XPATH, '//*[@text="EMPTY"]')
    EMPTY_CART_CANCEL_BUTTON = (AppiumBy.XPATH, '//*[@text="CANCEL"]')

    @staticmethod
    def current_customer_name(name: str):
        return (AppiumBy.XPATH, f'//*[@text="{name}"]')

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
    # Confirmed live: when verification fails, "Confirm & Proceed" isn't
    # merely disabled - it's ABSENT from the tree entirely, replaced by
    # this blocked-state button instead. Checking is_enabled() on
    # CONFIRM_AND_PROCEED_BUTTON in the failure case raises a
    # TimeoutException (element never found), not a clean False - use this
    # marker to detect the blocked state instead.
    BELOW_REQUIRED_AGE_LABEL = (AppiumBy.XPATH, '//*[@text="Below required age"]')
    REMOVE_RESTRICTED_ITEMS_BUTTON = (AppiumBy.XPATH, '//*[@text="Remove Restricted Items"]')

    # region within the modal to swipe (not the whole screen — the app
    # letterboxes this screen, and swiping outside the real content area
    # is a silent no-op)
    MODAL_SWIPE_REGION = {"left": 450, "top": 900, "width": 700, "height": 350}


class DiscountLocators:
    """Locators for the "Add Discount" modal (opened via Additional Discount).

    Confirmed live 2026-10-19: this modal supports TWO discount modes via a
    dropdown toggle - "Percentage (%)" (default) and "Fixed ($)" - not just
    percentage. The toggle shows whichever mode is currently active; tapping
    it opens both options as a 2-item list.

    CANCEL_BUTTON only clears the typed digits - confirmed live it does NOT
    close/dismiss the modal (the modal stayed open, value reset to $0.00/0%).
    There's a separate close ("Dismiss dialog") icon at the top-right if the
    modal needs to be abandoned without clearing+confirming; this suite only
    ever uses CONFIRM_BUTTON, which does close the modal and returns to the
    cart with the new discount applied (confirmed live - no separate "close"
    step needed after Confirm).

    No locators are defined here for the modal's own live-preview fields
    (Discount Amount / Total After Discount) - validate via
    SaleOrderPage.get_sub_total()/get_grand_total() on the cart AFTER
    confirming instead (same proven pattern the percentage-discount test
    already uses); the preview fields' DOM structure is label-group-then-
    value-group, not interleaved, so a naive following-sibling lookup
    silently resolves to the WRONG value's label.
    """
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Add Discount"]')
    CONFIRM_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Confirm")
    CANCEL_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Cancel")')
    # The modal always opens in Percentage mode by default (confirmed live) -
    # this is that default trigger specifically, not a generic "whichever
    # mode is active" matcher. The trailing ", " distinguishes the trigger
    # (content-desc "Percentage (%), <icon>") from the dropdown's own
    # "Percentage (%)" option row (no trailing icon/comma) once opened.
    PERCENTAGE_MODE_TRIGGER = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Percentage (%), ")')
    FIXED_MODE_OPTION = (AppiumBy.ACCESSIBILITY_ID, "Fixed ($)")
    PERCENTAGE_MODE_OPTION = (AppiumBy.ACCESSIBILITY_ID, "Percentage (%)")

    # Confirmed live 2026-10-20: a Fixed ($) discount greater than the
    # cart's own total disables Confirm (enabled="false", though Appium
    # still reports clickable="true" - always check is_enabled(), not
    # clickability) and shows this exact validation text. The preview
    # "Total After Discount" field still shows the raw negative number
    # (e.g. -30.00) even though it can never actually be confirmed.
    VALIDATION_MESSAGE_DISCOUNT_EXCEEDS_TOTAL = (
        AppiumBy.XPATH,
        '//*[@text="Discount cannot exceed the total amount."]',
    )

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
    # Same structural pattern as Amount Due - confirmed live 2026-10-20 for
    # the overpayment case ($20 received on $10 due read back exactly
    # "10.00"). NOTE: only verified reliable for overpayment; for
    # underpayment this read back the stale Amount Due figure instead of a
    # real (negative/zero) change value, so don't trust it there - the
    # reliable signal for underpayment is CONFIRM_BUTTON's own enabled
    # state (confirmed false), not this field.
    CHANGE_DUE_VALUE = (
        AppiumBy.XPATH,
        '//*[@text="Change Due"]/following-sibling::android.view.ViewGroup[1]/android.widget.TextView',
    )
    CONFIRM_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Confirm")
    CANCEL_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Cancel")')

    @staticmethod
    def digit(d: str):
        return (AppiumBy.ACCESSIBILITY_ID, d)


class ReceiptPromptLocators:
    """Locators for the post-payment receipt prompt."""
    NO_RECEIPT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("No Receipt")')


class ParkOrderLocators:
    """Locators for the cart's "Park Order" confirmation dialog.

    Confirmed live 2026-10-19: tapping the sidebar's Park Order tile opens a
    confirmation dialog summarizing the order (Customer / Total Items /
    Total Amount) plus an optional note field, before actually parking it -
    worth asserting against, since it's a second independent readout of the
    cart contents besides the totals drawer. The dialog's OWN confirm button
    is ALSO labeled "Park Order" (identical text to the sidebar trigger that
    opened it) - same [last()] disambiguation pattern as
    ClockInLocators.user_option / ShiftLocators.START_SHIFT_BUTTON.

    Confirming resets the cart to empty and shows a "Order parked
    successfully" toast - confirmed live via screenshot (Total Products: 0,
    Sub Total: $0.00, search panel shows "There are no products in the list
    yet"). Resuming a parked order is covered separately - see
    ParkedOrdersLocators (locators/parked_orders_locators.py), reached from
    DashboardPage.open_hold_resume().
    """
    TRIGGER = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Park Order")')
    CONFIRM_DIALOG_TITLE = (
        AppiumBy.XPATH,
        '//*[@text="Are you sure you want to park this order?\nThe order will be saved and can be resumed later."]',
    )
    CUSTOMER_VALUE = (AppiumBy.XPATH, '//*[@text="Customer"]/following-sibling::*[1]')
    TOTAL_ITEMS_VALUE = (AppiumBy.XPATH, '//*[@text="Total Items"]/following-sibling::*[1]')
    TOTAL_AMOUNT_VALUE = (AppiumBy.XPATH, '//*[@text="Total Amount"]/following-sibling::*[1]')
    NOTE_FIELD = (AppiumBy.XPATH, '//*[@text="Enter a note for this parked order..."]')
    DIALOG_CANCEL_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Cancel")
    CONFIRM_BUTTON = (AppiumBy.XPATH, '(//*[@text="Park Order"])[last()]')
    SUCCESS_TOAST = (AppiumBy.XPATH, '//*[@text="Order parked successfully"]')
