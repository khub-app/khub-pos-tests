from locators.sale_order_locators import ReceiptPromptLocators
from locators.split_payment_locators import SplitPaymentLocators
from pages.base_page import BasePage
from pages.card_amount_popup_page import CardAmountPopupPage
from pages.card_payment_webview_page import CardPaymentWebviewPage
from pages.cash_amount_popup_page import CashAmountPopupPage
from utilities.currency import parse_currency
from utilities.logger import get_logger

logger = get_logger(__name__)


class SplitPaymentPage(BasePage):
    def is_shown(self, timeout: int = 15) -> bool:
        return self.is_displayed(SplitPaymentLocators.MODAL_TITLE, timeout)

    def _scroll_to_summary(self):
        """The Total/Paid/Remaining summary sits at the top of this dialog's
        own internal scroll area - after interacting with the card webview
        (further down, past Added Payments), that summary can scroll out of
        the rendered viewport entirely (same virtualization behavior as the
        Switch User dialog's PIN keypad rows). Scrolling up is a harmless
        no-op if it's already visible."""
        self.scroll_up()

    def get_total_amount(self) -> float:
        self._scroll_to_summary()
        return parse_currency(self.find(SplitPaymentLocators.TOTAL_AMOUNT_VALUE).text)

    def get_paid_amount(self) -> float:
        self._scroll_to_summary()
        return parse_currency(self.find(SplitPaymentLocators.PAID_AMOUNT_VALUE).text)

    def get_remaining_amount(self) -> float:
        self._scroll_to_summary()
        return parse_currency(self.find(SplitPaymentLocators.REMAINING_VALUE).text)

    def click_cash(self):
        """Adds a Cash row pre-filled with the ENTIRE remaining balance -
        confirmed live this is the button's default behavior, matching why
        the amount then needs editing down via set_cash_amount()."""
        logger.info("Adding Cash payment method")
        self.click(SplitPaymentLocators.CASH_BUTTON)
        return self

    def click_card(self):
        """Adds a Card row pre-filled with the entire remaining balance.
        Unlike Cash, tapping the Card button opens a "Card Amount" popup
        first (confirmed live) - since the pre-filled amount is already
        the full remaining balance this suite wants, this confirms it
        immediately rather than exposing a separate step to callers."""
        logger.info("Adding Card payment method")
        self.click(SplitPaymentLocators.CARD_BUTTON)
        card_amount_popup = CardAmountPopupPage(self.driver)
        assert card_amount_popup.is_shown(), "Card Amount popup did not open after tapping Card"
        card_amount_popup.confirm()
        return self

    def open_manual_card_entry(self) -> CardPaymentWebviewPage:
        """Navigates from the confirmed Card row to the NMI Collect.js
        webview form. Usually takes two native taps - "Enter Card Details
        Manually" (under the "Card - NMI Terminal" section) reveals a
        further "Key In Card" choice, and only "Enter card info" there
        actually attaches the WEBVIEW_com.anonymous.ititansapp context
        (the alternative at each step, "Use NMI Card Reader" / "Charge $X
        on reader", drives the physical NMI reader instead - unusable here
        since this emulator is rooted, which NMI's SDK refuses to connect
        to). Confirmed live this app SOMETIMES skips straight to the card
        form without either intermediate tap (a failure screenshot caught
        it mid-run: Card Number/Exp Date/CVC already on screen right after
        confirming the Card Amount popup) - each tap is only attempted if
        its button actually shows up within a few seconds, rather than
        blindly clicking and hanging on the default 60s wait when the app
        took the shorter path."""
        logger.info("Opening manual card entry")
        if self.is_displayed(SplitPaymentLocators.ENTER_CARD_DETAILS_MANUALLY_BUTTON, timeout=5):
            self.click(SplitPaymentLocators.ENTER_CARD_DETAILS_MANUALLY_BUTTON)
        if self.is_displayed(SplitPaymentLocators.ENTER_CARD_INFO_BUTTON, timeout=5):
            self.click(SplitPaymentLocators.ENTER_CARD_INFO_BUTTON)
        return CardPaymentWebviewPage(self.driver)

    def edit_added_payment_amount(self, current_amount_text: str):
        """Taps the Edit icon for the Added Payments row whose amount
        currently reads `current_amount_text` (e.g. "$27.50"), opening the
        Cash Amount popup. `current_amount_text` must match the row's
        content-desc value exactly, since the icon has no accessible node
        of its own and is located as a sibling of the amount cell."""
        self.click(SplitPaymentLocators.edit_icon_for_amount(current_amount_text))
        return CashAmountPopupPage(self.driver)

    def set_cash_amount(self, current_amount_text: str, new_amount: str):
        """Full flow: open the Cash row's Cash Amount popup, clear the
        auto-populated value, enter `new_amount`, confirm."""
        popup = self.edit_added_payment_amount(current_amount_text)
        popup.set_amount(new_amount)
        return self

    def pay_by_card(self, card_number: str, exp_date: str, cvc: str) -> CardPaymentWebviewPage:
        """Fills and submits the NMI hosted card form for the Card row
        already added via click_card(). Returns to the NATIVE_APP context
        before returning, so callers can immediately check/click Complete
        Payment on this same SplitPaymentPage."""
        webview = self.open_manual_card_entry()
        webview.fill_card_details(card_number, exp_date, cvc)
        webview.submit_payment()
        return webview

    def is_complete_payment_enabled(self) -> bool:
        return self.is_enabled(SplitPaymentLocators.COMPLETE_PAYMENT_BUTTON)

    def complete_payment(self):
        logger.info("Clicking Complete Payment")
        self.click(SplitPaymentLocators.COMPLETE_PAYMENT_BUTTON)
        return self

    def dismiss_receipt_prompt(self):
        """Reuses the same No Receipt locator as the direct (non-split)
        cash flow's CashPaymentPage - confirmed live this is the identical
        element/behavior regardless of which payment flow reached it."""
        logger.info("Dismissing receipt prompt with No Receipt")
        self.click(ReceiptPromptLocators.NO_RECEIPT_BUTTON)
        return self
