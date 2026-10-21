import allure
import yaml

from tests.pos_base_setup import POSBaseSetup
from utilities.api_client import ApiClient
from utilities.logger import get_logger

logger = get_logger(__name__)

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


@allure.feature("Sale Order")
@allure.story("Cash Overpayment and Change Due")
class TestCashOverpaymentChangeDue(POSBaseSetup):
    """
    The existing payment tests only ever tender the exact amount due. This
    tenders more than the amount due and verifies the modal's own live
    "Change Due" field computes the difference correctly (confirmed live
    2026-10-20: $20.00 received on a $10.00 due order reads back exactly
    $10.00 Change Due), then completes the payment normally.
    """

    product = None
    sale_order = None
    cash_page = None
    AMOUNT_TENDERED = "20.00"

    @allure.title("Prepare Test Data")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_prepare_test_data(self):
        with allure.step("Step 1: Prepare a fresh $10 product through the API"):
            client = ApiClient()
            category = client.EXISTING_MSA_CATEGORY
            channels = client.get_channels()
            TestCashOverpaymentChangeDue.product = client.create_product(
                category["id"], channels, is_msa_compliant=True, price=10.00, msa_category_code=category["code"]
            )
            logger.info(f"Generated product: {self.product['name']} (upc={self.product['upc']}, price=${self.product['price']})")

    @allure.title("Add Product and Open Cash Payment")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_add_product_and_open_cash(self):
        with allure.step("Step 2: Start a new sale, add the product, and open Cash Payment"):
            TestCashOverpaymentChangeDue.sale_order = self.dashboard.start_new_sale()
            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            self.sale_order.add_product_by_upc(self.product["upc"], dob=dob)
            TestCashOverpaymentChangeDue.cash_page = self.sale_order.tap_cash()

    @allure.title("Tender More Than Amount Due and Verify Change Due")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_03_overpay_and_verify_change_due(self):
        with allure.step(f"Step 3: Enter ${self.AMOUNT_TENDERED} cash received and verify the computed Change Due"):
            amount_due = float(self.cash_page.get_amount_due())
            self.cash_page.enter_amount(self.AMOUNT_TENDERED)

            assert self.cash_page.is_confirm_enabled(), "Confirm should be enabled for a valid overpayment"
            expected_change = round(float(self.AMOUNT_TENDERED) - amount_due, 2)
            actual_change = self.cash_page.get_change_due()
            assert actual_change == expected_change, (
                f"Change Due shows ${actual_change}, expected ${expected_change} "
                f"(${self.AMOUNT_TENDERED} tendered - ${amount_due} due)"
            )

    @allure.title("Complete the Overpayment")
    @allure.severity(allure.severity_level.NORMAL)
    def test_04_complete_payment(self):
        with allure.step("Step 4: Confirm the payment and dismiss the receipt prompt"):
            self.cash_page.confirm()
            self.cash_page.dismiss_receipt_prompt()


@allure.feature("Sale Order")
@allure.story("Cash Underpayment Blocked")
class TestCashUnderpaymentBlocked(POSBaseSetup):
    """
    A cashier entering less cash than the amount due cannot confirm the
    payment. Confirmed live 2026-10-20: Confirm reports enabled="false"
    when cash received ($5.00) is less than amount due ($10.00) - the app
    blocks this at the UI level rather than accepting a partial payment.
    """

    product = None
    sale_order = None
    cash_page = None
    AMOUNT_TENDERED = "5.00"

    @allure.title("Prepare Test Data")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_prepare_test_data(self):
        with allure.step("Step 1: Prepare a fresh $10 product through the API"):
            client = ApiClient()
            category = client.EXISTING_MSA_CATEGORY
            channels = client.get_channels()
            TestCashUnderpaymentBlocked.product = client.create_product(
                category["id"], channels, is_msa_compliant=True, price=10.00, msa_category_code=category["code"]
            )
            logger.info(f"Generated product: {self.product['name']} (upc={self.product['upc']}, price=${self.product['price']})")

    @allure.title("Add Product and Enter Less Than Amount Due")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_underpay_is_blocked(self):
        with allure.step(f"Step 2: Start a new sale, add the product, and tender only ${self.AMOUNT_TENDERED}"):
            TestCashUnderpaymentBlocked.sale_order = self.dashboard.start_new_sale()
            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            self.sale_order.add_product_by_upc(self.product["upc"], dob=dob)
            TestCashUnderpaymentBlocked.cash_page = self.sale_order.tap_cash()

            self.cash_page.enter_amount(self.AMOUNT_TENDERED)
            assert not self.cash_page.is_confirm_enabled(), (
                f"Confirm should be disabled when tendering ${self.AMOUNT_TENDERED} against a larger amount due"
            )

    @allure.title("Verify the Cart Is Unaffected After Closing the Modal")
    @allure.severity(allure.severity_level.NORMAL)
    def test_03_cart_unaffected_after_closing(self):
        with allure.step("Step 3: Close the modal without confirming and verify the sale is still pending"):
            self.cash_page.close_without_confirming()
            assert self.sale_order.get_sub_total() == self.product["price"], (
                "Cart Sub Total changed despite no payment being confirmed"
            )
