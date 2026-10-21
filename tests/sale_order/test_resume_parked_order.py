import allure
import yaml

from tests.pos_base_setup import POSBaseSetup
from utilities.api_client import ApiClient
from utilities.logger import get_logger

logger = get_logger(__name__)

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


@allure.feature("Sale Order")
@allure.story("Resume Parked Order")
class TestResumeParkedOrder(POSBaseSetup):
    """
    Flow: Start New Sale -> add a product -> Park Order -> go to the
    dashboard -> open Hold / Resume -> select the most recently parked
    order -> Resume Order -> verify the success toast names that same
    order -> verify the cart repopulates with the exact product/qty/price
    that was parked.
    """

    product = None
    sale_order = None
    park_page = None
    parked_order_number = None

    @allure.title("Prepare Test Data")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_prepare_test_data(self):
        with allure.step("Step 1: Prepare a fresh product through the API"):
            client = ApiClient()
            category = client.EXISTING_MSA_CATEGORY
            channels = client.get_channels()
            TestResumeParkedOrder.product = client.create_product(
                category["id"], channels, is_msa_compliant=True, price=22.00, msa_category_code=category["code"]
            )
            logger.info(f"Generated product: {self.product['name']} (upc={self.product['upc']}, price=${self.product['price']})")

    @allure.title("Start New Sale, Add Product, and Park It")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_start_sale_add_product_and_park(self):
        with allure.step("Step 2: Start a new sale, add the product, and park the order"):
            TestResumeParkedOrder.sale_order = self.dashboard.start_new_sale()
            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            self.sale_order.add_product_by_upc(self.product["upc"], dob=dob)
            assert self.sale_order.get_total_quantity() == 1, "Cart quantity is not 1 after adding the product"

            TestResumeParkedOrder.park_page = self.sale_order.open_park_order()
            assert self.park_page.is_shown(), "Park Order confirmation dialog did not open"
            self.park_page.confirm()
            assert self.park_page.is_success_toast_shown(), "Expected 'Order parked successfully' toast did not appear"

    @allure.title("Navigate to Hold / Resume, Select, and Resume the Parked Order")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_03_navigate_select_and_resume(self):
        with allure.step("Step 3: Go to the dashboard, open Hold / Resume, select and resume the most recent parked order"):
            dashboard = self.sale_order.go_to_menu()
            parked_orders = dashboard.open_hold_resume()
            assert parked_orders.is_shown(), "Parked Orders screen did not open"

            TestResumeParkedOrder.parked_order_number = parked_orders.get_top_row_order_number()
            logger.info(f"Most recently parked order: {self.parked_order_number}")
            parked_orders.select_top_row()

            TestResumeParkedOrder.sale_order = parked_orders.resume_selected_order()

            # The resume toast is transient - assert on it immediately rather
            # than in a later test method, where it may have already faded.
            toast_text = parked_orders.get_resume_toast_text()
            assert self.parked_order_number in toast_text, (
                f"Resume toast '{toast_text}' does not mention the resumed order '{self.parked_order_number}'"
            )
            assert "1 product(s)" in toast_text, f"Resume toast '{toast_text}' does not report 1 product"

    @allure.title("Verify Cart Contents After Resume")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_04_verify_cart_after_resume(self):
        with allure.step("Step 4: Verify the resumed cart matches what was parked"):
            assert self.sale_order.get_total_quantity() == 1, "Resumed cart quantity is not 1"
            assert self.sale_order.get_sub_total() == self.product["price"], (
                f"Resumed cart Sub Total (${self.sale_order.get_sub_total()}) does not match "
                f"the parked product's price (${self.product['price']})"
            )
            assert self.sale_order.get_grand_total() == self.product["price"], (
                f"Resumed cart Grand Total (${self.sale_order.get_grand_total()}) does not match "
                f"the parked product's price (${self.product['price']})"
            )
