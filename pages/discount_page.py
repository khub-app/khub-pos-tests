from locators.sale_order_locators import DiscountLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class DiscountPage(BasePage):
    def enter_percentage(self, percent: str):
        logger.info(f"Entering discount percentage: {percent}")
        for digit in percent:
            self.click(DiscountLocators.digit(digit))
        return self

    def confirm(self):
        logger.info("Confirming discount")
        self.click(DiscountLocators.CONFIRM_BUTTON)
        return self

    def apply_percentage_discount(self, percent: str):
        self.enter_percentage(percent)
        self.confirm()
