from appium.webdriver.common.appiumby import AppiumBy


class SalesHistoryLocators:
    """
    Locators for the Sales History screen.

    NOTE: this screen shows a shared, continuously-changing real tenant
    dataset (thousands of orders from other activity, not just ours) — never
    assume "the first row" is an order this test created. Use
    utilities.api_client.ApiClient.get_latest_guest_order_number() right
    after checkout to get the exact order number, then search for it here.
    """
    # No content-desc on this field — found via its `hint` attribute instead.
    SEARCH_BY_ORDER_ID_FIELD = (AppiumBy.XPATH, '//android.widget.EditText[@hint="Search by Order ID"]')

    # The right-side action menu (Print/View Order/View Customer/...) is
    # entirely ABSENT from the tree (not just disabled) until a row is
    # selected - confirmed live: no "Print" node exists at all beforehand.
    #
    # Each row also carries its own "View order notes" icon (content-desc
    # exactly "View order notes", no leading comma) - confirmed live via
    # page-source dump that a bare descriptionContains("View Order") matches
    # THESE first (there are usually several per page, one per annotated
    # row) before it ever reaches the real ", View Order" action button,
    # so a plain find_element/click() silently taps the wrong row's notes
    # icon instead. Every real action button's content-desc has a leading
    # ", " before its label (same convention as split_payment_locators.py's
    # CASH_BUTTON/CARD_BUTTON) - matching on that prefix is what actually
    # disambiguates them.
    PRINT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains(", Print")')
    VIEW_ORDER_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains(", View Order")')
    VOID_PAYMENT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains(", Void Payment")')
    EDIT_ORDER_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains(", Edit Order")')

    # Fallback when no order number was captured (see ReceiptCompletePage):
    # every result row's content-desc follows "{order_no}, {date}, {name},
    # {name}, {mode}, ${total}, {lifecycle}" - ", $" reliably marks a real
    # result row without matching anything else on this screen. Sorted
    # newest-first by the app itself, so [1] is the most recent transaction.
    FIRST_ROW = (AppiumBy.XPATH, '(//*[contains(@content-desc, ", $")])[1]')

    @staticmethod
    def order_row_lifecycle(order_no: str):
        return (AppiumBy.XPATH, f'//*[contains(@content-desc, "{order_no}")]//*[@text="Completed"]')

    @staticmethod
    def order_row_sale_total(order_no: str):
        return (
            AppiumBy.XPATH,
            f'//*[contains(@content-desc, "{order_no}")]//*[contains(@text, "$")]',
        )


class InvoicePreviewLocators:
    """
    Locators for the invoice Print Preview screen (opened via the "Print"
    action). Confirmed live via page-source dump: this is a plain-text
    receipt (store info, customer info, item list, Total Quantity) with NO
    Total/Tax/Payment-amount fields at all - its ScrollView's measured
    content bounds end exactly where the visible text ends, so this isn't
    a scroll/virtualization issue, the fields genuinely aren't on this
    screen. Use OrderDetailsLocators (via "View Order") for the actual
    Total/Amount Paid validation instead.
    """
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Print Preview"]')

    @staticmethod
    def order_number_marker(order_no: str):
        return (AppiumBy.XPATH, f'//*[contains(@text, "{order_no}")]')

    @staticmethod
    def customer_name_marker(name: str):
        return (AppiumBy.XPATH, f'//*[contains(@text, "{name}")]')

    @staticmethod
    def product_name_marker(name: str):
        return (AppiumBy.XPATH, f'//*[contains(@text, "{name}")]')


class OrderDetailsLocators:
    """
    Locators for the "Order Details" modal (opened via the "View Order"
    action) - confirmed live this is the screen that actually carries
    structured Sub Total / Total / Amount Paid / Invoice Status fields,
    plus a Payment History tab listing each payment method applied to the
    order (Cash, Credit/Debit Card, ...). Same label + following-sibling
    text pattern used elsewhere in this app.
    """
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Order Details"]')
    CLOSE_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Close")

    SUB_TOTAL_VALUE = (AppiumBy.XPATH, '//*[@text="Sub Total"]/following-sibling::*[1]')
    TOTAL_VALUE = (AppiumBy.XPATH, '//*[@text="Total"]/following-sibling::*[1]')
    AMOUNT_PAID_VALUE = (AppiumBy.XPATH, '//*[@text="Amount Paid"]/following-sibling::*[1]')
    # Scoped to plain "Paid" rather than nesting under "Invoice Status"'s
    # following-sibling - confirmed live the nested form spuriously matched
    # a stale/duplicate "Invoice Status" node elsewhere in the RN tree and
    # never resolved to a visible element. "Paid" is otherwise unique on
    # this screen (the Print Preview's "PAID" banner belongs to a separate,
    # already-closed screen).
    INVOICE_STATUS_PAID_BADGE = (AppiumBy.XPATH, '//*[@text="Paid"]')

    PAYMENT_HISTORY_TAB = (AppiumBy.ACCESSIBILITY_ID, "Payment History")
    # Payment History table rows: "Payment Type / Payment Sub Type" column -
    # confirmed live as plain "Cash" and "Credit/Debit Card / Key in
    # Credit/Debit ..." text cells (no accessible node of their own).
    CASH_PAYMENT_ROW = (AppiumBy.XPATH, '//*[@text="Cash"]')
    CARD_PAYMENT_ROW = (AppiumBy.XPATH, '//*[contains(@text, "Credit/Debit Card")]')


class VoidPaymentLocators:
    """
    Locators for the Void Payment confirmation flow (launched from a
    selected order row's action panel).

    KNOWN ISSUE (documented 2026-08-20): confirming VOID here consistently
    returns a backend "Server Error" in this environment - reproduced
    across 3 separate fresh orders and a full emulator cold-boot, ruling
    out flakiness/stale emulator state. The dialog and its buttons work
    correctly; the failure is server-side. See tests/sales_history/test_void_payment.py.

    Both dialogs here are NATIVE Android AlertDialogs (confirmed via
    android:id/button1, android:id/message resource-ids in a live dump) -
    their buttons have NO content-desc, only text, so ACCESSIBILITY_ID
    cannot match them; these use XPath text matches instead.
    """
    CONFIRM_TITLE = (AppiumBy.XPATH, '//*[@text="Void Payment"]')
    VOID_BUTTON = (AppiumBy.XPATH, '//*[@text="VOID"]')
    CANCEL_BUTTON = (AppiumBy.XPATH, '//*[@text="CANCEL"]')
    SERVER_ERROR_TITLE = (AppiumBy.XPATH, '//*[@text="Server Error"]')
    SERVER_ERROR_OK_BUTTON = (AppiumBy.XPATH, '//*[@text="OK"]')


class EditOrderLocators:
    """
    Locators for the "Edit Order" panel (launched from a selected order
    row's action panel).

    Only Sale Price/Unit is a genuinely editable per-line field - Quantity
    renders as plain non-clickable text and the line Discount's "$0.00"
    clickable field opens no editor (confirmed live: tapping it produces a
    byte-for-byte identical page-source dump). Order date is required
    before Save will proceed (blocks with a native "Select order date."
    AlertDialog otherwise) - its picker is a custom RN calendar (NOT a
    native DatePickerDialog), and its "today" cell is reliably matched via
    descriptionContains("today") regardless of the actual date.

    KNOWN ISSUE (documented 2026-08-20): even with a valid date set, Save
    consistently fails with a native AlertDialog: "This order has no
    channel id. Cannot save." - confirmed live that orders created via the
    walk-in cash-sale flow never get a channel_id set, and this screen
    exposes no Channel field/control to supply one. See
    tests/sales_history/test_edit_order.py.
    """
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Edit Order"]')
    CANCEL_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Cancel")
    SAVE_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Save")

    ORDER_DATE_FIELD = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Select date")')
    DATE_PICKER_TODAY_CELL = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("today")')

    SALE_PRICE_FIELD = (AppiumBy.XPATH, '//android.widget.EditText[@hint="0.00"]')
    SUBTOTAL_VALUE = (AppiumBy.XPATH, '//*[@text="Subtotal"]/following-sibling::*[1]')

    # Native AlertDialogs (see VoidPaymentLocators docstring) - text match,
    # not ACCESSIBILITY_ID.
    MISSING_DATE_ERROR = (AppiumBy.XPATH, '//*[@text="Select order date."]')
    NO_CHANNEL_ERROR = (AppiumBy.XPATH, '//*[@text="This order has no channel id. Cannot save."]')
    ERROR_OK_BUTTON = (AppiumBy.XPATH, '//*[@text="OK"]')
