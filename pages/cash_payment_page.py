from locators.sale_order_locators import CashPaymentLocators, ReceiptPromptLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class CashPaymentPage(BasePage):
    def get_amount_due(self) -> str:
        """Never hardcode this — always read the live Amount Due so the
        test tracks whatever the cart/discount actually computed."""
        return self.find(CashPaymentLocators.AMOUNT_DUE_VALUE).text

    def enter_amount(self, amount: str):
        """Cents-style entry, right-to-left, no decimal key on this pad —
        e.g. "19.80" is entered by tapping 1, 9, 8, 0."""
        logger.info(f"Entering cash received: {amount}")
        for digit in amount.replace(".", ""):
            self.click(CashPaymentLocators.digit(digit))
        return self

    def confirm(self):
        logger.info("Confirming cash payment")
        self.click(CashPaymentLocators.CONFIRM_BUTTON)
        return self

    def pay_exact_amount_due(self):
        amount_due = self.get_amount_due()
        self.enter_amount(amount_due)
        self.confirm()
        return amount_due

    def dismiss_receipt_prompt(self):
        logger.info("Dismissing receipt prompt with No Receipt")
        self.click(ReceiptPromptLocators.NO_RECEIPT_BUTTON)
        return self
