from locators.sale_order_locators import ParkOrderLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class ParkOrderPage(BasePage):
    """The "Park Order" confirmation dialog - see ParkOrderLocators for what's
    been confirmed live and what's still unverified (resuming a parked order)."""

    def is_shown(self, timeout: int = 15) -> bool:
        return self.is_displayed(ParkOrderLocators.CONFIRM_DIALOG_TITLE, timeout)

    def get_customer(self) -> str:
        return self.find(ParkOrderLocators.CUSTOMER_VALUE).text

    def get_total_items(self) -> int:
        return int(self.find(ParkOrderLocators.TOTAL_ITEMS_VALUE).text)

    def get_total_amount(self) -> float:
        from utilities.currency import parse_currency

        return parse_currency(self.find(ParkOrderLocators.TOTAL_AMOUNT_VALUE).text)

    def confirm(self):
        logger.info("Confirming Park Order")
        self.click(ParkOrderLocators.CONFIRM_BUTTON)
        return self

    def is_success_toast_shown(self, timeout: int = 10) -> bool:
        return self.is_displayed(ParkOrderLocators.SUCCESS_TOAST, timeout)
