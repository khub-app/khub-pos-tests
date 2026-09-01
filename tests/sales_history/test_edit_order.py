from decimal import Decimal

import allure
import yaml

from pages.receipt_complete_page import ORDER_NUMBER_PATTERN, ReceiptCompletePage
from tests.pos_base_setup import POSBaseSetup
from utilities.api_client import ApiClient
from utilities.logger import get_logger

logger = get_logger(__name__)

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


def _money(value: float) -> Decimal:
    return Decimal(str(value))


@allure.feature("Sales History")
@allure.story("Edit Order (known backend limitation)")
class TestEditOrder(POSBaseSetup):
    """
    KNOWN ISSUE (documented 2026-08-20): saving an edited order (a changed
    Sale Price/Unit, with the also-required Order date set) consistently
    fails with a native "This order has no channel id. Cannot save."
    dialog - confirmed live that orders created via the walk-in cash-sale
    flow never get a channel_id set, and the Edit Order screen exposes no
    Channel field/control to supply one itself. Everything up to Save
    works correctly: the price EditText accepts input, totals (Subtotal)
    recalculate live, and the date picker's required-field validation
    clears once a date is set.

    This test intentionally asserts the CURRENT (broken) behavior rather
    than skipping it, so that the day this is fixed, the test flips to a
    real failure - a clear signal to come update it to assert a successful
    save instead, rather than the feature quietly starting to work while
    the suite stays silent about it.

    Split into one pytest test method per logical step (mirrors
    khub-web-tests' runner pattern) so each step gets its own Allure page
    with History/Retries tabs, instead of a flat allure.step() list inside
    one monolithic test. Steps share state via CLASS attributes, safe
    because the class object persists across every test method here even
    though pytest instantiates a fresh one per method.
    """

    customer = None
    sale_order = None
    order_no = None
    sales_history = None
    edit_order = None

    @allure.title("Preconditions")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_preconditions(self):
        with allure.step("Preconditions: base setup succeeded"):
            switch_user = TEST_DATA["shift"]["switch_user"]
            assert self.dashboard.is_admin_user(switch_user), f"Expected 'ADMIN: {switch_user}' badge not shown"

    @allure.title("Prepare Test Data and Complete Cash Sale")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_prepare_and_complete_sale(self):
        with allure.step("Step 1: Prepare test data and complete a cash sale"):
            client = ApiClient()
            category = client.EXISTING_MSA_CATEGORY
            channels = client.get_channels()
            product = client.create_product(
                category["id"], channels, is_msa_compliant=True, price=40.00, msa_category_code=category["code"]
            )
            TestEditOrder.customer = client.create_customer()
            logger.info(f"Generated customer: {self.customer['name']} (id={self.customer['id']})")
            logger.info(f"Generated product: {product['name']} (upc={product['upc']})")

            TestEditOrder.sale_order = self.dashboard.start_new_sale()
            add_customer_page = self.sale_order.open_add_quick_customer()
            add_customer_page.search_and_select(self.customer["email"], self.customer["name"])

            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            self.sale_order.add_product_by_upc(product["upc"], dob=dob)

            cash_page = self.sale_order.tap_cash()
            cash_page.pay_exact_amount_due()
            cash_page.dismiss_receipt_prompt()

    @allure.title("Capture Order Number")
    @allure.severity(allure.severity_level.NORMAL)
    def test_03_capture_order_number(self):
        with allure.step("Capture the order number if the app surfaces one"):
            receipt_complete = ReceiptCompletePage(self.driver)
            if receipt_complete.is_shown(timeout=10):
                TestEditOrder.order_no = receipt_complete.get_order_number()
                receipt_complete.click_done()
            logger.info(f"Order number from receipt: {self.order_no}")

    @allure.title("Locate Order in Sales History")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_04_locate_order(self):
        with allure.step("Step 2: Locate the completed order in Sales History"):
            dashboard = self.sale_order.go_to_menu()
            assert dashboard.is_loaded(), "Dashboard did not reload after completing the sale"
            TestEditOrder.sales_history = dashboard.open_sales_history()
            self.sales_history.open_transaction_lookup_tab()

            if not self.order_no:
                row_desc = self.sales_history.get_first_row_content_desc()
                logger.warning(f"No order number captured from the receipt; resolving it from the newest row: {row_desc!r}")
                assert self.customer["name"] in row_desc, f"Newest Transaction Lookup row is not for customer {self.customer['name']}"
                match = ORDER_NUMBER_PATTERN.search(row_desc)
                assert match, f"No order number found in row content-desc: {row_desc!r}"
                TestEditOrder.order_no = match.group()
            logger.info(f"Resolved order number: {self.order_no}")

            self.sales_history.search_by_order_id(self.order_no)
            self.sales_history.select_order_row(self.order_no)

    @allure.title("Open Edit Order and Change Sale Price")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_05_edit_price(self):
        with allure.step("Step 3: Open Edit Order, set the required Order date, and change the Sale Price"):
            TestEditOrder.edit_order = self.sales_history.click_edit_order()
            assert self.edit_order.is_shown(), "Edit Order did not open"

            self.edit_order.set_order_date_to_today()
            self.edit_order.set_sale_price("25")

            new_subtotal = _money(self.edit_order.get_subtotal())
            assert new_subtotal == Decimal("25.00"), (
                f"Subtotal did not recalculate live after the price edit (got ${new_subtotal})"
            )

    @allure.title("Attempt to Save")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_06_attempt_save(self):
        with allure.step("Step 4: Attempt to save"):
            self.edit_order.save()

    @allure.title("Verify Known Missing-Channel Error")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_07_verify_known_error(self):
        with allure.step("Step 5 (KNOWN ISSUE): backend currently rejects the save with a missing-channel error"):
            assert self.edit_order.is_no_channel_error_shown(), (
                "Expected the known 'This order has no channel id. Cannot save.' failure, but it did not "
                "appear - the backend issue may be FIXED. If so, update this test to assert a successful "
                "save instead."
            )
            self.edit_order.dismiss_error()
            self.edit_order.cancel()
