import allure
import yaml

from tests.pos_base_setup import POSBaseSetup
from utilities.api_client import ApiClient
from utilities.currency import parse_currency
from utilities.logger import get_logger

logger = get_logger(__name__)

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


@allure.feature("Sale Order")
@allure.story("Create sale with MSA-restricted products")
class TestCreateSaleOrder(POSBaseSetup):
    """
    Flow: Start New Sale -> add a tobacco/MSA product (triggers age
    verification: DOB, Check age, Confirm & Proceed) -> add a second
    tobacco product (age verification must NOT reappear, since the
    customer was already verified for this order) -> Additional Discount
    -> Cash payment for the exact amount due -> dismiss the receipt
    prompt -> back at the dashboard.

    Login + Clock In + Switch to Automation user run once per class via
    POSBaseSetup's autouse fixture. Split into one pytest test method per
    logical step (mirrors khub-web-tests' runner pattern) so each step
    gets its own Allure page with History/Retries tabs, instead of a flat
    allure.step() list inside one monolithic test. Steps share state via
    CLASS attributes, safe because the class object persists across every
    test method here even though pytest instantiates a fresh one per
    method. conftest.py's hooks skip a step if an earlier one in this same
    class failed, rather than running it against unknown app state.
    """

    product_1 = None
    product_2 = None
    sale_order = None
    sub_total_before_discount = None
    cash_page = None

    @allure.title("Prepare Two MSA Products")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_prepare_test_data(self):
        with allure.step("Step 1: Prepare two fresh MSA-restricted products through the API"):
            # The static UPCs previously hardcoded in test_data.yaml went
            # stale (this is a shared, live preprod catalog - confirmed live
            # the product search now returns "No products found" for them).
            # Creating fresh products per run, the same way Split Payment and
            # Sale Return already do, avoids that drift entirely.
            client = ApiClient()
            category = client.EXISTING_MSA_CATEGORY
            channels = client.get_channels()
            TestCreateSaleOrder.product_1 = client.create_product(
                category["id"], channels, is_msa_compliant=True, price=10.00, msa_category_code=category["code"]
            )
            TestCreateSaleOrder.product_2 = client.create_product(
                category["id"], channels, is_msa_compliant=True, price=15.00, msa_category_code=category["code"]
            )
            logger.info(f"Generated product 1: {self.product_1['name']} (upc={self.product_1['upc']}, price=${self.product_1['price']})")
            logger.info(f"Generated product 2: {self.product_2['name']} (upc={self.product_2['upc']}, price=${self.product_2['price']})")

    @allure.title("Start New Sale")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_start_new_sale(self):
        with allure.step("Step 2: Start a new sale"):
            TestCreateSaleOrder.sale_order = self.dashboard.start_new_sale()

    @allure.title("Add First Tobacco Product — Age Verification Required")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_03_add_first_product(self):
        with allure.step("Step 3: Add first tobacco product — age verification must appear and be completed"):
            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            shown = self.sale_order.add_product_by_upc(self.product_1["upc"], dob=dob)
            assert shown, "Age verification did not appear for the first MSA/tobacco product"
            assert self.sale_order.get_total_quantity() == 1, "Cart quantity is not 1 after adding the first product"

    @allure.title("Add Second Tobacco Product — Age Verification Must Not Reappear")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_04_add_second_product(self):
        with allure.step("Step 4: Add second tobacco product — age verification must NOT reappear"):
            dob = tuple(TEST_DATA["tobacco_products"]["age_verification_dob"])
            shown = self.sale_order.add_product_by_upc(self.product_2["upc"], dob=dob)
            assert not shown, "Age verification reappeared for the second product — should only prompt once per order"
            assert self.sale_order.get_total_quantity() == 2, "Cart quantity is not 2 after adding the second product"

    @allure.title("Apply Additional Discount")
    @allure.severity(allure.severity_level.NORMAL)
    def test_05_apply_discount(self):
        with allure.step("Step 5: Apply an additional discount and verify the total decreased"):
            TestCreateSaleOrder.sub_total_before_discount = self.sale_order.get_sub_total()
            discount_page = self.sale_order.open_additional_discount()
            discount_page.apply_percentage_discount(TEST_DATA.get("discount_percent", "10"))
            grand_total_after_discount = self.sale_order.get_grand_total()
            assert grand_total_after_discount < self.sub_total_before_discount, (
                f"Discount did not reduce the total: sub_total={self.sub_total_before_discount}, "
                f"grand_total_after_discount={grand_total_after_discount}"
            )

    @allure.title("Pay Exact Amount Due in Cash")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_06_pay_cash(self):
        with allure.step("Step 6: Pay the exact amount due in cash"):
            TestCreateSaleOrder.cash_page = self.sale_order.tap_cash()
            amount_due = self.cash_page.get_amount_due()
            assert amount_due, "Amount Due was empty — cart total did not compute"
            assert parse_currency(amount_due) > 0, f"Amount Due parsed to a non-positive value: {amount_due!r}"
            self.cash_page.pay_exact_amount_due()

    @allure.title("Dismiss Receipt Prompt")
    @allure.severity(allure.severity_level.NORMAL)
    def test_07_dismiss_receipt(self):
        with allure.step("Step 7: Dismiss the receipt prompt"):
            self.cash_page.dismiss_receipt_prompt()

    @allure.title("Return to Dashboard")
    @allure.severity(allure.severity_level.NORMAL)
    def test_08_return_to_dashboard(self):
        with allure.step("Step 8: Navigate back to the Dashboard via Go to Menu (post-sale — NOT a product return)"):
            dashboard = self.sale_order.go_to_menu()
            assert dashboard.is_loaded(), "Dashboard did not reload after completing the sale"
