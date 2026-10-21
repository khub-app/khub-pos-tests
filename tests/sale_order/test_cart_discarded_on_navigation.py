import allure
import yaml

from tests.pos_base_setup import POSBaseSetup
from utilities.api_client import ApiClient
from utilities.logger import get_logger

logger = get_logger(__name__)

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


@allure.feature("Sale Order")
@allure.story("Unsaved Cart Discarded on Navigation")
class TestCartDiscardedOnNavigation(POSBaseSetup):
    """
    A cashier can add a product to the cart and then navigate away via
    "Go to Menu" without explicitly Parking the order first - "Switch
    user" itself is only reachable from the dashboard, not the cart
    screen, so any user-switch mid-sale necessarily goes through this same
    "Go to Menu" path first.

    Confirmed live 2026-10-20: doing so silently DISCARDS the in-progress
    cart rather than preserving it - returning to Start New Sale shows a
    fresh empty cart (Guest Customer, qty 0, $0.00), not the product that
    was still sitting there. This is presumably intended behavior (Park
    Order exists specifically to preserve a cart across navigation), but
    it's worth a regression guard: if this ever silently started
    retaining/resurrecting stale cart data instead, that would be a worse
    bug (e.g. charging a later customer for an earlier abandoned cart's
    items).
    """

    product = None
    sale_order = None

    @allure.title("Prepare Test Data")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_prepare_test_data(self):
        with allure.step("Step 1: Prepare a fresh product through the API"):
            client = ApiClient()
            category = client.EXISTING_MSA_CATEGORY
            channels = client.get_channels()
            TestCartDiscardedOnNavigation.product = client.create_product(
                category["id"], channels, is_msa_compliant=True, price=10.00, msa_category_code=category["code"]
            )
            logger.info(f"Generated product: {self.product['name']} (upc={self.product['upc']}, price=${self.product['price']})")

    @allure.title("Add a Product Without Parking, Navigate Away, and Verify It Is Lost")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_unsaved_cart_is_discarded(self):
        with allure.step("Step 2: Add a product, tap Go to Menu without parking, then return to Start New Sale"):
            TestCartDiscardedOnNavigation.sale_order = self.dashboard.start_new_sale()
            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            self.sale_order.add_product_by_upc(self.product["upc"], dob=dob)
            assert self.sale_order.get_total_quantity() == 1, "Cart quantity is not 1 after adding the product"

            dashboard = self.sale_order.go_to_menu()
            assert dashboard.is_loaded(), "Dashboard did not reload after Go to Menu"

            TestCartDiscardedOnNavigation.sale_order = dashboard.start_new_sale()
            assert self.sale_order.is_cart_empty(), "Cart was not empty after returning to Start New Sale"
            assert self.sale_order.get_total_quantity() == 0, "Cart quantity is not 0 - the unsaved cart was not discarded"
            assert self.sale_order.get_grand_total() == 0.0, "Grand Total is not $0.00 - the unsaved cart was not discarded"
