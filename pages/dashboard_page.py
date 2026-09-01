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

    def is_admin_user(self, name: str, timeout: int = 15) -> bool:
        return self.is_displayed(DashboardLocators.admin_status_badge(name), timeout)

    def is_start_new_sale_enabled(self, timeout: int = 15) -> bool:
        return self.is_enabled(DashboardLocators.START_NEW_SALE, timeout)

    def is_product_enabled(self, timeout: int = 15) -> bool:
        return self.is_enabled(DashboardLocators.PRODUCT_BUTTON, timeout)

    def is_shift_open(self, timeout: int = 15) -> bool:
        return self.is_displayed(DashboardLocators.SHIFT_OPEN_MARKER, timeout)
