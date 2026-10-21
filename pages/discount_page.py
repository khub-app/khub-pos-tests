import time

from locators.sale_order_locators import DiscountLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class DiscountPage(BasePage):
    def enter_percentage(self, percent: str):
        logger.info(f"Entering discount percentage: {percent}")
        for digit in percent:
            self.click(DiscountLocators.digit(digit))
        return self

    def enter_amount(self, amount: str):
        logger.info(f"Entering discount amount: ${amount}")
        for digit in amount:
            self.click(DiscountLocators.digit(digit))
        return self

    def switch_to_fixed_amount(self):
        """Switches the modal from its default Percentage mode to Fixed ($)
        via the mode dropdown - must be called before entering digits."""
        logger.info("Switching discount mode to Fixed ($)")
        self.click(DiscountLocators.PERCENTAGE_MODE_TRIGGER)
        time.sleep(1)  # let the dropdown render before selecting an option
        self.click(DiscountLocators.FIXED_MODE_OPTION)
        return self

    def confirm(self):
        logger.info("Confirming discount")
        self.click(DiscountLocators.CONFIRM_BUTTON)
        return self

    def apply_percentage_discount(self, percent: str):
        self.enter_percentage(percent)
        self.confirm()

    def apply_fixed_discount(self, amount: str):
        self.switch_to_fixed_amount()
        self.enter_amount(amount)
        self.confirm()

    def is_confirm_enabled(self) -> bool:
        return self.is_enabled(DiscountLocators.CONFIRM_BUTTON)

    def is_exceeds_total_validation_shown(self, timeout: int = 5) -> bool:
        return self.is_displayed(DiscountLocators.VALIDATION_MESSAGE_DISCOUNT_EXCEEDS_TOTAL, timeout)

    def close_without_confirming(self):
        """Leaves the modal without applying anything - Cancel only clears
        digits (see DiscountLocators' docstring), so this uses the Android
        back button instead, the same pattern already proven elsewhere."""
        logger.info("Closing discount modal via back button, without confirming")
        self.driver.back()
        return self
