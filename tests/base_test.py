import pytest
import yaml

from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


class BaseTest:
    """Base class for scenario tests that need to already be logged in and
    clocked in — the precondition for nearly every real POS flow.

    Mirrors khub-web-tests' class-scoped `setup` fixture: login (and here,
    clock-in) happens ONCE per test class via this autouse fixture, not once
    per test method, so scenario tests just write their flow against an
    already-authenticated `self.dashboard` / `self.driver`.

    CONVENTION: every new test class for a real POS flow (sale order, sale
    return, inventory, etc.) MUST inherit from BaseTest — this is the
    equivalent of khub-web-tests requiring `@pytest.mark.usefixtures("setup")`
    on every test class. The only intended exceptions are
    `tests/login/test_login.py` and `tests/shift/test_clock_in.py`, which
    test the login/clock-in precondition itself and would be redundant (or
    conflict with) having it pre-applied — the same deliberate-opt-out
    pattern khub-web-tests uses for its API-only DatabaseIsolation tests.
    """

    @pytest.fixture(autouse=True, scope="class")
    def _login_and_clock_in(self, request, driver):
        login_page = LoginPage(driver)
        creds = TEST_DATA["login"]["valid"]
        login_page.login(creds["username"], creds["password"])
        assert login_page.is_login_successful(), "Login precondition failed"

        dashboard = DashboardPage(driver)
        clockin_page = dashboard.open_time_clock()
        clockin_page.clock_in(TEST_DATA["shift"]["clock_in_pin"])
        assert dashboard.is_clocked_in(), "Clock-in precondition failed"

        # Assign on the class, not `self` — pytest creates a fresh test
        # instance per test method, but the class object is shared, so every
        # method's `self.driver` / `self.dashboard` resolves here via normal
        # attribute fallback.
        request.cls.driver = driver
        request.cls.dashboard = dashboard
