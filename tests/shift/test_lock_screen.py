import allure
import yaml

from tests.pos_base_setup import POSBaseSetup
from utilities.logger import get_logger

logger = get_logger(__name__)

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


@allure.feature("Shift")
@allure.story("Lock Screen and Unlock")
class TestLockScreen(POSBaseSetup):
    """
    Flow: Lock Screen from the dashboard -> verify the currently active
    staff member's name is shown on the lock modal -> enter a wrong PIN and
    verify it's rejected (not silently accepted, no lockout observed) ->
    clear and enter the correct PIN -> verify the dashboard resumes exactly
    as it was.
    """

    lock_page = None

    @allure.title("Open Lock Screen and Verify Staff Name")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_open_lock_screen(self):
        with allure.step("Step 1: Open Lock Screen and verify the active staff member is shown"):
            switch_user = TEST_DATA["shift"]["switch_user"]
            TestLockScreen.lock_page = self.dashboard.open_lock_screen()
            assert self.lock_page.is_shown(), "Screen Locked modal did not appear"
            assert self.lock_page.is_staff_shown(switch_user), f"Staff name '{switch_user}' was not shown on the lock screen"

    @allure.title("Enter a Wrong PIN and Verify It Is Rejected")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_wrong_pin_rejected(self):
        with allure.step("Step 2: Enter an incorrect PIN and verify the screen stays locked"):
            self.lock_page.enter_pin("0000")
            self.lock_page.tap_unlock()
            assert self.lock_page.is_incorrect_pin_error_shown(), "Expected 'Incorrect PIN. Please try again.' error did not appear"
            assert self.lock_page.is_shown(), "Screen should still be locked after a wrong PIN"

    @allure.title("Enter the Correct PIN and Unlock")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_03_correct_pin_unlocks(self):
        with allure.step("Step 3: Clear the wrong PIN, enter the correct one, and verify the dashboard resumes"):
            pin = TEST_DATA["shift"]["clock_in_pin"]
            self.lock_page.clear_pin()
            self.lock_page.enter_pin(pin)
            self.lock_page.tap_unlock()
            assert self.dashboard.is_loaded(), "Dashboard did not resume after entering the correct PIN"
