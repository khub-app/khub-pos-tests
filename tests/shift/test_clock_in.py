import allure
import yaml

from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


@allure.feature("Shift")
@allure.story("Clock in")
def test_clock_in_with_valid_pin(driver):
    login_page = LoginPage(driver)
    creds = TEST_DATA["login"]["valid"]

    with allure.step("Log in"):
        login_page.login(creds["username"], creds["password"])
        assert login_page.is_login_successful(), "Home screen marker not found after login"

    dashboard = DashboardPage(driver)
    with allure.step("Open Time Clock"):
        clockin_page = dashboard.open_time_clock()

    with allure.step("Enter PIN and submit Clock In"):
        clockin_page.clock_in(TEST_DATA["shift"]["clock_in_pin"])

    with allure.step("Verify the dashboard shows Clocked In"):
        assert dashboard.is_clocked_in(), "Dashboard did not show 'Clocked In' after submitting PIN"
