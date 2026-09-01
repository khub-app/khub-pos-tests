import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from locators.split_payment_locators import CardPaymentWebviewLocators
from utilities.logger import get_logger

logger = get_logger(__name__)

WEBVIEW_SWITCH_TIMEOUT = 20


class CardPaymentWebviewPage:
    """
    Drives the NMI Collect.js card-entry form reached via Split Payment's
    Card button -> Card Amount popup (Confirm) -> "Enter Card Details
    Manually" -> "Enter card info" (see SplitPaymentPage.open_manual_card_entry).
    Each field (card number, exp date, cvc) is its own cross-origin iframe,
    so this uses Selenium's standard webview/iframe APIs (By,
    switch_to.frame) instead of the AppiumBy-based locator pattern the
    rest of this project uses - the native accessibility tree cannot see
    inside these iframes at all.

    The WEBVIEW_com.anonymous.ititansapp context only attaches a few
    seconds after "Enter card info" is tapped (confirmed live: the form
    shows "Loading card form..." natively before the iframes exist at
    all) - _webview_context() polls for it rather than failing on the
    first check.

    Requires chromedriverAutodownload (see driver_manager.py) and the
    Appium server flag --allow-insecure uiautomator2:chromedriver_autodownload
    (see COMMANDS.md) - without both, entering the webview context raises
    "No Chromedriver found that can automate Chrome ...".
    """

    CONTEXT_POLL_TIMEOUT = 20
    CONTEXT_POLL_INTERVAL = 1

    def __init__(self, driver):
        self.driver = driver

    def _webview_context(self) -> str:
        deadline = time.time() + self.CONTEXT_POLL_TIMEOUT
        contexts = self.driver.contexts
        while time.time() < deadline:
            webview_contexts = [c for c in contexts if c != "NATIVE_APP"]
            if webview_contexts:
                return webview_contexts[0]
            time.sleep(self.CONTEXT_POLL_INTERVAL)
            contexts = self.driver.contexts
        raise RuntimeError(f"No webview context available for card entry after {self.CONTEXT_POLL_TIMEOUT}s. Contexts: {contexts}")

    def _fill_field(self, iframe_id: str, value: str):
        self.driver.switch_to.default_content()
        iframe = WebDriverWait(self.driver, WEBVIEW_SWITCH_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f"#{iframe_id}"))
        )
        self.driver.switch_to.frame(iframe)
        try:
            field = WebDriverWait(self.driver, WEBVIEW_SWITCH_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input"))
            )
            field.click()
            field.send_keys(value)
        finally:
            self.driver.switch_to.default_content()

    def fill_card_details(self, card_number: str, exp_date: str, cvc: str):
        """Switches into the webview context and fills all three hosted
        fields. Leaves the driver in the webview context (default_content)
        on return - call submit_payment() next, or switch back to
        NATIVE_APP explicitly when done with the webview."""
        logger.info("Switching to card entry webview")
        self.driver.switch_to.context(self._webview_context())
        # Let the Collect.js iframes finish their own load/handshake before
        # the first field interaction - confirmed live this needs a beat.
        time.sleep(2)

        logger.info("Entering card number")
        self._fill_field(CardPaymentWebviewLocators.CARD_NUMBER_IFRAME_ID, card_number.replace(" ", ""))
        logger.info("Entering expiration date")
        self._fill_field(CardPaymentWebviewLocators.EXP_DATE_IFRAME_ID, exp_date)
        logger.info("Entering CVC")
        self._fill_field(CardPaymentWebviewLocators.CVC_IFRAME_ID, cvc)
        return self

    def submit_payment(self):
        """Clicks Submit Payment (still within the webview context) and
        waits for NMI to tokenize/process. Switches back to NATIVE_APP
        before returning, since the native "Complete Payment" button is
        the next thing callers need to interact with."""
        logger.info("Clicking Submit Payment")
        self.driver.switch_to.default_content()
        submit_button = WebDriverWait(self.driver, WEBVIEW_SWITCH_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, CardPaymentWebviewLocators.SUBMIT_BUTTON_CSS))
        )
        submit_button.click()
        # NMI's own submit-timeout is 20s (see the webview's own JS) - give
        # it the same headroom rather than guessing a shorter wait.
        time.sleep(20)
        self.driver.switch_to.context("NATIVE_APP")
        return self
