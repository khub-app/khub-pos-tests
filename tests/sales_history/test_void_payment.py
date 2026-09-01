import allure
import yaml

from pages.receipt_complete_page import ORDER_NUMBER_PATTERN, ReceiptCompletePage
from tests.pos_base_setup import POSBaseSetup
from utilities.api_client import ApiClient
from utilities.logger import get_logger

logger = get_logger(__name__)

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


@allure.feature("Sales History")
@allure.story("Void Payment (known backend limitation)")
class TestVoidPayment(POSBaseSetup):
    """
    KNOWN ISSUE (documented 2026-08-20): confirming Void Payment on a
    completed cash order consistently returns a "Server Error" from the
    backend in this environment - reproduced across 3 separate fresh
    orders and a full emulator cold-boot, ruling out flakiness/stale
    device state. The confirmation dialog itself and its VOID/CANCEL
    buttons work correctly; the failure is server-side.

    This test intentionally asserts the CURRENT (broken) behavior rather
    than skipping it, so that the day this is fixed, the test flips to a
    real failure - a clear signal to come update it to assert successful
    voiding instead, rather than the feature quietly starting to work
    while the suite stays silent about it.

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
    void_page = None

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
                category["id"], channels, is_msa_compliant=True, price=20.00, msa_category_code=category["code"]
            )
            TestVoidPayment.customer = client.create_customer()
            logger.info(f"Generated customer: {self.customer['name']} (id={self.customer['id']})")
            logger.info(f"Generated product: {product['name']} (upc={product['upc']})")

            TestVoidPayment.sale_order = self.dashboard.start_new_sale()
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
                TestVoidPayment.order_no = receipt_complete.get_order_number()
                receipt_complete.click_done()
            logger.info(f"Order number from receipt: {self.order_no}")

    @allure.title("Locate Order in Sales History")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_04_locate_order(self):
        with allure.step("Step 2: Locate the completed order in Sales History"):
            dashboard = self.sale_order.go_to_menu()
            assert dashboard.is_loaded(), "Dashboard did not reload after completing the sale"
            TestVoidPayment.sales_history = dashboard.open_sales_history()
            self.sales_history.open_transaction_lookup_tab()

            if not self.order_no:
                row_desc = self.sales_history.get_first_row_content_desc()
                logger.warning(f"No order number captured from the receipt; resolving it from the newest row: {row_desc!r}")
                assert self.customer["name"] in row_desc, f"Newest Transaction Lookup row is not for customer {self.customer['name']}"
                match = ORDER_NUMBER_PATTERN.search(row_desc)
                assert match, f"No order number found in row content-desc: {row_desc!r}"
                TestVoidPayment.order_no = match.group()
            logger.info(f"Resolved order number: {self.order_no}")

            self.sales_history.search_by_order_id(self.order_no)
            self.sales_history.select_order_row(self.order_no)

    @allure.title("Open Void Payment and Confirm")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_05_open_and_confirm_void(self):
        with allure.step("Step 3: Open Void Payment and confirm"):
            TestVoidPayment.void_page = self.sales_history.click_void_payment()
            assert self.void_page.is_shown(), "Void Payment confirmation dialog did not open"
            self.void_page.confirm_void()

    @allure.title("Verify Known Server Error")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_06_verify_known_error(self):
        with allure.step("Step 4 (KNOWN ISSUE): backend currently rejects the void with a Server Error"):
            assert self.void_page.is_server_error_shown(), (
                "Expected the known 'Server Error' failure on Void Payment confirm, but it did not appear - "
                "the backend issue may be FIXED. If so, update this test to assert successful voiding instead."
            )
            self.void_page.dismiss_server_error()

    @allure.title("Verify Order Was Not Actually Voided")
    @allure.severity(allure.severity_level.NORMAL)
    def test_07_verify_not_voided(self):
        with allure.step("Step 5: Verify the order was NOT actually voided (lifecycle still Completed)"):
            self.sales_history.open_transaction_lookup_tab()
            self.sales_history.search_by_order_id(self.order_no)
            assert self.sales_history.is_order_row_lifecycle_completed(self.order_no), (
                f"Order {self.order_no}'s lifecycle changed even though Void Payment reported a Server Error"
            )
