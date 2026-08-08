from locators.clockin_locators import ClockInLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class ClockInPage(BasePage):
    def enter_pin(self, pin: str):
        logger.info("Entering clock-in PIN")
        for digit in pin:
            self.click(ClockInLocators.pin_digit(digit))
        return self

    def click_clock_in(self):
        logger.info("Clicking Clock In")
        self.click(ClockInLocators.CLOCK_IN_SUBMIT)
        return self

    def clock_in(self, pin: str):
        self.enter_pin(pin)
        self.click_clock_in()
