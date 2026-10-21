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
@allure.story("Partial Return (1 of 2 units)")
class TestPartialReturn(POSBaseSetup):
    """
    The existing Sale Return test only ever fully returns a single-qty
    order via Auto Fill. This buys 2 units of one product, then returns
    only 1 of them via the Sales Return screen's own per-line "Increase
    return quantity" stepper (confirmed live 2026-10-20 to have a real
    content-desc, unlike the cart's own qty stepper) - NOT Auto Fill, which
    jumps straight to the order's full quantity.

    Confirmed live: one tap correctly scales Total Quantity to 1 (not 2)
    and Total to Refund to 1x unit price (not 2x), proving the return
    screen computes a genuine partial refund rather than always returning
    the full order.
    """

    product = None
    sale_order = None
    unit_price = None
    cash_page = None
    order_no = None
    sales_history = None
    return_page = None
    payment_page = None

    @allure.title("Prepare Test Data")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_prepare_test_data(self):
        with allure.step("Step 1: Prepare a fresh product through the API"):
            client = ApiClient()
            category = client.EXISTING_MSA_CATEGORY
            channels = client.get_channels()
            TestPartialReturn.product = client.create_product(
                category["id"], channels, is_msa_compliant=True, price=10.00, msa_category_code=category["code"]
            )
            TestPartialReturn.unit_price = _money(self.product["price"])
            logger.info(f"Generated product: {self.product['name']} (upc={self.product['upc']}, price=${self.product['price']})")

    @allure.title("Buy 2 Units and Pay Cash")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_buy_two_units_pay_cash(self):
        with allure.step("Step 2: Add the product, bump quantity to 2, and pay the exact amount due in cash"):
            TestPartialReturn.sale_order = self.dashboard.start_new_sale()
            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            self.sale_order.add_product_by_upc(self.product["upc"], dob=dob)
            self.sale_order.tap_quantity_increment()
            assert self.sale_order.get_total_quantity() == 2, "Cart quantity is not 2"
            assert _money(self.sale_order.get_sub_total()) == self.unit_price * 2, "Sub Total is not 2x unit price"

            TestPartialReturn.cash_page = self.sale_order.tap_cash()
            self.cash_page.pay_exact_amount_due()
            self.cash_page.dismiss_receipt_prompt()

    @allure.title("Resolve Order Number and Open Sales Return")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_03_resolve_order_and_open_return(self):
        with allure.step("Step 3: Resolve the order number and open Sales Return for it"):
            receipt_complete = ReceiptCompletePage(self.driver)
            if receipt_complete.is_shown(timeout=10):
                TestPartialReturn.order_no = receipt_complete.get_order_number()
                receipt_complete.click_done()

            dashboard = self.sale_order.go_to_menu()
            TestPartialReturn.sales_history = dashboard.open_sales_history()
            self.sales_history.open_transaction_lookup_tab()

            if not self.order_no:
                row_desc = self.sales_history.get_first_row_content_desc()
                match = ORDER_NUMBER_PATTERN.search(row_desc)
                assert match, f"No order number found in row content-desc: {row_desc!r}"
                TestPartialReturn.order_no = match.group()
            logger.info(f"Order number: {self.order_no}")

            TestPartialReturn.return_page = self.sales_history.return_order(self.order_no)
            assert self.return_page.is_shown(self.order_no), "Sales Return screen did not open for the expected order"
            assert self.return_page.get_total_quantity() == 0, "Total Quantity is not 0 before any return quantity is selected"
            assert not self.return_page.is_return_button_enabled(), "Return button is enabled before any quantity is selected"

    @allure.title("Select a Partial Return Quantity and Verify the Math")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_04_partial_return_quantity_math(self):
        with allure.step("Step 4: Tap 'Increase return quantity' ONCE (not Auto Fill) and verify the refund is 1x unit price"):
            self.return_page.increase_return_quantity()

            assert self.return_page.get_total_quantity() == 1, (
                "Total Quantity is not 1 after a single Increase tap - expected a partial (not full) return quantity"
            )
            assert _money(self.return_page.get_total_to_refund()) == self.unit_price, (
                f"Total to refund (${self.return_page.get_total_to_refund()}) is not 1x unit price (${self.unit_price}) - "
                f"a single Increase tap should refund only one of the two units purchased"
            )
            assert self.return_page.is_return_button_enabled(), "Return button is not enabled after selecting a return quantity"

    @allure.title("Submit and Complete the Partial Return")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_05_complete_partial_return(self):
        with allure.step("Step 5: Submit the partial return, verify the payment popup, and complete it via cash"):
            TestPartialReturn.payment_page = self.return_page.submit_return()
            assert self.payment_page.is_shown(), "Choose Your Payment Method did not open"
            assert _money(self.payment_page.get_return_total()) == self.unit_price, (
                f"Return Total (${self.payment_page.get_return_total()}) does not match 1x unit price (${self.unit_price})"
            )

            self.payment_page.enter_return_reason("Automated partial return test")
            self.payment_page.complete_return()

            return_no = self.payment_page.get_return_number()
            logger.info(f"Return number: {return_no}")
            assert return_no, "No 'Return ... created successfully' confirmation was shown"
