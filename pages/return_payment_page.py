import re

from locators.sale_return_locators import ReturnPaymentMethodLocators
from pages.base_page import BasePage
from utilities.currency import parse_currency
from utilities.logger import get_logger

logger = get_logger(__name__)

RETURN_NUMBER_PATTERN = re.compile(r"RE-\d{6}-\d+")


class ReturnPaymentPage(BasePage):
    def is_shown(self, timeout: int = 15) -> bool:
        return self.is_displayed(ReturnPaymentMethodLocators.MODAL_TITLE, timeout)

    def get_return_total(self) -> float:
        return parse_currency(self.find(ReturnPaymentMethodLocators.RETURN_TOTAL_VALUE).text)

    def get_returnable_amount(self) -> float:
        return parse_currency(self.find(ReturnPaymentMethodLocators.RETURNABLE_AMOUNT_VALUE).text)

    def get_customer_name(self) -> str:
        return self.find(ReturnPaymentMethodLocators.CUSTOMER_VALUE).text

    def enter_return_reason(self, reason: str):
        logger.info(f"Entering return reason: {reason}")
        self.type_text(ReturnPaymentMethodLocators.RETURN_REASON_FIELD, reason)
        return self

    def complete_return(self):
        logger.info("Tapping Complete Return")
        self.click(ReturnPaymentMethodLocators.COMPLETE_RETURN_BUTTON)
        return self

    def get_return_number(self, timeout: int = 10) -> str | None:
        """Reads the "Return RE-XXXXXX-XXXXX created successfully" toast
        shown after Complete Return - returns None (rather than raising) if
        it isn't found, mirroring ReceiptCompletePage.get_order_number()'s
        no-raise contract so callers can fall back to other verification."""
        if not self.is_displayed(ReturnPaymentMethodLocators.SUCCESS_TOAST, timeout):
            return None
        text = self.find(ReturnPaymentMethodLocators.SUCCESS_TOAST).text
        match = RETURN_NUMBER_PATTERN.search(text)
        if not match:
            logger.warning(f"Success toast present but no return number pattern found in: {text!r}")
            return None
        return match.group()
