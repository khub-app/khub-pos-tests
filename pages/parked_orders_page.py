from locators.parked_orders_locators import ParkedOrdersLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class ParkedOrdersPage(BasePage):
    def is_shown(self, timeout: int = 15) -> bool:
        return self.is_displayed(ParkedOrdersLocators.TITLE, timeout)

    def get_top_row_order_number(self) -> str:
        return self.find(ParkedOrdersLocators.TOP_ROW_ORDER_NUMBER).text

    def select_top_row(self):
        logger.info("Selecting the most recently parked order")
        self.click(ParkedOrdersLocators.TOP_ROW_ORDER_NUMBER)
        return self

    def resume_selected_order(self):
        from pages.sale_order_page import SaleOrderPage

        logger.info("Tapping Resume Order")
        self.click(ParkedOrdersLocators.RESUME_ORDER_BUTTON)
        return SaleOrderPage(self.driver)

    def get_resume_toast_text(self, timeout: int = 10) -> str:
        return self.find(ParkedOrdersLocators.RESUME_TOAST, timeout).text
