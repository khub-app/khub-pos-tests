from locators.shift_locators import ShiftLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class ShiftPage(BasePage):
    def open_start_shift(self):
        logger.info("Tapping Start Shift")
        self.click(ShiftLocators.START_SHIFT_BUTTON)
        return self

    def confirm_start_shift(self):
        logger.info("Confirming Start Shift with $0.00 opening cash")
        self.find(ShiftLocators.MODAL_TITLE)
        self.click(ShiftLocators.START_SHIFT_BUTTON)
        return self

    def start_shift(self):
        self.open_start_shift()
        self.confirm_start_shift()
        return self
