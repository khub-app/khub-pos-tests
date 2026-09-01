from locators.sale_return_locators import SalesReturnTabLocators
from locators.sales_history_locators import SalesHistoryLocators
from pages.base_page import BasePage
from pages.sale_return_page import SaleReturnPage
from utilities.logger import get_logger

logger = get_logger(__name__)


class SalesHistoryPage(BasePage):
    def search_by_order_id(self, order_no: str):
        logger.info(f"Searching Sales History for order: {order_no}")
        self.type_text(SalesHistoryLocators.SEARCH_BY_ORDER_ID_FIELD, order_no)
        return self

    def open_transaction_lookup_tab(self):
        logger.info("Opening Transaction Lookup tab")
        self.click(SalesReturnTabLocators.TRANSACTION_LOOKUP_TAB)
        return self

    def select_order_row(self, order_no: str):
        logger.info(f"Selecting order row: {order_no}")
        self.click(SalesReturnTabLocators.order_row(order_no))
        return self

    def tap_sales_return(self) -> SaleReturnPage:
        logger.info("Tapping Sales Return")
        self.click(SalesReturnTabLocators.SALES_RETURN_BUTTON)
        return SaleReturnPage(self.driver)

    def return_order(self, order_no: str) -> SaleReturnPage:
        """Full flow from the Sales History screen to the return-quantity
        screen for a specific order: Transaction Lookup tab -> search +
        select the order row -> its own contextual Sales Return action
        button. Confirmed via a live manual walkthrough — do NOT go through
        the "Sales Returns" tab, that's a different (non-creating) flow."""
        self.open_transaction_lookup_tab()
        self.search_by_order_id(order_no)
        self.select_order_row(order_no)
        return self.tap_sales_return()

    def is_order_row_lifecycle_completed(self, order_no: str, timeout: int = 10) -> bool:
        return self.is_displayed(SalesHistoryLocators.order_row_lifecycle(order_no), timeout)

    def get_order_row_sale_total_text(self, order_no: str) -> str:
        return self.find(SalesHistoryLocators.order_row_sale_total(order_no)).text

    def is_action_menu_enabled(self, timeout: int = 10) -> bool:
        """The right-side action menu (Print/View Order/...) is absent from
        the tree entirely until a row is selected — this checks presence of
        its Print button as a proxy for "the menu is now enabled"."""
        return self.is_displayed(SalesHistoryLocators.PRINT_BUTTON, timeout)

    def click_print(self):
        from pages.invoice_preview_page import InvoicePreviewPage

        logger.info("Clicking Print to open the invoice preview")
        self.click(SalesHistoryLocators.PRINT_BUTTON)
        return InvoicePreviewPage(self.driver)

    def click_view_order(self):
        from pages.order_details_page import OrderDetailsPage

        logger.info("Clicking View Order to open Order Details")
        self.click(SalesHistoryLocators.VIEW_ORDER_BUTTON)
        return OrderDetailsPage(self.driver)

    def open_invoice_preview_for_order(self, order_no: str):
        """Full flow: Transaction Lookup tab -> search + select the order
        row -> Print. Mirrors return_order()'s navigation, ending at Print
        instead of Sales Return."""
        self.open_transaction_lookup_tab()
        self.search_by_order_id(order_no)
        self.select_order_row(order_no)
        return self.click_print()

    def get_first_row_content_desc(self, timeout: int = 10) -> str:
        """Fallback for when no order number was captured after payment:
        reads the newest (first, unsearched) row's full content-desc
        ("{order_no}, {date}, {name}, {name}, {mode}, ${total}, {lifecycle}")
        so the caller can verify it belongs to this test by customer name +
        sale total + lifecycle before selecting it, per the project's
        documented "don't trust the first row blindly" convention."""
        element = self.find(SalesHistoryLocators.FIRST_ROW, timeout)
        return element.get_attribute("content-desc")

    def select_first_row(self):
        logger.info("Selecting the first (newest) result row")
        self.click(SalesHistoryLocators.FIRST_ROW)
        return self

    def is_no_returnable_orders_shown(self, timeout: int = 10) -> bool:
        return self.is_displayed(SalesReturnTabLocators.NO_RETURNABLE_ORDERS_TEXT, timeout)

    def click_void_payment(self):
        from pages.void_payment_page import VoidPaymentPage

        logger.info("Clicking Void Payment")
        self.click(SalesHistoryLocators.VOID_PAYMENT_BUTTON)
        return VoidPaymentPage(self.driver)

    def click_edit_order(self):
        from pages.edit_order_page import EditOrderPage

        logger.info("Clicking Edit Order")
        self.click(SalesHistoryLocators.EDIT_ORDER_BUTTON)
        return EditOrderPage(self.driver)
