import re
from decimal import ROUND_HALF_UP, Decimal

import allure
import yaml

from pages.receipt_complete_page import ReceiptCompletePage
from tests.pos_base_setup import POSBaseSetup
from utilities.api_client import ApiClient
from utilities.currency import parse_currency
from utilities.logger import get_logger

logger = get_logger(__name__)

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)

CASH_AMOUNT = Decimal("10.00")
CENTS = Decimal("0.01")


def _money(value: float) -> Decimal:
    """Converts a parsed UI amount (float, from utilities.currency.parse_currency)
    to a Decimal for currency-safe comparisons/arithmetic. Going through
    str() first avoids introducing binary-float artifacts beyond what the
    UI's own 2-decimal value already represents."""
    return Decimal(str(value))


@allure.feature("Sale Order")
@allure.story("Split Payment (Cash + Card)")
class TestSplitPayment(POSBaseSetup):
    """
    Flow: POS base setup (login, clock in, switch to Automation) -> create a
    fresh MSA product + customer via API -> Start New Sale -> add the API
    customer -> add the API product (triggers age verification) -> Split
    Payment: $10.00 cash + the remaining balance on a test card -> Complete
    Payment -> No Receipt -> verify the completed transaction in Transaction
    Lookup -> open its Print Preview and verify the invoice total matches
    the original sale total.

    Split into one pytest test method per logical step (mirrors
    khub-web-tests' runner pattern - see
    PWkhubTest/SaleBeta/.../test_sale_payment_update_void_validation_beta_runner.py)
    so each step gets its own Allure page with History/Retries tabs and
    attachments, instead of being a flat allure.step() list inside one
    monolithic test method. Steps share state via CLASS attributes
    (sale_order, customer, product, ...): pytest instantiates a fresh
    TestSplitPayment object per test method, but the class object itself
    persists across all of them for the whole run, and POSBaseSetup's
    class-scoped fixture already guarantees a single shared
    self.driver/self.dashboard for the whole class the same way.

    conftest.py's pytest_runtest_setup/makereport hooks SKIP a step (rather
    than letting it run and fail confusingly) if an earlier step in this
    same class already failed - e.g. adding the card payment skips outright
    if adding the cash payment failed, rather than running against a Split
    Payment dialog left in an unknown state.
    """

    customer = None
    product = None
    sale_order = None
    split_payment = None
    sale_total = None
    card_amount = None
    order_no = None
    sales_history = None

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
            test_data = client.create_msa_product_and_customer(price=25.00)
            TestSplitPayment.customer = test_data["customer"]
            TestSplitPayment.product = test_data["product"]
            logger.info(f"Generated customer: {self.customer['name']} (id={self.customer['id']}, email={self.customer['email']})")
            logger.info(f"Generated product: {self.product['name']} (upc={self.product['upc']}, price=${self.product['price']})")

    @allure.title("Start New Sale")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_03_start_new_sale(self):
        with allure.step("Step 2: Start a new sale and confirm Guest Customer is shown"):
            TestSplitPayment.sale_order = self.dashboard.start_new_sale()
            assert self.sale_order.is_guest_customer(), "New Sale screen did not initially show Guest Customer"

    @allure.title("Add Customer")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_04_add_customer(self):
        with allure.step("Step 3: Add the API-created customer (search by email, select from results)"):
            add_customer_page = self.sale_order.open_add_quick_customer()
            assert add_customer_page.is_shown(), "Add Customer panel did not open"
            add_customer_page.search_and_select(self.customer["email"], self.customer["name"])
            assert self.sale_order.is_customer_selected(self.customer["name"]), (
                f"Customer '{self.customer['name']}' did not replace Guest Customer as the current customer"
            )

    @allure.title("Add Product and Complete Age Verification")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_05_add_product_age_verification(self):
        with allure.step("Step 4-5: Add the API-created product, verify the cart, complete age verification"):
            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            # add_product_by_upc completes age verification internally when
            # it appears (enter DOB, Check age, Confirm & Proceed).
            age_verification_shown = self.sale_order.add_product_by_upc(self.product["upc"], dob=dob)
            assert age_verification_shown, "Age verification did not appear for the MSA-restricted product"
            assert self.sale_order.get_total_quantity() == 1, "Cart quantity is not 1 after adding the product"

    @allure.title("Capture Order Total")
    @allure.severity(allure.severity_level.NORMAL)
    def test_06_capture_order_total(self):
        with allure.step("Step 6: Capture and validate the order total; compute cash/card split"):
            TestSplitPayment.sale_total = _money(self.sale_order.get_grand_total())
            logger.info(f"Sale total: ${self.sale_total}")
            assert self.sale_total > Decimal("10.00"), f"Sale total ${self.sale_total} is not greater than $10.00"

            TestSplitPayment.card_amount = (self.sale_total - CASH_AMOUNT).quantize(CENTS, rounding=ROUND_HALF_UP)
            logger.info(f"Cash amount: ${CASH_AMOUNT}, Card amount: ${self.card_amount}")

    @allure.title("Open Split Payment")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_07_open_split_payment(self):
        with allure.step("Step 7: Open Split Payment and verify its initial state"):
            more_options = self.sale_order.open_more_options()
            assert more_options.are_all_options_displayed(), (
                "More Options did not show all of Split Payment / Add Notes / Recall Last Parked / Go to Return"
            )
            TestSplitPayment.split_payment = more_options.select_split_payment()
            assert self.split_payment.is_shown(), "Split Payment dialog did not open"
            assert _money(self.split_payment.get_total_amount()) == self.sale_total, "Split Payment Total Amount does not match the sale total"
            assert _money(self.split_payment.get_paid_amount()) == Decimal("0.00"), "Paid Amount is not $0.00 initially"
            assert _money(self.split_payment.get_remaining_amount()) == self.sale_total, "Remaining does not match the sale total initially"

    @allure.title("Add Cash Payment")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_08_add_cash_payment(self):
        with allure.step("Step 8: Add the $10.00 cash payment"):
            # Cash defaults to the entire remaining balance when added - the
            # row's amount cell (used to locate its Edit icon) still reads
            # the ORIGINAL sale total at this point, before it's edited down.
            original_total_text = f"${self.sale_total:.2f}"
            self.split_payment.click_cash()
            self.split_payment.set_cash_amount(original_total_text, f"{CASH_AMOUNT:.2f}")

            assert _money(self.split_payment.get_paid_amount()) == CASH_AMOUNT, "Paid Amount is not $10.00 after the cash entry"
            expected_remaining_after_cash = self.sale_total - CASH_AMOUNT
            assert _money(self.split_payment.get_remaining_amount()) == expected_remaining_after_cash, (
                "Remaining does not equal Total Amount - $10.00 after the cash entry"
            )

    @allure.title("Add Card Payment")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_09_add_card_payment(self):
        with allure.step("Step 9: Add the remaining balance as a card payment and submit test card details"):
            self.split_payment.click_card()
            test_card = TEST_DATA["test_card"]
            self.split_payment.pay_by_card(test_card["number"], test_card["exp_date"], test_card["cvc"])

    @allure.title("Verify and Complete Payment")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_10_complete_payment(self):
        with allure.step("Step 10: Verify the card payment was accepted and complete the payment"):
            assert self.split_payment.is_complete_payment_enabled(), "Complete Payment is not enabled after card submission"
            assert _money(self.split_payment.get_paid_amount()) == self.sale_total, "Paid Amount does not equal Total Amount after the card payment"
            assert _money(self.split_payment.get_remaining_amount()) == Decimal("0.00"), "Remaining is not $0.00 before completing payment"
            self.split_payment.complete_payment()

    @allure.title("Dismiss Receipt Prompt")
    @allure.severity(allure.severity_level.NORMAL)
    def test_11_dismiss_receipt(self):
        with allure.step("Step 11: Handle receipt delivery - select No Receipt"):
            self.split_payment.dismiss_receipt_prompt()

    @allure.title("Capture Transaction ID")
    @allure.severity(allure.severity_level.NORMAL)
    def test_12_capture_transaction_id(self):
        with allure.step("Capture the transaction/order ID if the app surfaces one"):
            receipt_complete = ReceiptCompletePage(self.driver)
            if receipt_complete.is_shown(timeout=10):
                TestSplitPayment.order_no = receipt_complete.get_order_number()
                logger.info(f"Final transaction ID: {self.order_no}")
                receipt_complete.click_done()

    @allure.title("Verify POS Ready for Next Transaction")
    @allure.severity(allure.severity_level.NORMAL)
    def test_13_final_validations(self):
        with allure.step("Final validations: sale completed, Split Payment closed, POS ready for the next transaction"):
            assert self.sale_order.is_guest_customer(), "POS did not return to an empty-cart / Guest Customer state after payment"

    @allure.title("Navigate to Transaction Lookup")
    @allure.severity(allure.severity_level.NORMAL)
    def test_14_navigate_to_transaction_lookup(self):
        with allure.step("Post-payment Step 1-2: Go to Menu -> Sales History -> Transaction Lookup"):
            dashboard = self.sale_order.go_to_menu()
            assert dashboard.is_loaded(), "Dashboard did not reload after completing the sale"
            TestSplitPayment.sales_history = dashboard.open_sales_history()
            self.sales_history.open_transaction_lookup_tab()

    @allure.title("Locate Completed Transaction")
    @allure.severity(allure.severity_level.NORMAL)
    def test_15_locate_transaction(self):
        with allure.step("Post-payment Step 3: Locate the completed split-payment transaction"):
            if self.order_no:
                self.sales_history.search_by_order_id(self.order_no)
                assert self.sales_history.is_order_row_lifecycle_completed(self.order_no), (
                    f"Order {self.order_no} is not showing a Completed lifecycle in Transaction Lookup"
                )
                actual_total_text = self.sales_history.get_order_row_sale_total_text(self.order_no)
            else:
                # Fallback per spec: no order ID captured - verify the
                # newest row belongs to this test before trusting it.
                row_desc = self.sales_history.get_first_row_content_desc()
                logger.warning(f"No order number captured from the receipt; verifying newest row instead: {row_desc!r}")
                assert self.customer["name"] in row_desc, f"Newest Transaction Lookup row is not for customer {self.customer['name']}"
                assert "Completed" in row_desc, "Newest Transaction Lookup row is not Completed"
                # The row's content-desc is "{order_no}, {date}, {name}, {name},
                # {mode}, ${total}, {lifecycle}" - the order number itself
                # contains digits that parse_currency's generic number regex
                # would otherwise match first, so pull out just the "$X.XX"
                # token rather than handing it the whole string.
                total_match = re.search(r"\$[\d,]+\.\d{2}", row_desc)
                assert total_match, f"No dollar amount found in row content-desc: {row_desc!r}"
                actual_total_text = total_match.group()

            actual_row_total = _money(parse_currency(actual_total_text))
            assert actual_row_total == self.sale_total, (
                f"Transaction Lookup Sale Total ${actual_row_total} does not match the captured sale total ${self.sale_total}"
            )

    @allure.title("Open Print Preview")
    @allure.severity(allure.severity_level.NORMAL)
    def test_16_open_print_preview(self):
        with allure.step("Post-payment Step 4: Select the transaction and open its Print Preview"):
            if self.order_no:
                self.sales_history.select_order_row(self.order_no)
            else:
                self.sales_history.select_first_row()
            assert self.sales_history.is_action_menu_enabled(), "Right-side action menu did not become enabled after selecting the row"
            invoice = self.sales_history.click_print()
            assert invoice.is_shown(), "Print Preview did not open"
            invoice.close()

    @allure.title("Validate Order Total via Order Details")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_17_validate_order_details(self):
        with allure.step("Post-payment Step 5: Validate the order's total via Order Details / View Order"):
            # The Print Preview receipt itself carries no Total/Payment
            # fields, so the actual "does the completed order's total
            # match" validation is performed against the Order Details
            # modal instead, which does expose structured Sub Total /
            # Total / Amount Paid fields.
            order_details = self.sales_history.click_view_order()
            assert order_details.is_shown(), "Order Details did not open"

            order_total = _money(order_details.get_total())
            logger.info(f"Order number={self.order_no}, expected total=${self.sale_total}, Order Details total=${order_total}")
            assert order_total == self.sale_total, (
                f"Order Details Total (${order_total}) does not match the original sale total (${self.sale_total})"
            )

            amount_paid = _money(order_details.get_amount_paid())
            assert amount_paid == self.sale_total, (
                f"Order Details Amount Paid (${amount_paid}) does not match the original sale total (${self.sale_total})"
            )
            assert order_details.is_invoice_status_paid(), "Order Details Invoice Status is not 'Paid'"

            order_details.open_payment_history_tab()
            assert order_details.has_cash_payment_row(), "Payment History does not show a Cash payment"
            assert order_details.has_card_payment_row(), "Payment History does not show a Credit/Debit Card payment"
