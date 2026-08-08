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
