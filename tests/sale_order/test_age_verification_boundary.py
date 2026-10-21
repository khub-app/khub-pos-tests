import datetime
import time

import allure

from pages.age_verification_page import AgeVerificationPage
from tests.pos_base_setup import POSBaseSetup
from utilities.api_client import ApiClient
from utilities.logger import get_logger

logger = get_logger(__name__)


@allure.feature("Sale Order")
@allure.story("Age Verification Boundary (18+)")
class TestAgeVerificationBoundary(POSBaseSetup):
    """
    The POS app's Age Verification screen enforces an 18+ floor - confirmed
    live 2026-10-20 and confirmed with the product/business team that this
    is the app's actual intended limitation (not a bug to work around).
    `ApiClient.create_product(is_msa_compliant=True)` sets `age_threshold:
    18` to match.

    This exercises the real boundary: a customer who turns 18 tomorrow
    (currently 17) must be blocked, and a customer who is exactly 18 today
    must be allowed through - both DOBs computed relative to today so the
    test doesn't go stale as real time passes.
    """

    product = None
    sale_order = None
    seventeen_year_old_dob = None
    eighteen_year_old_dob = None

    @allure.title("Prepare Test Data")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_prepare_test_data(self):
        with allure.step("Step 1: Prepare a fresh age-restricted product through the API"):
            client = ApiClient()
            category = client.EXISTING_MSA_CATEGORY
            channels = client.get_channels()
            TestAgeVerificationBoundary.product = client.create_product(
                category["id"], channels, is_msa_compliant=True, price=10.00, msa_category_code=category["code"]
            )
            logger.info(f"Generated product: {self.product['name']} (upc={self.product['upc']}, price=${self.product['price']})")

            today = datetime.date.today()
            # Turns 18 TOMORROW, i.e. currently 17 - must be blocked.
            TestAgeVerificationBoundary.seventeen_year_old_dob = today.replace(year=today.year - 18) + datetime.timedelta(days=1)
            # Turned 18 exactly today - must be allowed.
            TestAgeVerificationBoundary.eighteen_year_old_dob = today.replace(year=today.year - 18)
            logger.info(f"17-year-old DOB: {self.seventeen_year_old_dob}, 18-year-old DOB: {self.eighteen_year_old_dob}")

    @allure.title("A 17-Year-Old Is Blocked")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_seventeen_year_old_blocked(self):
        with allure.step("Step 2: Start a new sale, search the product, and enter a DOB for someone currently 17"):
            TestAgeVerificationBoundary.sale_order = self.dashboard.start_new_sale()
            self.sale_order.search_product(self.product["upc"])
            time.sleep(3)
            self.sale_order.tap_first_result()
            time.sleep(2)

            age_page = AgeVerificationPage(self.driver)
            assert age_page.is_shown(), "Age Verification Required modal did not appear"

            dob = self.seventeen_year_old_dob
            age_page.enter_dob(f"{dob.month:02d}", f"{dob.day:02d}", str(dob.year))
            age_page.check_age()

            assert not age_page.is_verified(), "A 17-year-old was shown as 'Verified' - the 18+ floor is not being enforced"
            assert age_page.is_blocked_for_age(), (
                "Expected the 'Below required age' blocked state for a 17-year-old - the 18+ floor is not being enforced"
            )

            # Dismiss the blocked modal (no separate close/cancel exists)
            # so the next test can search and reopen verification cleanly.
            age_page.remove_restricted_items()

    @allure.title("An 18-Year-Old Is Allowed and the Product Is Added")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_03_eighteen_year_old_allowed(self):
        with allure.step("Step 3: Search the product again and enter a DOB for someone exactly 18 today"):
            self.sale_order.search_product(self.product["upc"])
            time.sleep(3)
            self.sale_order.tap_first_result()
            time.sleep(2)

            age_page = AgeVerificationPage(self.driver)
            assert age_page.is_shown(), "Age Verification Required modal did not appear"

            dob = self.eighteen_year_old_dob
            age_page.enter_dob(f"{dob.month:02d}", f"{dob.day:02d}", str(dob.year))
            age_page.check_age()

            assert age_page.is_verified(), "An 18-year-old was not shown as 'Verified'"
            assert age_page.is_confirm_and_proceed_enabled(), "Confirm & Proceed was disabled for an 18-year-old"

            age_page.confirm_and_proceed()
            assert self.sale_order.get_total_quantity() == 1, "Product was not added to the cart for an 18-year-old"
