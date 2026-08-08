import time

from selenium.common.exceptions import InvalidElementStateException, StaleElementReferenceException

from locators.sale_order_locators import SaleOrderLocators
from pages.age_verification_page import AgeVerificationPage
from pages.base_page import BasePage
from pages.cash_payment_page import CashPaymentPage
from pages.discount_page import DiscountPage
from utilities.currency import parse_currency
from utilities.logger import get_logger

logger = get_logger(__name__)


class SaleOrderPage(BasePage):
    def search_product(self, query: str, attempts: int = 3):
        """Search the product list. The search box requires two taps before
        it accepts input — the first tap only changes its hint text to
        "Tap again to type…" and the field itself reports enabled=false
        until the second tap. That means BasePage.click()'s wait-for-
        clickable would deadlock here (it refuses to tap an element the
        app itself won't mark enabled until that same tap happens), so
        this uses a plain find+click for both taps instead.

        The whole tap-tap-type sequence occasionally hits a transient
        InvalidElementStateException (the field re-renders between the
        second tap and the keystroke) — retried a few times rather than
        failing the whole flow on what's proven to be a one-off race."""
        logger.info(f"Searching for product: {query}")
        last_exc = None
        for attempt in range(1, attempts + 1):
            try:
                self.wait.wait_for_visible(SaleOrderLocators.SEARCH_PRODUCTS_FIELD).click()
                time.sleep(1)
                field = self.wait.wait_for_visible(SaleOrderLocators.SEARCH_PRODUCTS_FIELD)
                field.click()
                field.send_keys(query)
                return self
            except (InvalidElementStateException, StaleElementReferenceException) as e:
                last_exc = e
                logger.warning(f"search_product attempt {attempt}/{attempts} failed ({type(e).__name__}), retrying")
                time.sleep(1.5)
        raise last_exc

    def tap_first_result(self):
        """Result rows have no accessible node (confirmed empty across the
        whole tree), so this is a deliberate coordinate tap, not a shortcut."""
        logger.info("Tapping first search result")
        self.driver.execute_script("mobile: clickGesture", SaleOrderLocators.FIRST_RESULT_ROW_COORDS)
        return self

    def add_product_by_upc(self, upc: str, dob: tuple[str, str, str] | None = None) -> bool:
        """Search + add a product by UPC. If age verification appears, `dob`
        (mm, dd, yyyy) must be provided to clear it; if it doesn't appear,
        `dob` is ignored. Returns whether age verification appeared, so
        callers/tests can assert on it explicitly rather than relying on the
        ValueError-if-unhandled side effect alone."""
        self.search_product(upc)
        time.sleep(3)  # let the search results settle before tapping
        self.tap_first_result()

        age_verification = AgeVerificationPage(self.driver)
        shown = age_verification.is_shown()
        if shown:
            if dob is None:
                raise ValueError(f"Age verification appeared for UPC {upc} but no dob was provided")
            age_verification.verify(*dob)
        return shown

    def expand_totals_drawer(self, attempts: int = 3):
        """The cart summary (Total Quantity / Sub Total / Total / etc.)
        lives in a bottom drawer that's collapsed by default — its labels
        are completely absent from the tree until this handle is tapped.
        Idempotent: does nothing if already expanded."""
        for attempt in range(1, attempts + 1):
            if self.is_displayed(SaleOrderLocators.TOTAL_QUANTITY_VALUE, timeout=3):
                return self
            logger.info(f"Totals drawer not expanded yet, tapping handle (attempt {attempt}/{attempts})")
            self.driver.execute_script("mobile: clickGesture", SaleOrderLocators.TOTALS_DRAWER_HANDLE_COORDS)
            time.sleep(1)
        return self

    def get_total_quantity(self) -> int:
        """Read the live "Total Quantity" cart value — never hardcode this,
        it depends on how many products were added."""
        self.expand_totals_drawer()
        return int(self.find(SaleOrderLocators.TOTAL_QUANTITY_VALUE).text)

    def get_sub_total(self) -> float:
        self.expand_totals_drawer()
        return parse_currency(self.find(SaleOrderLocators.SUB_TOTAL_VALUE).text)

    def get_grand_total(self) -> float:
        self.expand_totals_drawer()
        return parse_currency(self.find(SaleOrderLocators.GRAND_TOTAL_VALUE).text)

    def open_additional_discount(self) -> DiscountPage:
        logger.info("Opening Additional Discount")
        self.click(SaleOrderLocators.ADDITIONAL_DISCOUNT_BUTTON)
        return DiscountPage(self.driver)

    def tap_cash(self) -> CashPaymentPage:
        logger.info("Tapping Cash")
        self.click(SaleOrderLocators.CASH_BUTTON)
        return CashPaymentPage(self.driver)

    def go_to_menu(self):
        # Local import: dashboard_page imports SaleOrderPage at module level,
        # so importing DashboardPage there would be circular.
        from pages.dashboard_page import DashboardPage

        logger.info("Tapping Go to Menu")
        self.click(SaleOrderLocators.GO_TO_MENU_BUTTON)
        return DashboardPage(self.driver)
