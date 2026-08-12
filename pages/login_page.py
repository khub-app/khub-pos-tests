from locators.clockin_locators import ClockInLocators
from locators.login_locators import LoginLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class LoginPage(BasePage):
    def enter_username(self, username: str):
        logger.info("Entering username")
        self.type_text(LoginLocators.USERNAME_INPUT, username)
        return self

    def enter_password(self, password: str):
        logger.info("Entering password")
        self.type_text(LoginLocators.PASSWORD_INPUT, password)
        return self

    def click_login(self):
        logger.info("Clicking login button")
        self.hide_keyboard()
        self.click(LoginLocators.LOGIN_BUTTON)
        return self

    def login(self, username: str, password: str):
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()

    def is_login_successful(self, timeout: int = 15) -> bool:
        # The app auto-opens the "Clock in to your Account" modal right after
        # login when the cashier isn't clocked in, which covers the dashboard's
        # HOME_SCREEN_MARKER and makes it report as not displayed. Either the
        # modal or the marker showing means login itself succeeded.
        half = max(timeout // 2, 1)
        if self.is_displayed(ClockInLocators.MODAL_TITLE, half):
            return True
        return self.is_displayed(LoginLocators.HOME_SCREEN_MARKER, half)
