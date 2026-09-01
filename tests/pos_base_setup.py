import pytest
import yaml

from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


class POSBaseSetup:
    """Reusable 3-stage precondition for POS scenario tests that need a
    specific active user (Split Payment, etc.), distinct from BaseTest's
    login+generic-clock-in precondition:

    1. Log in.
    2. Clock in the configured shift-owner user, unless already clocked in.
    3. Switch the active session to the configured automation user.

    Mirrors BaseTest's structure (class-scoped autouse fixture, `self.driver`
    / `self.dashboard` available to every test method) - inherit from this
    instead of BaseTest whenever a scenario needs the Automation user active
    rather than whichever user BaseTest's generic clock-in leaves active.
    """

    @pytest.fixture(autouse=True, scope="class")
    def _pos_base_setup(self, request, driver):
        creds = TEST_DATA["login"]["valid"]
        clock_in_user = TEST_DATA["shift"]["clock_in_user"]
        switch_user = TEST_DATA["shift"]["switch_user"]
        pin = TEST_DATA["shift"]["clock_in_pin"]

        # Stage 1: log in
        login_page = LoginPage(driver)
        login_page.login(creds["username"], creds["password"])
        assert login_page.is_login_successful(), "Login precondition failed"

        # Stage 2: clock in clock_in_user (skipped if already clocked in)
        dashboard = DashboardPage(driver)
        clockin_page = dashboard.open_time_clock()
        clockin_page.clock_in_user_if_needed(clock_in_user, pin)

        # Stage 3: switch the active session to switch_user
        switch_user_page = dashboard.open_switch_user()
        switch_user_page.switch_to(switch_user, pin)
        assert dashboard.is_loaded(), "Dashboard did not load after switching users"

        request.cls.driver = driver
        request.cls.dashboard = dashboard
