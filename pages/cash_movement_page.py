import re

from appium.webdriver.common.appiumby import AppiumBy

from locators.cash_movement_locators import CashMovementLocators
from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class CashMovementPage(BasePage):
    """Shared page object for the Cash In / Cash Out modals.

    Confirmed live 2026-10-20: the three money values (Amount / Current
    Drawer / New Drawer) are NOT safely readable via a per-label
    following-sibling lookup - this modal has the same label-group-then-
    value-group DOM structure already documented for the Discount modal,
    and a naive lookup silently resolves to the WRONG value regardless of
    which label is anchored on. Reading all three decimal-formatted
    ("12.34"-shaped) text nodes in document order and indexing
    positionally (0=typed amount, 1=current drawer, 2=new drawer) is the
    approach confirmed reliable live.
    """

    def _read_three_money_values(self) -> list[float]:
        values = []
        for el in self.driver.find_elements(AppiumBy.XPATH, "//*[@text!='']"):
            if re.fullmatch(r"\d+\.\d{2}", el.text):
                values.append(float(el.text))
            if len(values) == 3:
                break
        return values

    def tap_quick_amount(self, amount: str):
        logger.info(f"Tapping quick amount {amount}")
        self.click(CashMovementLocators.quick_amount(amount))
        return self

    def get_amount(self) -> float:
        return self._read_three_money_values()[0]

    def get_current_drawer(self) -> float:
        return self._read_three_money_values()[1]

    def get_new_drawer(self) -> float:
        return self._read_three_money_values()[2]

    def is_confirm_enabled(self) -> bool:
        return self.is_enabled(CashMovementLocators.CONFIRM_BUTTON)

    def confirm(self):
        logger.info("Confirming cash movement")
        self.click(CashMovementLocators.CONFIRM_BUTTON)
        return self
