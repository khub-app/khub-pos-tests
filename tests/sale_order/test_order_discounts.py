import allure
import yaml

from tests.pos_base_setup import POSBaseSetup
from utilities.api_client import ApiClient
from utilities.logger import get_logger

logger = get_logger(__name__)

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


@allure.feature("Sale Order")
@allure.story("Additional Discount — Fixed ($) mode")
class TestOrderFixedDiscount(POSBaseSetup):
    """
    The existing Create Sale Order test only exercises the Additional
    Discount modal's default Percentage (%) mode. This exercises its other
    mode, Fixed ($) - confirmed live 2026-10-19 via the mode dropdown - and
    verifies the exact dollar math (not just "total went down"), the same
    way a percentage discount really should be checked too.
    """

    product = None
    sale_order = None
    sub_total = None
    DISCOUNT_AMOUNT = 5.00

    @allure.title("Prepare Test Data")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_prepare_test_data(self):
        with allure.step("Step 1: Prepare a fresh product through the API"):
            client = ApiClient()
            category = client.EXISTING_MSA_CATEGORY
            channels = client.get_channels()
            TestOrderFixedDiscount.product = client.create_product(
                category["id"], channels, is_msa_compliant=True, price=30.00, msa_category_code=category["code"]
            )
            logger.info(f"Generated product: {self.product['name']} (upc={self.product['upc']}, price=${self.product['price']})")

    @allure.title("Start New Sale and Add Product")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_start_new_sale_and_add_product(self):
        with allure.step("Step 2: Start a new sale and add the product"):
            TestOrderFixedDiscount.sale_order = self.dashboard.start_new_sale()
            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            self.sale_order.add_product_by_upc(self.product["upc"], dob=dob)
            TestOrderFixedDiscount.sub_total = self.sale_order.get_sub_total()
            assert self.sub_total == self.product["price"], (
                f"Cart Sub Total (${self.sub_total}) does not match the product's price (${self.product['price']})"
            )

    @allure.title("Apply a Fixed ($) Discount and Verify Exact Math")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_03_apply_fixed_discount(self):
        with allure.step("Step 3: Switch the discount modal to Fixed ($), apply a $5 discount, and verify the exact total"):
            discount_page = self.sale_order.open_additional_discount()
            discount_page.apply_fixed_discount(f"{self.DISCOUNT_AMOUNT:.0f}")

            grand_total_after_discount = self.sale_order.get_grand_total()
            expected_total = self.sub_total - self.DISCOUNT_AMOUNT
            assert grand_total_after_discount == expected_total, (
                f"Grand Total after a ${self.DISCOUNT_AMOUNT:.2f} fixed discount is ${grand_total_after_discount}, "
                f"expected ${expected_total} (sub_total ${self.sub_total} - discount ${self.DISCOUNT_AMOUNT:.2f})"
            )
