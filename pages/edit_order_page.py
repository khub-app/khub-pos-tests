from locators.sales_history_locators import EditOrderLocators
from pages.base_page import BasePage
from utilities.currency import parse_currency
from utilities.logger import get_logger

logger = get_logger(__name__)


class EditOrderPage(BasePage):
    """See locators.sales_history_locators.EditOrderLocators for the known
    "no channel id" issue this flow currently hits on Save."""

    def is_shown(self, timeout: int = 15) -> bool:
        return self.is_displayed(EditOrderLocators.MODAL_TITLE, timeout)

    def set_order_date_to_today(self):
        """Order date is a required field before Save will proceed - its
        picker is a custom calendar, not a native DatePickerDialog."""
        logger.info("Setting Order date to today")
        self.click(EditOrderLocators.ORDER_DATE_FIELD)
        self.click(EditOrderLocators.DATE_PICKER_TODAY_CELL)
        return self

    def set_sale_price(self, price: str):
        logger.info(f"Setting Sale Price/Unit to {price}")
        field = self.find(EditOrderLocators.SALE_PRICE_FIELD)
        field.click()
        field.clear()
        field.send_keys(price)
        self.hide_keyboard()
        return self

    def get_subtotal(self) -> float:
        return parse_currency(self.find(EditOrderLocators.SUBTOTAL_VALUE).text)

    def save(self):
        logger.info("Tapping Save")
        self.click(EditOrderLocators.SAVE_BUTTON)
        return self

    def cancel(self):
        logger.info("Cancelling Edit Order")
        self.click(EditOrderLocators.CANCEL_BUTTON)
        return self

    def is_no_channel_error_shown(self, timeout: int = 10) -> bool:
        return self.is_displayed(EditOrderLocators.NO_CHANNEL_ERROR, timeout)

    def dismiss_error(self):
        logger.info("Dismissing error dialog")
        self.click(EditOrderLocators.ERROR_OK_BUTTON)
        return self
