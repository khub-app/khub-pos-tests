import allure
import yaml

from tests.pos_base_setup import POSBaseSetup
from utilities.api_client import ApiClient
from utilities.logger import get_logger

logger = get_logger(__name__)

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


@allure.feature("Sale Order")
@allure.story("Multi-Quantity Line Math")
class TestMultiQuantityLineMath(POSBaseSetup):
    """
    The existing Create Sale Order test only ever adds qty 1 of each of two
    different products - it never exercises the quantity stepper on a
    single line. This increments/decrements one product's quantity via the
    cart row's +/- controls and verifies the line (and cart) total scales
    exactly with unit price x qty each step, not just "it changed".
    """

    product = None
    sale_order = None
    UNIT_PRICE = 10.00

    @allure.title("Prepare Test Data")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_prepare_test_data(self):
        with allure.step("Step 1: Prepare a fresh product through the API"):
            client = ApiClient()
            category = client.EXISTING_MSA_CATEGORY
            channels = client.get_channels()
            TestMultiQuantityLineMath.product = client.create_product(
                category["id"], channels, is_msa_compliant=True, price=self.UNIT_PRICE, msa_category_code=category["code"]
            )
            logger.info(f"Generated product: {self.product['name']} (upc={self.product['upc']}, price=${self.product['price']})")

    @allure.title("Add Product and Increment Quantity Twice")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_add_and_increment(self):
        with allure.step("Step 2: Add the product (qty 1), then tap '+' twice and verify math each step"):
            TestMultiQuantityLineMath.sale_order = self.dashboard.start_new_sale()
            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            self.sale_order.add_product_by_upc(self.product["upc"], dob=dob)
            assert self.sale_order.get_total_quantity() == 1
            assert self.sale_order.get_sub_total() == self.UNIT_PRICE * 1

            self.sale_order.tap_quantity_increment()
            assert self.sale_order.get_total_quantity() == 2, "Quantity did not increment to 2"
            assert self.sale_order.get_sub_total() == self.UNIT_PRICE * 2, "Sub Total did not scale to 2x unit price"

            self.sale_order.tap_quantity_increment()
            assert self.sale_order.get_total_quantity() == 3, "Quantity did not increment to 3"
            assert self.sale_order.get_sub_total() == self.UNIT_PRICE * 3, "Sub Total did not scale to 3x unit price"

    @allure.title("Decrement Quantity and Verify Math")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_03_decrement(self):
        with allure.step("Step 3: Tap '-' once and verify the total scales back down"):
            self.sale_order.tap_quantity_decrement()
            assert self.sale_order.get_total_quantity() == 2, "Quantity did not decrement to 2"
            assert self.sale_order.get_sub_total() == self.UNIT_PRICE * 2, "Sub Total did not scale back to 2x unit price"
            assert self.sale_order.get_grand_total() == self.sale_order.get_sub_total(), (
                "Grand Total should equal Sub Total with no discount/tax applied"
            )


@allure.feature("Sale Order")
@allure.story("Remove Product and Empty Cart")
class TestRemoveProductAndEmptyCart(POSBaseSetup):
    """
    Covers the two distinct ways a cashier clears cart contents, confirmed
    live 2026-10-20 to behave differently:
    - Remove product (single line): fires immediately, no confirmation.
    - Empty Cart (all lines): confirms first ("Are you sure you want to
      remove all items?" / CANCEL / EMPTY).
    """

    product = None
    sale_order = None
    UNIT_PRICE = 10.00

    @allure.title("Prepare Test Data")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_prepare_test_data(self):
        with allure.step("Step 1: Prepare a fresh product through the API"):
            client = ApiClient()
            category = client.EXISTING_MSA_CATEGORY
            channels = client.get_channels()
            TestRemoveProductAndEmptyCart.product = client.create_product(
                category["id"], channels, is_msa_compliant=True, price=self.UNIT_PRICE, msa_category_code=category["code"]
            )
            logger.info(f"Generated product: {self.product['name']} (upc={self.product['upc']}, price=${self.product['price']})")

    @allure.title("Add Product and Remove It (No Confirmation)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_add_and_remove_product(self):
        with allure.step("Step 2: Add the product, then remove it - verify the cart is immediately empty"):
            TestRemoveProductAndEmptyCart.sale_order = self.dashboard.start_new_sale()
            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            self.sale_order.add_product_by_upc(self.product["upc"], dob=dob)
            assert self.sale_order.get_sub_total() == self.UNIT_PRICE

            self.sale_order.remove_product()
            assert self.sale_order.is_cart_empty(), "Cart did not show the empty-products message after Remove product"
            assert self.sale_order.get_sub_total() == 0.0, "Sub Total is not $0.00 after removing the only product"

    @allure.title("Add Multiple Quantity and Empty Cart (Confirmation Required)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_03_empty_cart_with_confirmation(self):
        with allure.step("Step 3: Add the product, bump quantity to 2, then Empty Cart via its confirm dialog"):
            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            self.sale_order.add_product_by_upc(self.product["upc"], dob=dob)
            self.sale_order.tap_quantity_increment()
            assert self.sale_order.get_total_quantity() == 2
            assert self.sale_order.get_sub_total() == self.UNIT_PRICE * 2

            self.sale_order.empty_cart()
            assert self.sale_order.is_cart_empty(), "Cart did not show the empty-products message after Empty Cart"
            assert self.sale_order.get_total_quantity() == 0, "Total Quantity is not 0 after Empty Cart"
            assert self.sale_order.get_grand_total() == 0.0, "Grand Total is not $0.00 after Empty Cart"
            assert self.sale_order.is_guest_customer(), "Cart did not reset to Guest Customer after Empty Cart"


@allure.feature("Sale Order")
@allure.story("Checkout Blocked on an Empty Cart")
class TestZeroItemCheckoutBlocked(POSBaseSetup):
    """
    Confirmed live 2026-10-20: Cash and Card both report enabled="true"
    even with Total Products: 0 - the app does NOT grey these buttons out
    on an empty cart. Tapping Cash instead surfaces a native
    "Error / Please add products to cart first / OK" dialog rather than
    opening the Cash Payment modal. This verifies that safety net
    explicitly, since a disabled-button assumption would have been wrong.
    """

    sale_order = None

    @allure.title("Tap Cash on an Empty Cart and Verify It Is Blocked")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_cash_blocked_on_empty_cart(self):
        with allure.step("Step 1: Start a new sale with an empty cart and tap Cash"):
            TestZeroItemCheckoutBlocked.sale_order = self.dashboard.start_new_sale()
            assert self.sale_order.get_sub_total() == 0.0, "Cart should start empty"

            self.sale_order.tap_cash_on_empty_cart()
            assert self.sale_order.is_add_products_first_error_shown(), (
                "Expected 'Please add products to cart first' error did not appear when tapping Cash on an empty cart"
            )

    @allure.title("Dismiss the Error and Verify the Cart Is Still Usable")
    @allure.severity(allure.severity_level.NORMAL)
    def test_02_dismiss_and_cart_still_usable(self):
        with allure.step("Step 2: Dismiss the error and verify the cart recovered cleanly"):
            self.sale_order.dismiss_add_products_first_error()
            assert self.sale_order.get_sub_total() == 0.0, "Sub Total changed even though nothing was added"
            assert self.sale_order.is_guest_customer(), "Cart is not back to its normal Guest Customer state"
