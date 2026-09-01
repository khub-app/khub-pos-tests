from decimal import Decimal

import allure
import yaml

from pages.receipt_complete_page import ORDER_NUMBER_PATTERN, ReceiptCompletePage
from tests.pos_base_setup import POSBaseSetup
from utilities.api_client import ApiClient
from utilities.currency import parse_currency
from utilities.logger import get_logger

logger = get_logger(__name__)

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


def _money(value: float) -> Decimal:
    return Decimal(str(value))


@allure.feature("Sale Return")
@allure.story("Return a completed cash sale")
class TestSaleReturn(POSBaseSetup):
    """
    Flow: POS base setup -> create a fresh MSA product + customer via API ->
    complete a cash sale for that product (reusing the same product/customer
    creation, add-to-cart, and age-verification flow as Split Payment and
    Create Sale Order) -> locate the completed order in Sales History ->
    Sales Return: auto-fill return quantities -> refund via cash -> verify
    the return is recorded and the order is no longer returnable.

    Split into one pytest test method per logical step (mirrors
    khub-web-tests' runner pattern) so each step gets its own Allure page
    with History/Retries tabs, instead of a flat allure.step() list inside
    one monolithic test. Steps share state via CLASS attributes, safe
    because the class object persists across every test method here even
    though pytest instantiates a fresh one per method. conftest.py's hooks
    skip a step if an earlier one in this same class failed, rather than
    running it against unknown app state.
    """

    customer = None
    product = None
    sale_order = None
    sub_total = None
    sale_total = None
    cash_page = None
    order_no = None
    sales_history = None
    return_page = None
    payment_page = None

    @allure.title("Preconditions")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_preconditions(self):
        with allure.step("Preconditions: base setup succeeded, Automation active, shift open, Start New Sale enabled"):
            switch_user = TEST_DATA["shift"]["switch_user"]
            assert self.dashboard.is_admin_user(switch_user), f"Expected 'ADMIN: {switch_user}' badge not shown"
            assert self.dashboard.is_shift_open(), "Shift is not open"
            assert self.dashboard.is_start_new_sale_enabled(), "Start New Sale is not enabled"

    @allure.title("Prepare Test Data (Customer + MSA Product)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_prepare_test_data(self):
        with allure.step("Step 1: Prepare test data through the API (customer + MSA-restricted product)"):
            client = ApiClient()
            test_data = client.create_msa_product_and_customer(price=12.00)
            TestSaleReturn.customer = test_data["customer"]
            TestSaleReturn.product = test_data["product"]
            logger.info(f"Generated customer: {self.customer['name']} (id={self.customer['id']}, email={self.customer['email']})")
            logger.info(f"Generated product: {self.product['name']} (upc={self.product['upc']}, price=${self.product['price']})")

    @allure.title("Start New Sale, Add Customer and Product")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_03_add_customer_and_product(self):
        with allure.step("Step 2: Start a new sale, add the customer and product"):
            TestSaleReturn.sale_order = self.dashboard.start_new_sale()
            assert self.sale_order.is_guest_customer(), "New Sale screen did not initially show Guest Customer"

            add_customer_page = self.sale_order.open_add_quick_customer()
            assert add_customer_page.is_shown(), "Add Customer panel did not open"
            add_customer_page.search_and_select(self.customer["email"], self.customer["name"])
            assert self.sale_order.is_customer_selected(self.customer["name"]), (
                f"Customer '{self.customer['name']}' did not replace Guest Customer as the current customer"
            )

            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            age_verification_shown = self.sale_order.add_product_by_upc(self.product["upc"], dob=dob)
            assert age_verification_shown, "Age verification did not appear for the MSA-restricted product"
            assert self.sale_order.get_total_quantity() == 1, "Cart quantity is not 1 after adding the product"

    @allure.title("Pay Exact Amount Due in Cash")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_04_pay_cash(self):
        with allure.step("Step 3: Pay the exact amount due in cash"):
            # Sales Return's "Total to refund" / "Return Total" reflect the
            # pre-tax Sub Total, not the tax-inclusive amount actually paid -
            # confirmed live (a real order with tax: refund total came back
            # as the product's $12.00 sub total, not the $13.20 grand total
            # that was paid). A plain product return doesn't auto-refund
            # tax; that needs the return screen's own separate "+ Add tax"
            # step, which this basic flow doesn't exercise.
            TestSaleReturn.sub_total = _money(self.sale_order.get_sub_total())
            TestSaleReturn.sale_total = _money(self.sale_order.get_grand_total())
            logger.info(f"Sub total: ${self.sub_total}, sale total (paid): ${self.sale_total}")

            TestSaleReturn.cash_page = self.sale_order.tap_cash()
            amount_due = _money(parse_currency(self.cash_page.get_amount_due()))
            assert amount_due == self.sale_total, f"Amount Due (${amount_due}) does not match the cart total (${self.sale_total})"
            self.cash_page.pay_exact_amount_due()
            self.cash_page.dismiss_receipt_prompt()

    @allure.title("Capture Order Number")
    @allure.severity(allure.severity_level.NORMAL)
    def test_05_capture_order_number(self):
        with allure.step("Capture the order number if the app surfaces one"):
            receipt_complete = ReceiptCompletePage(self.driver)
            if receipt_complete.is_shown(timeout=10):
                TestSaleReturn.order_no = receipt_complete.get_order_number()
                receipt_complete.click_done()
            logger.info(f"Order number from receipt: {self.order_no}")

    @allure.title("Navigate to Transaction Lookup")
    @allure.severity(allure.severity_level.NORMAL)
    def test_06_navigate_to_transaction_lookup(self):
        with allure.step("Go to Menu -> Sales History -> Transaction Lookup"):
            dashboard = self.sale_order.go_to_menu()
            assert dashboard.is_loaded(), "Dashboard did not reload after completing the sale"
            TestSaleReturn.sales_history = dashboard.open_sales_history()
            self.sales_history.open_transaction_lookup_tab()

    @allure.title("Resolve Order Number")
    @allure.severity(allure.severity_level.NORMAL)
    def test_07_resolve_order_number(self):
        with allure.step("Fallback: resolve the order number from the newest Transaction Lookup row, if not already captured"):
            if not self.order_no:
                row_desc = self.sales_history.get_first_row_content_desc()
                logger.warning(f"No order number captured from the receipt; resolving it from the newest row: {row_desc!r}")
                assert self.customer["name"] in row_desc, f"Newest Transaction Lookup row is not for customer {self.customer['name']}"
                assert "Completed" in row_desc, "Newest Transaction Lookup row is not Completed"
                match = ORDER_NUMBER_PATTERN.search(row_desc)
                assert match, f"No order number found in row content-desc: {row_desc!r}"
                TestSaleReturn.order_no = match.group()
            logger.info(f"Resolved order number: {self.order_no}")

    @allure.title("Open Sales Return")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_08_open_sales_return(self):
        with allure.step("Step 4: Open Sales Return for the order and verify its initial state"):
            TestSaleReturn.return_page = self.sales_history.return_order(self.order_no)
            assert self.return_page.is_shown(self.order_no), "Sales Return screen did not open for the expected order"
            assert _money(self.return_page.get_total_to_refund()) == Decimal("0.00"), "Total to refund is not $0.00 before Auto Fill"
            assert not self.return_page.is_return_button_enabled(), "Return button is enabled before any quantity is selected"

    @allure.title("Auto-Fill Return Quantities")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_09_auto_fill_return_quantities(self):
        with allure.step("Step 5: Auto-fill return quantities and verify the refund total"):
            self.return_page.auto_fill()
            assert self.return_page.get_total_quantity() == 1, "Total Quantity is not 1 after Auto Fill"
            assert _money(self.return_page.get_total_to_refund()) == self.sub_total, (
                "Total to refund does not match the original sale's sub total after Auto Fill"
            )
            assert self.return_page.is_return_button_enabled(), "Return button is not enabled after Auto Fill"

    @allure.title("Submit Return and Verify Payment Popup")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_10_submit_return(self):
        with allure.step("Step 6: Submit the return and verify the payment method popup"):
            TestSaleReturn.payment_page = self.return_page.submit_return()
            assert self.payment_page.is_shown(), "Choose Your Payment Method did not open"
            assert _money(self.payment_page.get_return_total()) == self.sub_total, "Return Total does not match the original sale's sub total"
            assert _money(self.payment_page.get_returnable_amount()) == self.sub_total, (
                "Returnable Amount does not match the original sale's sub total"
            )
            assert self.payment_page.get_customer_name() == self.customer["name"], "Refund customer does not match the sale's customer"

    @allure.title("Complete Return via Cash")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_11_complete_return(self):
        with allure.step("Step 7: Complete the return via cash and verify it was recorded"):
            self.payment_page.enter_return_reason("Automated test return")
            self.payment_page.complete_return()

            return_no = self.payment_page.get_return_number()
            logger.info(f"Return number: {return_no}")
            assert return_no, "No 'Return ... created successfully' confirmation was shown"

    @allure.title("Verify Order No Longer Returnable")
    @allure.severity(allure.severity_level.NORMAL)
    def test_12_verify_not_returnable(self):
        with allure.step("Step 8: Verify the original order is no longer returnable"):
            assert self.sales_history.is_no_returnable_orders_shown(), (
                f"Order {self.order_no} is still showing as returnable after its return was completed"
            )
