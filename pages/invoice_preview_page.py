from locators.sales_history_locators import InvoicePreviewLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class InvoicePreviewPage(BasePage):
    """The plain-text receipt opened via the "Print" action. Confirmed live
    it carries no Total/Payment-amount fields - see
    locators/sales_history_locators.py::InvoicePreviewLocators for the
    verified content. Only used to confirm Print Preview actually opens;
    use OrderDetailsPage (via "View Order") for the real total validation."""

    def is_shown(self, timeout: int = 15) -> bool:
        return self.is_displayed(InvoicePreviewLocators.MODAL_TITLE, timeout)

    def shows_order_number(self, order_no: str) -> bool:
        return self.is_displayed(InvoicePreviewLocators.order_number_marker(order_no))

    def shows_customer_name(self, name: str) -> bool:
        return self.is_displayed(InvoicePreviewLocators.customer_name_marker(name))

    def shows_product_name(self, name: str) -> bool:
        return self.is_displayed(InvoicePreviewLocators.product_name_marker(name))

    def close(self):
        """No reliable accessible close button (its content-desc is empty) -
        the Android back button reliably dismisses this modal instead."""
        logger.info("Dismissing Print Preview")
        self.driver.back()
        return self
