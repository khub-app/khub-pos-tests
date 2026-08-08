from locators.sale_return_locators import ReturnPaymentMethodLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class ReturnPaymentPage(BasePage):
    def is_shown(self, timeout: int = 15) -> bool:
        return self.is_displayed(ReturnPaymentMethodLocators.MODAL_TITLE, timeout)

    def enter_return_reason(self, reason: str):
        logger.info(f"Entering return reason: {reason}")
        self.type_text(ReturnPaymentMethodLocators.RETURN_REASON_FIELD, reason)
        return self

    def complete_return(self):
        logger.info("Tapping Complete Return")
        self.click(ReturnPaymentMethodLocators.COMPLETE_RETURN_BUTTON)
        return self
