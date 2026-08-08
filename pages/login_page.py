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
        return self.is_displayed(LoginLocators.HOME_SCREEN_MARKER, timeout)
