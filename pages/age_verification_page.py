from locators.sale_order_locators import AgeVerificationLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class AgeVerificationPage(BasePage):
    def is_shown(self, timeout: int = 15) -> bool:
        return self.is_displayed(AgeVerificationLocators.MODAL_TITLE, timeout)

    def enter_dob(self, mm: str, dd: str, yyyy: str):
        logger.info(f"Entering DOB {mm}/{dd}/{yyyy} for age verification")
        dob_field = self.find(AgeVerificationLocators.DOB_FIELD)
        dob_field.click()
        # No real EditText backs this control; `mobile: type` sends keys to
        # whatever is currently focused instead of a specific element.
        self.driver.execute_script("mobile: type", {"text": f"{mm}{dd}{yyyy}"})
        self.hide_keyboard()
        return self

    def _reveal_actions(self, attempts: int = 3):
        # "Check age" / "Confirm & Proceed" render below the fold; a swipe
        # within the modal's own bounds is required before they exist in
        # the tree at all. A single swipe doesn't always travel far enough
        # (observed: sometimes stops one line short, right at the "Age NN —
        # meets 18+ requirement" text) — retry the swipe rather than assume
        # one pass always fully reveals the buttons.
        for attempt in range(1, attempts + 1):
            if self.is_displayed(AgeVerificationLocators.CHECK_AGE_BUTTON, timeout=3):
                return
            logger.info(f"Check age not visible yet, swiping (attempt {attempt}/{attempts})")
            self.driver.execute_script("mobile: swipeGesture", {
                **AgeVerificationLocators.MODAL_SWIPE_REGION,
                "direction": "up",
                "percent": 1.0,
                "speed": 1500,
            })

    def check_age(self):
        logger.info("Tapping Check age")
        self._reveal_actions()
        self.click(AgeVerificationLocators.CHECK_AGE_BUTTON)
        return self

    def confirm_and_proceed(self):
        logger.info("Tapping Confirm & Proceed")
        self.click(AgeVerificationLocators.CONFIRM_AND_PROCEED_BUTTON)
        return self

    def verify(self, mm: str, dd: str, yyyy: str):
        """Full verification flow: enter DOB, check age, confirm & proceed."""
        self.enter_dob(mm, dd, yyyy)
        self.check_age()
        self.confirm_and_proceed()
