import allure
import yaml

from tests.pos_base_setup import POSBaseSetup
from utilities.api_client import ApiClient
from utilities.logger import get_logger

logger = get_logger(__name__)

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


@allure.feature("Sale Order")
@allure.story("Park Order")
class TestParkOrder(POSBaseSetup):
    """
    Flow: Start New Sale -> add a product -> Park Order -> verify the
    confirmation dialog's own summary (Customer / Total Items / Total
    Amount) matches the cart before confirming -> confirm -> verify the
    success toast -> verify the cart resets to empty (Guest Customer,
    $0.00) ready for the next sale.

    Resuming a parked order is NOT covered here - confirmed live 2026-10-19
    that the screen reached after parking returns a page_source with zero
    elements despite being visibly populated, not yet root-caused. See
    ParkOrderLocators' docstring.
    """

    product = None
    sale_order = None
    park_page = None

    @allure.title("Prepare Test Data")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_prepare_test_data(self):
        with allure.step("Step 1: Prepare a fresh product through the API"):
            client = ApiClient()
            category = client.EXISTING_MSA_CATEGORY
            channels = client.get_channels()
            TestParkOrder.product = client.create_product(
                category["id"], channels, is_msa_compliant=True, price=35.00, msa_category_code=category["code"]
            )
            logger.info(f"Generated product: {self.product['name']} (upc={self.product['upc']}, price=${self.product['price']})")

    @allure.title("Start New Sale and Add Product")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_start_new_sale_and_add_product(self):
        with allure.step("Step 2: Start a new sale and add the product"):
            TestParkOrder.sale_order = self.dashboard.start_new_sale()
            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            self.sale_order.add_product_by_upc(self.product["upc"], dob=dob)
            assert self.sale_order.get_total_quantity() == 1, "Cart quantity is not 1 after adding the product"

    @allure.title("Open Park Order and Verify Summary")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_03_open_park_order_and_verify_summary(self):
        with allure.step("Step 3: Open Park Order and verify its summary matches the cart"):
            expected_total = self.sale_order.get_grand_total()
            TestParkOrder.park_page = self.sale_order.open_park_order()
            assert self.park_page.is_shown(), "Park Order confirmation dialog did not open"

            assert self.park_page.get_customer() == "Guest Customer", (
                f"Park dialog customer is '{self.park_page.get_customer()}', expected 'Guest Customer'"
            )
            assert self.park_page.get_total_items() == 1, "Park dialog Total Items is not 1"
            assert self.park_page.get_total_amount() == expected_total, (
                f"Park dialog Total Amount (${self.park_page.get_total_amount()}) does not match "
                f"the cart's own Grand Total (${expected_total})"
            )

    @allure.title("Confirm Park Order and Verify Cart Resets")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_04_confirm_park_and_verify_reset(self):
        with allure.step("Step 4: Confirm Park Order, verify the success toast, and verify the cart resets"):
            self.park_page.confirm()
            assert self.park_page.is_success_toast_shown(), "Expected 'Order parked successfully' toast did not appear"

            assert self.sale_order.is_guest_customer(), "Cart did not reset to Guest Customer after parking"
            assert self.sale_order.get_total_quantity() == 0, "Cart quantity is not 0 after parking the order"
            assert self.sale_order.get_grand_total() == 0.0, "Cart Grand Total is not $0.00 after parking the order"
