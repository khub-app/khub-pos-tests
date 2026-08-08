from locators.sale_return_locators import SaleReturnScreenLocators
from pages.base_page import BasePage
from pages.return_payment_page import ReturnPaymentPage
from utilities.logger import get_logger

logger = get_logger(__name__)


class SaleReturnPage(BasePage):
    def auto_fill(self):
        logger.info("Tapping Auto Fill to populate return quantities")
        self.click(SaleReturnScreenLocators.AUTO_FILL_LINK)
        return self

    def submit_return(self) -> ReturnPaymentPage:
        logger.info("Tapping Return")
        self.click(SaleReturnScreenLocators.RETURN_BUTTON)
        return ReturnPaymentPage(self.driver)
