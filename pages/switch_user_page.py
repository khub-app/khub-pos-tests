from locators.switch_user_locators import SwitchUserLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class SwitchUserPage(BasePage):
    def select_user(self, name: str):
        logger.info(f"Selecting switch-to user: {name}")
        self.click(SwitchUserLocators.user_option(name))
        return self

    def enter_pin(self, pin: str):
        logger.info("Entering switch-user PIN")
        # Only the keypad's first row (1/2/3) is laid out immediately after
        # selecting a user - rows 2-4 (4-9, 0) don't render until the dialog
        # is scrolled. A single fixed scroll_down() used to be enough, but
        # confirmed live this dialog's "Select user" list now shows every
        # real account in the tenant (7+ rows, not just the 1-2 relevant
        # ones) - a longer list pushes the keypad further down, so the
        # scroll distance needed isn't fixed. Scroll incrementally per
        # digit instead, re-checking visibility each time (a no-op once a
        # digit's already in view, so this is safe for repeated digits).
        for digit in pin:
            self._scroll_until_pin_digit_visible(digit)
            self.click(SwitchUserLocators.pin_digit(digit))
        return self

    def _scroll_until_pin_digit_visible(self, digit: str, attempts: int = 4):
        locator = SwitchUserLocators.pin_digit(digit)
        for _ in range(attempts):
            if self.is_displayed(locator, timeout=2):
                return
            self.scroll_down()

    def click_switch(self):
        logger.info("Clicking Switch")
        self.click(SwitchUserLocators.SWITCH_SUBMIT)
        return self

    def switch_to(self, name: str, pin: str):
        self.select_user(name)
        self.enter_pin(pin)
        self.click_switch()
