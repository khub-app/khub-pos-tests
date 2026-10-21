import allure
import yaml

from tests.pos_base_setup import POSBaseSetup
from utilities.api_client import ApiClient
from utilities.logger import get_logger

logger = get_logger(__name__)

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


@allure.feature("Sale Order")
@allure.story("Additional Discount — Fixed ($) Exceeding Subtotal")
class TestFixedDiscountExceedsSubtotal(POSBaseSetup):
    """
    A cashier can fat-finger a fixed-dollar discount larger than the cart's
    own total. Confirmed live 2026-10-20: the app blocks this at the UI
    level rather than silently clamping the total at $0.00 or letting it go
    negative - Confirm becomes disabled (enabled="false") and a validation
    message "Discount cannot exceed the total amount." appears. The
    modal's own "Total After Discount" preview still shows the raw
    (negative) unclamped number, but it can never actually be applied.
    """

    product = None
    sale_order = None
    sub_total = None
    DISCOUNT_AMOUNT = "50"  # on a $20 cart

    @allure.title("Prepare Test Data")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_prepare_test_data(self):
        with allure.step("Step 1: Prepare a fresh $20 product through the API"):
            client = ApiClient()
            category = client.EXISTING_MSA_CATEGORY
            channels = client.get_channels()
            TestFixedDiscountExceedsSubtotal.product = client.create_product(
                category["id"], channels, is_msa_compliant=True, price=20.00, msa_category_code=category["code"]
            )
            logger.info(f"Generated product: {self.product['name']} (upc={self.product['upc']}, price=${self.product['price']})")

    @allure.title("Start New Sale and Add Product")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_start_new_sale_and_add_product(self):
        with allure.step("Step 2: Start a new sale and add the product"):
            TestFixedDiscountExceedsSubtotal.sale_order = self.dashboard.start_new_sale()
            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            self.sale_order.add_product_by_upc(self.product["upc"], dob=dob)
            TestFixedDiscountExceedsSubtotal.sub_total = self.sale_order.get_sub_total()
            assert self.sub_total == self.product["price"], (
                f"Cart Sub Total (${self.sub_total}) does not match the product's price (${self.product['price']})"
            )

    @allure.title("Enter a Discount Larger Than the Cart and Verify It Is Blocked")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_03_discount_exceeding_total_is_blocked(self):
        with allure.step(f"Step 3: Enter a ${self.DISCOUNT_AMOUNT} fixed discount on a ${self.sub_total} cart"):
            discount_page = self.sale_order.open_additional_discount()
            discount_page.switch_to_fixed_amount()
            discount_page.enter_amount(self.DISCOUNT_AMOUNT)

            assert discount_page.is_exceeds_total_validation_shown(), (
                "Expected 'Discount cannot exceed the total amount.' validation message did not appear"
            )
            assert not discount_page.is_confirm_enabled(), (
                "Confirm should be disabled when the fixed discount exceeds the cart total"
            )

    @allure.title("Verify the Cart Is Unaffected After Closing the Modal")
    @allure.severity(allure.severity_level.NORMAL)
    def test_04_cart_unaffected_after_closing(self):
        with allure.step("Step 4: Close the modal without confirming and verify the cart kept its original total"):
            from pages.discount_page import DiscountPage

            DiscountPage(self.driver).close_without_confirming()
            assert self.sale_order.get_sub_total() == self.sub_total, "Sub Total changed despite no discount being confirmed"
            assert self.sale_order.get_grand_total() == self.sub_total, "Grand Total changed despite no discount being confirmed"


@allure.feature("Sale Order")
@allure.story("Additional Discount — Percentage Input Capped at 99%")
class TestPercentageDiscountOver100(POSBaseSetup):
    """
    A cashier typing a 3-digit percentage (e.g. "150" meaning 150%, a typo
    for 15%) cannot actually enter it. Confirmed live 2026-10-20: the
    Discount (%) digit pad silently caps/truncates input at 2 digits - the
    3rd keystroke is simply dropped, so "150" registers as "15%", never
    150%. There is no validation message for this one (unlike the Fixed ($)
    case) because the field never reaches an invalid value in the first
    place. Confirming applies the (correctly capped) 15% discount, which
    this test verifies via the cart's real grand total rather than trying
    to read the modal's own preview fields (see DiscountLocators' docstring
    on why that's unreliable).
    """

    product = None
    sale_order = None
    sub_total = None
    TYPED_PERCENTAGE = "150"
    EXPECTED_APPLIED_PERCENTAGE = 15

    @allure.title("Prepare Test Data")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_prepare_test_data(self):
        with allure.step("Step 1: Prepare a fresh $20 product through the API"):
            client = ApiClient()
            category = client.EXISTING_MSA_CATEGORY
            channels = client.get_channels()
            TestPercentageDiscountOver100.product = client.create_product(
                category["id"], channels, is_msa_compliant=True, price=20.00, msa_category_code=category["code"]
            )
            logger.info(f"Generated product: {self.product['name']} (upc={self.product['upc']}, price=${self.product['price']})")

    @allure.title("Start New Sale and Add Product")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_start_new_sale_and_add_product(self):
        with allure.step("Step 2: Start a new sale and add the product"):
            TestPercentageDiscountOver100.sale_order = self.dashboard.start_new_sale()
            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            self.sale_order.add_product_by_upc(self.product["upc"], dob=dob)
            TestPercentageDiscountOver100.sub_total = self.sale_order.get_sub_total()
            assert self.sub_total == self.product["price"], (
                f"Cart Sub Total (${self.sub_total}) does not match the product's price (${self.product['price']})"
            )

    @allure.title("Type a 3-Digit Percentage and Verify It Is Capped, Not Rejected")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_03_percentage_input_is_capped_not_rejected(self):
        with allure.step(f"Step 3: Type '{self.TYPED_PERCENTAGE}' into the Discount (%) pad and confirm"):
            discount_page = self.sale_order.open_additional_discount()
            discount_page.enter_percentage(self.TYPED_PERCENTAGE)

            assert discount_page.is_confirm_enabled(), (
                "Confirm should remain enabled - the pad caps input at 2 digits, so this never becomes an invalid >100% value"
            )
            discount_page.confirm()

            expected_total = round(self.sub_total * (1 - self.EXPECTED_APPLIED_PERCENTAGE / 100), 2)
            actual_total = self.sale_order.get_grand_total()
            assert actual_total == expected_total, (
                f"Grand Total after typing '{self.TYPED_PERCENTAGE}' is ${actual_total}, expected ${expected_total} "
                f"(${self.sub_total} - {self.EXPECTED_APPLIED_PERCENTAGE}%, proving the 3rd digit was dropped not applied)"
            )
