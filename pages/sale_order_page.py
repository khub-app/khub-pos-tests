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
                # tap_first_result() is a fixed-coordinate tap - confirmed
                # live via page-source dump that a still-open keyboard can
                # intercept/absorb that tap (the search field's results
                # stay on screen, untouched, exactly as if nothing was
                # tapped at all) even though the row's bounds don't
                # visually overlap the keyboard. Dismiss it here so the
                # coordinate tap reliably reaches the row underneath.
                self.hide_keyboard()
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

    def add_product_by_upc(self, upc: str, dob: tuple[str, str, str] | None = None, max_attempts: int = 3) -> bool:
        """Search + add a product by UPC. If age verification appears, `dob`
        (mm, dd, yyyy) must be provided to clear it; if it doesn't appear,
        `dob` is ignored. Returns whether age verification appeared, so
        callers/tests can assert on it explicitly rather than relying on the
        ValueError-if-unhandled side effect alone.

        tap_first_result() is a coordinate tap (see its docstring - result
        rows have no accessible node at all), and confirmed live 2026-10-19
        that it can silently miss: the search results stay on screen
        untouched (same screen, same query, same row) with the cart total
        unchanged - no exception, nothing to catch, the row is simply never
        actually added. Standalone repro scripts never hit this (small
        sample luck), but it reproduced on every real pytest run of this
        suite's second-product step. Verifying the cart's own product count
        actually increased, and retrying the search+tap when it didn't, is
        the fix - not a locator problem, there's no accessible element to
        fix a locator for."""
        before_qty = self._current_quantity()
        for attempt in range(1, max_attempts + 1):
            self.search_product(upc)
            time.sleep(3)  # let the search results settle before tapping
            self.tap_first_result()
            time.sleep(2)  # let the add-to-cart + any UI transition settle

            age_verification = AgeVerificationPage(self.driver)
            shown = age_verification.is_shown()
            if shown:
                if dob is None:
                    raise ValueError(f"Age verification appeared for UPC {upc} but no dob was provided")
                age_verification.verify(*dob)

            after_qty = self._current_quantity()
            if after_qty > before_qty:
                return shown
            logger.warning(
                f"Product {upc} did not register in the cart (qty {before_qty} -> {after_qty}) - "
                f"retrying search+tap (attempt {attempt}/{max_attempts})"
            )
        raise RuntimeError(f"Product {upc} still not added to cart after {max_attempts} attempts")

    def _current_quantity(self) -> int:
        """Like get_total_quantity(), but tolerant of the drawer/value not
        being there yet (returns 0) - used internally to verify an add
        actually landed, before the cart necessarily has anything in it."""
        self.expand_totals_drawer()
        if not self.is_displayed(SaleOrderLocators.TOTAL_QUANTITY_VALUE, timeout=3):
            return 0
        return int(self.find(SaleOrderLocators.TOTAL_QUANTITY_VALUE).text)

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

    def open_park_order(self):
        from locators.sale_order_locators import ParkOrderLocators
        from pages.park_order_page import ParkOrderPage

        logger.info("Opening Park Order")
        self.click(ParkOrderLocators.TRIGGER)
        return ParkOrderPage(self.driver)

    def tap_cash(self) -> CashPaymentPage:
        logger.info("Tapping Cash")
        self.click(SaleOrderLocators.CASH_BUTTON)
        return CashPaymentPage(self.driver)

    def tap_cash_on_empty_cart(self):
        """Like tap_cash(), but for the empty-cart negative case: the app
        shows an error dialog instead of opening CashPaymentPage, so this
        deliberately stays on SaleOrderPage rather than returning one."""
        logger.info("Tapping Cash with an empty cart")
        self.click(SaleOrderLocators.CASH_BUTTON)
        return self

    def is_add_products_first_error_shown(self, timeout: int = 5) -> bool:
        return self.is_displayed(SaleOrderLocators.ADD_PRODUCTS_FIRST_ERROR_MESSAGE, timeout)

    def dismiss_add_products_first_error(self):
        logger.info("Dismissing 'Please add products to cart first' error")
        self.click(SaleOrderLocators.ADD_PRODUCTS_FIRST_ERROR_OK_BUTTON)
        return self

    def tap_quantity_increment(self):
        """Coordinate tap - see QUANTITY_INCREMENT_COORDS' docstring. Only
        valid for the cart's first/only row."""
        self.driver.execute_script("mobile: clickGesture", SaleOrderLocators.QUANTITY_INCREMENT_COORDS)
        return self

    def tap_quantity_decrement(self):
        self.driver.execute_script("mobile: clickGesture", SaleOrderLocators.QUANTITY_DECREMENT_COORDS)
        return self

    def remove_product(self):
        logger.info("Removing product")
        self.click(SaleOrderLocators.REMOVE_PRODUCT_BUTTON)
        return self

    def empty_cart(self):
        logger.info("Emptying cart")
        self.click(SaleOrderLocators.EMPTY_CART_BUTTON)
        self.click(SaleOrderLocators.EMPTY_CART_CONFIRM_BUTTON)
        return self

    def is_cart_empty(self, timeout: int = 10) -> bool:
        return self.is_displayed(SaleOrderLocators.NO_PRODUCTS_IN_CART_MARKER, timeout)

    def go_to_menu(self):
        # Local import: dashboard_page imports SaleOrderPage at module level,
        # so importing DashboardPage there would be circular.
        from pages.dashboard_page import DashboardPage

        logger.info("Tapping Go to Menu")
        self.click(SaleOrderLocators.GO_TO_MENU_BUTTON)
        return DashboardPage(self.driver)

    def is_guest_customer(self, timeout: int = 10) -> bool:
        return self.is_displayed(SaleOrderLocators.GUEST_CUSTOMER_MARKER, timeout)

    def is_customer_selected(self, name: str, timeout: int = 10) -> bool:
        return self.is_displayed(SaleOrderLocators.current_customer_name(name), timeout)

    def open_add_quick_customer(self):
        from pages.add_customer_page import AddCustomerPage

        logger.info("Opening Add Quick Customer")
        self.click(SaleOrderLocators.ADD_QUICK_CUSTOMER_BUTTON)
        return AddCustomerPage(self.driver)

    def open_more_options(self):
        from pages.more_options_page import MoreOptionsPage

        logger.info("Opening More Options")
        self.click(SaleOrderLocators.MORE_OPTIONS_BUTTON)
        return MoreOptionsPage(self.driver)
