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

    def select_user(self, name: str):
        logger.info(f"Selecting clock-in user: {name}")
        self.click(ClockInLocators.SELECT_USER_DROPDOWN)
        self.click(ClockInLocators.user_option(name))
        return self

    def is_already_clocked_in(self, timeout: int = 5) -> bool:
        return self.is_displayed(ClockInLocators.ALREADY_CLOCKED_IN_WARNING, timeout)

    def click_cancel(self):
        logger.info("Clicking Cancel on clock-in dialog")
        self.click(ClockInLocators.CANCEL_BUTTON)
        return self

    def clock_in_user_if_needed(self, name: str, pin: str) -> bool:
        """Select `name` and clock them in, unless the app's own real-time
        check reports they're already clocked in - in which case cancel out
        without touching the PIN or Clock Out. Returns whether a clock-in
        was actually performed."""
        self.select_user(name)
        if self.is_already_clocked_in():
            logger.info(f"{name} was already clocked in; clock-in was skipped")
            self.click_cancel()
            return False
        self.clock_in(pin)
        logger.info(f"{name} was clocked in successfully")
        return True
