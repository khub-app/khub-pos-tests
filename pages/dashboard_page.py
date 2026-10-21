from locators.clockin_locators import ClockInLocators
from locators.dashboard_locators import DashboardLocators
from pages.base_page import BasePage
from pages.clockin_page import ClockInPage
from pages.sale_order_page import SaleOrderPage
from pages.sales_history_page import SalesHistoryPage
from pages.switch_user_page import SwitchUserPage
from utilities.logger import get_logger

logger = get_logger(__name__)


class DashboardPage(BasePage):
    def is_loaded(self, timeout: int = 45) -> bool:
        # Bumped from 15s (then 30s - still not enough, confirmed live):
        # the very first dashboard load after a fresh reset_app_data()
        # cold-launches the RN bundle from scratch and can take well over
        # 30s, though later tests in the same suite run (warm app) render
        # in ~5-10s - not a locator regression, the same START_NEW_SALE
        # check just needs enough headroom for the worst case.
        return self.is_displayed(DashboardLocators.START_NEW_SALE, timeout)

    def open_time_clock(self) -> ClockInPage:
        # The app auto-opens this modal right after login when the cashier
        # isn't clocked in yet, in which case the Time Clock button itself is
        # covered by the modal and un-clickable — nothing to tap.
        if self.is_displayed(ClockInLocators.MODAL_TITLE, timeout=3):
            logger.info("Clock-in modal already open (auto-shown after login)")
            return ClockInPage(self.driver)
        logger.info("Opening Time Clock")
        self.click(DashboardLocators.TIME_CLOCK_BUTTON)
        return ClockInPage(self.driver)

    def is_clocked_in(self, timeout: int = 15) -> bool:
        return self.is_displayed(DashboardLocators.CLOCKED_IN_MARKER, timeout)

    def start_new_sale(self) -> SaleOrderPage:
        logger.info("Tapping Start New Sale")
        self.click(DashboardLocators.START_NEW_SALE)
        return SaleOrderPage(self.driver)

    def open_sales_history(self) -> SalesHistoryPage:
        logger.info("Opening Sales History")
        self.click(DashboardLocators.SALES_HISTORY_BUTTON)
        return SalesHistoryPage(self.driver)

    def open_switch_user(self) -> SwitchUserPage:
        logger.info("Opening Switch user")
        self.click(DashboardLocators.SWITCH_USER_BUTTON)
        return SwitchUserPage(self.driver)

    def open_hold_resume(self):
        from pages.parked_orders_page import ParkedOrdersPage

        logger.info("Opening Hold / Resume")
        self.click(DashboardLocators.HOLD_RESUME_BUTTON)
        return ParkedOrdersPage(self.driver)

    def open_lock_screen(self):
        from pages.lock_screen_page import LockScreenPage

        logger.info("Opening Lock Screen")
        self.click(DashboardLocators.LOCK_SCREEN_BUTTON)
        return LockScreenPage(self.driver)

    def open_cash_in(self):
        from pages.cash_movement_page import CashMovementPage

        logger.info("Opening Cash In")
        self.click(DashboardLocators.CASH_IN_BUTTON)
        return CashMovementPage(self.driver)

    def open_cash_out(self):
        from pages.cash_movement_page import CashMovementPage

        logger.info("Opening Cash Out")
        self.click(DashboardLocators.CASH_OUT_BUTTON)
        return CashMovementPage(self.driver)

    def is_admin_user(self, name: str, timeout: int = 15) -> bool:
        return self.is_displayed(DashboardLocators.admin_status_badge(name), timeout)

    def is_start_new_sale_enabled(self, timeout: int = 15) -> bool:
        return self.is_enabled(DashboardLocators.START_NEW_SALE, timeout)

    def is_product_enabled(self, timeout: int = 15) -> bool:
        return self.is_enabled(DashboardLocators.PRODUCT_BUTTON, timeout)

    def is_shift_open(self, timeout: int = 15) -> bool:
        return self.is_displayed(DashboardLocators.SHIFT_OPEN_MARKER, timeout)

    def start_shift_if_needed(self, timeout: int = 20) -> bool:
        """Starts a shift (Opening Cash left at $0.00) unless one is already
        open. A brand-new employee always starts with "SHIFT: Closed", and
        Start New Sale silently fails to work until a shift is open - see
        shift_locators.py. Returns whether a shift was actually started.

        Confirmed live 2026-10-19: right after Switch user, the "SHIFT: Open"
        header badge can take well over 5s to repaint (same transient RN
        rendering-gap class as expand_totals_drawer's retry and the Park
        Order confirm screen). A too-short check here falsely concludes the
        shift is closed, then hangs ~60s hunting for a "Start Shift" trigger
        tile that doesn't exist because the shift was already open -
        20s gives the badge enough headroom to settle."""
        from pages.shift_page import ShiftPage

        if self.is_shift_open(timeout=timeout):
            logger.info("Shift already open")
            return False
        logger.info("Shift is closed - starting one")
        ShiftPage(self.driver).start_shift()
        assert self.is_shift_open(), "Shift still not open after Start Shift"
        return True
