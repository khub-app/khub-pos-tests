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
