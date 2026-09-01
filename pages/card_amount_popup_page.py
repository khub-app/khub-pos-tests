from locators.split_payment_locators import CardAmountPopupLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class CardAmountPopupPage(BasePage):
    """The "Card Amount" popup opened from Split Payment's Card button.
    Pre-filled with the entire remaining balance, which is what this
    suite's Split Payment flow wants - unlike CashAmountPopupPage, no
    digit entry is needed, just Confirm."""

    def is_shown(self, timeout: int = 15) -> bool:
        return self.is_displayed(CardAmountPopupLocators.MODAL_TITLE, timeout)

    def confirm(self):
        logger.info("Confirming card amount")
        self.click(CardAmountPopupLocators.CONFIRM_BUTTON)
        return self
