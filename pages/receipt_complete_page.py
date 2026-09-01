import re

from locators.split_payment_locators import ReceiptCompleteLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)

ORDER_NUMBER_PATTERN = re.compile(r"SO-\d{6}-\d+")


class ReceiptCompletePage(BasePage):
    """The confirmation screen shown after a receipt-delivery choice is
    resolved (e.g. after tapping No Receipt). Not guaranteed to appear in
    every flow - callers should check is_shown() rather than assume it."""

    def is_shown(self, timeout: int = 15) -> bool:
        return self.is_displayed(ReceiptCompleteLocators.MODAL_TITLE, timeout)

    def get_order_number(self) -> str | None:
        """Extracts the SO-XXXXXX-XXXXX order number from the Reference
        line (e.g. "Reference: RCP-SO-260819-63404-..."). Returns None if
        the reference text isn't present or doesn't contain a recognizable
        order number, rather than raising - callers should fall back to
        matching on customer/total/lifecycle in Transaction Lookup instead."""
        if not self.is_displayed(ReceiptCompleteLocators.REFERENCE_TEXT, timeout=5):
            return None
        text = self.find(ReceiptCompleteLocators.REFERENCE_TEXT).text
        match = ORDER_NUMBER_PATTERN.search(text)
        if not match:
            logger.warning(f"Reference text present but no order number pattern found in: {text!r}")
            return None
        order_no = match.group()
        logger.info(f"Captured order number from receipt reference: {order_no}")
        return order_no

    def click_done(self):
        logger.info("Dismissing Receipt complete")
        self.click(ReceiptCompleteLocators.DONE_BUTTON)
        return self
