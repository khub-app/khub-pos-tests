from locators.sales_history_locators import OrderDetailsLocators
from pages.base_page import BasePage
from utilities.currency import parse_currency
from utilities.logger import get_logger

logger = get_logger(__name__)


class OrderDetailsPage(BasePage):
    """The "Order Details" modal opened via Sales History's "View Order"
    action - confirmed live this is the screen that actually carries
    structured Sub Total / Total / Amount Paid / Invoice Status fields, used
    as the primary post-payment total validation (the Print Preview receipt
    has no such fields - see InvoicePreviewPage)."""

    def is_shown(self, timeout: int = 15) -> bool:
        return self.is_displayed(OrderDetailsLocators.MODAL_TITLE, timeout)

    def get_sub_total(self) -> float:
        return parse_currency(self.find(OrderDetailsLocators.SUB_TOTAL_VALUE).text)

    def get_total(self) -> float:
        return parse_currency(self.find(OrderDetailsLocators.TOTAL_VALUE).text)

    def get_amount_paid(self) -> float:
        return parse_currency(self.find(OrderDetailsLocators.AMOUNT_PAID_VALUE).text)

    def is_invoice_status_paid(self) -> bool:
        return self.is_displayed(OrderDetailsLocators.INVOICE_STATUS_PAID_BADGE, timeout=5)

    def open_payment_history_tab(self):
        logger.info("Opening Payment History tab")
        self.click(OrderDetailsLocators.PAYMENT_HISTORY_TAB)
        return self

    def has_cash_payment_row(self) -> bool:
        return self.is_displayed(OrderDetailsLocators.CASH_PAYMENT_ROW, timeout=5)

    def has_card_payment_row(self) -> bool:
        return self.is_displayed(OrderDetailsLocators.CARD_PAYMENT_ROW, timeout=5)

    def close(self):
        logger.info("Closing Order Details")
        self.click(OrderDetailsLocators.CLOSE_BUTTON)
        return self
