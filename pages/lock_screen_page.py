from locators.lock_screen_locators import LockScreenLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class LockScreenPage(BasePage):
    def is_shown(self, timeout: int = 15) -> bool:
        return self.is_displayed(LockScreenLocators.TITLE, timeout)

    def is_staff_shown(self, name: str, timeout: int = 10) -> bool:
        return self.is_displayed(LockScreenLocators.staff_name(name), timeout)

    def enter_pin(self, pin: str):
        logger.info("Entering unlock PIN")
        for digit in str(pin):
            self.click(LockScreenLocators.digit(digit))
        return self

    def clear_pin(self):
        logger.info("Clearing entered PIN")
        self.click(LockScreenLocators.CLEAR_BUTTON)
        return self

    def tap_unlock(self):
        logger.info("Tapping Unlock")
        self.click(LockScreenLocators.UNLOCK_BUTTON)
        return self

    def is_incorrect_pin_error_shown(self, timeout: int = 5) -> bool:
        return self.is_displayed(LockScreenLocators.INCORRECT_PIN_ERROR, timeout)
