from appium.webdriver.common.appiumby import AppiumBy

from utilities.logger import get_logger
from utilities.screenshot_helper import take_screenshot
from utilities.wait_helper import WaitHelper

logger = get_logger(__name__)


class BasePage:
    """Common element interactions and mobile gestures shared by every page object."""

    def __init__(self, driver):
        self.driver = driver
        self.wait = WaitHelper(driver)

    # --- element interaction -------------------------------------------------
    def find(self, locator, timeout=None):
        return self.wait.wait_for_visible(locator, timeout)

    def click(self, locator, timeout=None):
        element = self.wait.wait_for_clickable(locator, timeout)
        element.click()
        return element

    def type_text(self, locator, text: str, clear_first: bool = True, timeout=None):
        element = self.wait.wait_for_visible(locator, timeout)
        if clear_first:
            element.clear()
        element.send_keys(text)
        return element

    def get_text(self, locator, timeout=None) -> str:
        return self.wait.wait_for_visible(locator, timeout).text

    def is_displayed(self, locator, timeout: int = 5) -> bool:
        try:
            self.wait.wait_for_visible(locator, timeout)
            return True
        except Exception:
            return False

    # --- mobile gestures -------------------------------------------------------
    def hide_keyboard(self):
        try:
            self.driver.hide_keyboard()
        except Exception:
            logger.debug("Keyboard already hidden or not present")

    def scroll_down(self, percent: float = 0.8, speed: int = 4000):
        size = self.driver.get_window_size()
        self.driver.execute_script("mobile: swipeGesture", {
            "left": int(size["width"] * 0.1),
            "top": int(size["height"] * 0.2),
            "width": int(size["width"] * 0.8),
            "height": int(size["height"] * 0.6),
            "direction": "up",
            "percent": percent,
            "speed": speed,
        })

    def scroll_up(self, percent: float = 0.8, speed: int = 4000):
        size = self.driver.get_window_size()
        self.driver.execute_script("mobile: swipeGesture", {
            "left": int(size["width"] * 0.1),
            "top": int(size["height"] * 0.2),
            "width": int(size["width"] * 0.8),
            "height": int(size["height"] * 0.6),
            "direction": "down",
            "percent": percent,
            "speed": speed,
        })

    def scroll_into_view_by_text(self, text: str, exact: bool = False):
        method = "text" if exact else "textContains"
        selector = (
            f'new UiScrollable(new UiSelector().scrollable(true))'
            f'.scrollIntoView(new UiSelector().{method}("{text}"))'
        )
        return self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, selector)

    def take_screenshot(self, name: str) -> str:
        return take_screenshot(self.driver, name)
