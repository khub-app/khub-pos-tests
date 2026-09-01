from locators.split_payment_locators import CashAmountPopupLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class CashAmountPopupPage(BasePage):
    """The "Cash Amount" popup opened from a Split Payment Cash row's Edit
    icon. Distinct from pages/cash_payment_page.py, which is the direct
    (non-split) "Total Cash Recieved" modal - different dialog, different
    resource-ids (this one's digits have no resource-id at all, unlike
    clockin-num-X/CashPaymentLocators's digit pad)."""

    def is_shown(self, timeout: int = 15) -> bool:
        return self.is_displayed(CashAmountPopupLocators.MODAL_TITLE, timeout)

    def clear_amount(self, max_presses: int = 10):
        logger.info("Clearing the auto-populated cash amount")
        delete_button = self.find(CashAmountPopupLocators.DELETE_BUTTON)
        for _ in range(max_presses):
            delete_button.click()
        return self

    def enter_amount(self, amount: str):
        """Cents-style entry, right-to-left - e.g. "10.00" is entered by
        tapping 1, 0, 0, 0."""
        logger.info(f"Entering cash amount: {amount}")
        for digit in amount.replace(".", ""):
            self.click(CashAmountPopupLocators.digit(digit))
        return self

    def confirm(self):
        logger.info("Confirming cash amount")
        self.click(CashAmountPopupLocators.CONFIRM_BUTTON)
        return self

    def set_amount(self, amount: str):
        self.clear_amount()
        self.enter_amount(amount)
        self.confirm()
