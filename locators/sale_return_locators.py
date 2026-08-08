from appium.webdriver.common.appiumby import AppiumBy


class SalesReturnTabLocators:
    """Locators for navigating to and starting a return.

    CORRECTED FLOW (confirmed working via a live manual walkthrough): from
    Sales History, open the **Transaction Lookup** tab (NOT the "Sales
    Returns" tab), search/select the order row directly, then tap that
    row's own contextual "Sales Return" action button — no separate
    "Create Sale Return" button or intermediate search screen involved.

    The previous approach (Sales Returns tab -> Create Sale Return button ->
    search -> select -> Sales Return) went through the UI motions without
    error, but the resulting "return" could never be found afterwards when
    searching by the original order number — that flow is suspected to be
    for a different purpose (e.g. Browse/manage already-created returns) and
    is NOT the correct way to create a new one. Keeping SALES_RETURNS_TAB
    here only because Transaction Lookup sits alongside it in the same tab
    bar (Sales History | Transaction Lookup | Sales Returns | Payments).
    """
    TRANSACTION_LOOKUP_TAB = (AppiumBy.XPATH, '//*[@text="Transaction Lookup"]')
    SALES_RETURNS_TAB = (AppiumBy.XPATH, '//*[@text="Sales Returns"]')

    @staticmethod
    def order_row(order_no: str):
        return (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().descriptionContains("{order_no}")')

    # NOTE: descriptionContains(", Sales Return") — the leading ", " excludes
    # the unrelated "Sales Returns" tab label, which would otherwise also
    # match a plain descriptionContains("Sales Return").
    SALES_RETURN_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains(", Sales Return")')


class SaleReturnScreenLocators:
    """Locators for the Sales Return quantity/products screen."""
    AUTO_FILL_LINK = (AppiumBy.XPATH, '//*[@text="Auto Fill"]')
    RETURN_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Return")


class ReturnPaymentMethodLocators:
    """Locators for the "Choose Your Payment Method" popup shown after tapping Return."""
    MODAL_TITLE = (AppiumBy.XPATH, '//*[@text="Choose Your Payment Method"]')
    RETURN_REASON_FIELD = (AppiumBy.XPATH, '//android.widget.EditText[@hint="Describe the reason for this return"]')
    COMPLETE_RETURN_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Complete Return")
