import allure
import yaml

from tests.base_test import BaseTest
from utilities.currency import parse_currency

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


@allure.feature("Sale Order")
@allure.story("Create sale with MSA-restricted products")
class TestCreateSaleOrder(BaseTest):
    """
    Flow: Start New Sale -> add a tobacco/MSA product (triggers age
    verification: DOB, Check age, Confirm & Proceed) -> add a second
    tobacco product (age verification must NOT reappear, since the
    customer was already verified for this order) -> Additional Discount
    -> Cash payment for the exact amount due -> dismiss the receipt
    prompt -> back at the dashboard.

    Login + Clock In run once per class via BaseTest's autouse fixture.
    Each step below asserts on the app's actual state (cart quantity/totals,
    age-verification visibility) rather than just performing the tap and
    moving on, so a broken step shows up as a failed step in the Allure
    report instead of a silently-passing one.
    """

    def test_create_sale_with_two_tobacco_products(self):
        products = TEST_DATA["tobacco_products"]
        dob = tuple(products["age_verification_dob"])

        with allure.step("Step 1: Start a new sale"):
            sale_order = self.dashboard.start_new_sale()

        with allure.step("Step 2: Add first tobacco product — age verification must appear and be completed"):
            shown = sale_order.add_product_by_upc(products["product_1_upc"], dob=dob)
            assert shown, "Age verification did not appear for the first MSA/tobacco product"
            assert sale_order.get_total_quantity() == 1, "Cart quantity is not 1 after adding the first product"

        with allure.step("Step 3: Add second tobacco product — age verification must NOT reappear"):
            shown = sale_order.add_product_by_upc(products["product_2_upc"], dob=dob)
            assert not shown, "Age verification reappeared for the second product — should only prompt once per order"
            assert sale_order.get_total_quantity() == 2, "Cart quantity is not 2 after adding the second product"

        with allure.step("Step 4: Apply an additional discount and verify the total decreased"):
            sub_total_before_discount = sale_order.get_sub_total()
            discount_page = sale_order.open_additional_discount()
            discount_page.apply_percentage_discount(TEST_DATA.get("discount_percent", "10"))
            grand_total_after_discount = sale_order.get_grand_total()
            assert grand_total_after_discount < sub_total_before_discount, (
                f"Discount did not reduce the total: sub_total={sub_total_before_discount}, "
                f"grand_total_after_discount={grand_total_after_discount}"
            )

        with allure.step("Step 5: Pay the exact amount due in cash"):
            cash_page = sale_order.tap_cash()
            amount_due = cash_page.get_amount_due()
            assert amount_due, "Amount Due was empty — cart total did not compute"
            assert parse_currency(amount_due) > 0, f"Amount Due parsed to a non-positive value: {amount_due!r}"
            cash_page.pay_exact_amount_due()

        with allure.step("Step 6: Dismiss the receipt prompt"):
            cash_page.dismiss_receipt_prompt()

        with allure.step("Step 7: Navigate back to the Dashboard via Go to Menu (post-sale — NOT a product return)"):
            dashboard = sale_order.go_to_menu()
            assert dashboard.is_loaded(), "Dashboard did not reload after completing the sale"
