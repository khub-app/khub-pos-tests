from locators.split_payment_locators import MoreOptionsLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class MoreOptionsPage(BasePage):
    def are_all_options_displayed(self) -> bool:
        return (
            self.is_displayed(MoreOptionsLocators.SPLIT_PAYMENT_OPTION)
            and self.is_displayed(MoreOptionsLocators.ADD_NOTES_OPTION)
            and self.is_displayed(MoreOptionsLocators.RECALL_LAST_PARKED_OPTION)
            and self.is_displayed(MoreOptionsLocators.GO_TO_RETURN_OPTION)
        )

    def select_split_payment(self):
        # Local import: split_payment_page doesn't import this module, so no
        # cycle - kept local only for consistency with the rest of this file
        # being a thin, single-purpose page object.
        from pages.split_payment_page import SplitPaymentPage

        logger.info("Selecting Split Payment")
        self.click(MoreOptionsLocators.SPLIT_PAYMENT_OPTION)
        if self.is_displayed(MoreOptionsLocators.CONFIRM_OK_BUTTON, timeout=3):
            logger.info("Dismissing Split Payment confirmation popup")
            self.click(MoreOptionsLocators.CONFIRM_OK_BUTTON)
        return SplitPaymentPage(self.driver)
