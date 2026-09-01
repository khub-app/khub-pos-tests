import time

from locators.split_payment_locators import AddCustomerLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class AddCustomerPage(BasePage):
    def is_shown(self, timeout: int = 15) -> bool:
        return self.is_displayed(AddCustomerLocators.MODAL_TITLE, timeout)

    def search_by_email(self, email: str):
        # This is a live/debounced search-as-you-type field whose results
        # dropdown is driven by an onChangeText-style handler - confirmed
        # live that BasePage.type_text()'s plain send_keys() (no prior tap)
        # sets the field's text fine but never triggers that handler, so no
        # results ever appear. An explicit tap to focus the field first,
        # then send_keys, reliably triggers it. Also needs a moment to
        # settle afterwards, same class of issue as
        # SaleOrderPage.add_product_by_upc's product search.
        logger.info(f"Searching for customer by email: {email}")
        field = self.find(AddCustomerLocators.EMAIL_SEARCH_FIELD)
        field.click()
        field.send_keys(email)
        time.sleep(3)
        return self

    def select_customer(self, name: str):
        # Do NOT hide_keyboard() here - the search-results dropdown is tied
        # to the field's focus/keyboard state and collapses (taking the
        # result row with it) as soon as the keyboard is dismissed.
        logger.info(f"Selecting customer: {name}")
        self.click(AddCustomerLocators.search_result_row(name))
        return self

    def confirm_if_still_open(self):
        """Normally, tapping the search-result card alone applies the
        customer and closes this panel immediately - confirmed live. But
        this has occasionally been flaky (the tap not registering as a
        selection), leaving the panel open with its own "Add Customer"
        confirm button still visible. Use a short timeout so the normal
        (already-closed) case doesn't pay the full default-timeout cost."""
        if self.is_shown(timeout=3):
            logger.info("Panel still open after selecting the row - confirming explicitly")
            self.click(AddCustomerLocators.CONFIRM_BUTTON)
        return self

    def search_and_select(self, email: str, name: str):
        self.search_by_email(email)
        self.select_customer(name)
        self.confirm_if_still_open()
