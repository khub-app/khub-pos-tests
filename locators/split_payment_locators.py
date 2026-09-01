from appium.webdriver.common.appiumby import AppiumBy


class AddCustomerLocators:
    """Locators for the "Add Customer" side panel (opened via Add Quick Customer)."""
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Add Customer"]')
    EMAIL_SEARCH_FIELD = (AppiumBy.XPATH, '//android.widget.EditText[@hint="Customer Email Address"]')
    # Confirmed live via page-source dump: the header title TextView has no
    # content-desc, so this exact accessibility id matches only the actual
    # confirm button (bounds near the bottom of the panel) - distinct from
    # ", Add New Customer" (the manual create-new-customer button).
    CONFIRM_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Add Customer")

    @staticmethod
    def search_result_row(customer_name: str):
        return (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().descriptionContains("{customer_name}")')


class MoreOptionsLocators:
    """Locators for the "More Options" dialog (opened from the New Sale screen)."""
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="More Options"]')
    SPLIT_PAYMENT_OPTION = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Split Payment")')
    ADD_NOTES_OPTION = (AppiumBy.XPATH, '//*[@text="Add Notes"]')
    RECALL_LAST_PARKED_OPTION = (AppiumBy.XPATH, '//*[@text="Recall Last Parked"]')
    GO_TO_RETURN_OPTION = (AppiumBy.XPATH, '//*[@text="Go to Return"]')
    # A confirmation popup sometimes appears after selecting Split Payment.
    CONFIRM_OK_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "OK")


class SplitPaymentLocators:
    """
    Locators for the "Split Payment" dialog.

    NOTE: the Cash/Card buttons here (leading ", " in content-desc) are
    DIFFERENT elements than SaleOrderLocators.CASH_BUTTON/CARD_BUTTON, which
    are the direct (non-split) payment buttons on the New Sale screen itself.
    """
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Split Payment"]')
    TOTAL_AMOUNT_VALUE = (AppiumBy.XPATH, '//*[@text="Total Amount"]/following-sibling::*[1]')
    PAID_AMOUNT_VALUE = (AppiumBy.XPATH, '//*[@text="Paid Amount"]/following-sibling::*[1]')
    REMAINING_VALUE = (AppiumBy.XPATH, '//*[@text="Remaining"]/following-sibling::*[1]')
    CASH_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains(", Cash")')
    CARD_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains(", Credit/Debit Card")')
    CANCEL_BUTTON = (AppiumBy.XPATH, '//*[@text="Cancel"]/..')
    COMPLETE_PAYMENT_BUTTON = (AppiumBy.XPATH, '//*[@text="Complete Payment"]/..')
    # After the Card Amount popup is confirmed, the "Card - NMI Terminal"
    # section appears with a choice of "Charge $X on reader" (physical NMI
    # reader - unusable on this emulator, see CardKeyInLocators docstring)
    # or this button, which reveals a further "Key In Card" choice between
    # the physical reader again and the actual manual-entry webview.
    ENTER_CARD_DETAILS_MANUALLY_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Enter Card Details Manually")'
    )
    # Confirmed live via page-source dump: visible label is "Enter card
    # info" here (distinct from "Enter Card Details Manually" above, which
    # is a separate, earlier button in the same flow) - tapping this is
    # what actually attaches the WEBVIEW_com.anonymous.ititansapp context.
    ENTER_CARD_INFO_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Enter card info")'
    )

    @staticmethod
    def added_payment_row(method_label: str):
        """Row in the Added Payments table for "Cash" or "Card"."""
        return (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().descriptionContains("{method_label}")')

    @staticmethod
    def edit_icon_for_amount(amount_text: str):
        """The Edit (pencil) icon has no accessible node of its own - it's
        the first following-sibling of the row's amount cell, which IS
        reliably matchable via its exact content-desc (e.g. "$10.00")."""
        return (AppiumBy.XPATH, f'//*[@content-desc="{amount_text}"]/following-sibling::*[1]')


class CashAmountPopupLocators:
    """Locators for the "Cash Amount" popup (opened via the Added Payments row's Edit icon)."""
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Cash Amount"]')
    DELETE_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains(", Delete")')
    CONFIRM_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Confirm")

    @staticmethod
    def digit(d: str):
        return (AppiumBy.ACCESSIBILITY_ID, d)


class CardAmountPopupLocators:
    """Locators for the "Card Amount" popup, shown immediately after tapping
    Split Payment's Card button. Same numeric-keypad layout/content-desc
    pattern as CashAmountPopupLocators (confirmed live via page-source
    dump) - kept as its own class since it's a functionally distinct
    dialog (Card Amount vs Cash Amount) even though the widget is
    identical. The amount is pre-filled with the entire remaining balance,
    which is what this suite's Split Payment flow wants, so only Confirm
    is needed - no digit entry."""
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Card Amount"]')
    CONFIRM_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Confirm")


class ReceiptCompleteLocators:
    """Locators for the "Receipt complete" confirmation shown after a
    receipt-delivery choice (No Receipt, whether tapped directly or reached
    via the 30s countdown timing out) is resolved. Its "Reference" line
    embeds the real order number (e.g. "RCP-SO-260819-63404-...") -
    confirmed live as the most reliable place to capture it, since the
    order/customer list API's customer_id filter param does not actually
    filter (silently returns unrelated orders), and no order number is
    otherwise surfaced anywhere in the checkout UI."""
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Receipt complete"]')
    DONE_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Done")
    REFERENCE_TEXT = (AppiumBy.XPATH, '//*[contains(@text, "Reference")]')


class CardPaymentWebviewLocators:
    """
    CSS selectors for the NMI Collect.js card-entry form. This form lives in
    an Appium WEBVIEW context (Chrome, proxied via chromedriver) rather than
    the native accessibility tree - each field is its own cross-origin
    iframe (id="CollectJSInline{field}"), per NMI's PCI-DSS SAQ-A hosted-
    fields design where card data never touches the app's own page/context.

    Requires the Appium server to be started with
    `--allow-insecure uiautomator2:chromedriver_autodownload` and the
    session capability `chromedriverAutodownload: True` (see
    utilities/driver_manager.py) - without both, switching into the webview
    context raises "No Chromedriver found that can automate Chrome ...".
    """
    CARD_NUMBER_IFRAME_ID = "CollectJSInlineccnumber"
    EXP_DATE_IFRAME_ID = "CollectJSInlineccexp"
    CVC_IFRAME_ID = "CollectJSInlinecvv"
    SUBMIT_BUTTON_CSS = "#payButton"
