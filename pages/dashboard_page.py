from locators.dashboard_locators import DashboardLocators
from pages.base_page import BasePage
from pages.clockin_page import ClockInPage
from pages.sale_order_page import SaleOrderPage
from pages.sales_history_page import SalesHistoryPage
from utilities.logger import get_logger

logger = get_logger(__name__)


class DashboardPage(BasePage):
    def is_loaded(self, timeout: int = 15) -> bool:
        return self.is_displayed(DashboardLocators.START_NEW_SALE, timeout)

    def open_time_clock(self) -> ClockInPage:
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
