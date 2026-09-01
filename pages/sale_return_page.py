from locators.sale_return_locators import SaleReturnScreenLocators
from pages.base_page import BasePage
from pages.return_payment_page import ReturnPaymentPage
from utilities.currency import parse_currency
from utilities.logger import get_logger

logger = get_logger(__name__)


class SaleReturnPage(BasePage):
    def is_shown(self, order_no: str, timeout: int = 15) -> bool:
        return self.is_displayed(SaleReturnScreenLocators.modal_title(order_no), timeout)

    def get_total_quantity(self) -> int:
        return int(self.find(SaleReturnScreenLocators.TOTAL_QUANTITY_VALUE).text)

    def get_total_to_refund(self) -> float:
        return parse_currency(self.find(SaleReturnScreenLocators.TOTAL_TO_REFUND_VALUE).text)

    def is_return_button_enabled(self) -> bool:
        return self.is_enabled(SaleReturnScreenLocators.RETURN_BUTTON)

    def auto_fill(self):
        logger.info("Tapping Auto Fill to populate return quantities")
        self.click(SaleReturnScreenLocators.AUTO_FILL_LINK)
        return self

    def submit_return(self) -> ReturnPaymentPage:
        logger.info("Tapping Return")
        self.click(SaleReturnScreenLocators.RETURN_BUTTON)
        return ReturnPaymentPage(self.driver)
