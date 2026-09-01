from locators.sales_history_locators import VoidPaymentLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class VoidPaymentPage(BasePage):
    """See locators.sales_history_locators.VoidPaymentLocators for the
    known Server Error issue this flow currently hits."""

    def is_shown(self, timeout: int = 15) -> bool:
        return self.is_displayed(VoidPaymentLocators.CONFIRM_TITLE, timeout)

    def confirm_void(self):
        logger.info("Confirming Void Payment")
        self.click(VoidPaymentLocators.VOID_BUTTON)
        return self

    def is_server_error_shown(self, timeout: int = 10) -> bool:
        return self.is_displayed(VoidPaymentLocators.SERVER_ERROR_TITLE, timeout)

    def dismiss_server_error(self):
        logger.info("Dismissing Server Error dialog")
        self.click(VoidPaymentLocators.SERVER_ERROR_OK_BUTTON)
        return self
