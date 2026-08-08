import allure
import pytest
import yaml

from pages.login_page import LoginPage

with open("data/test_data.yaml", "r", encoding="utf-8") as f:
    TEST_DATA = yaml.safe_load(f)


@allure.feature("Login")
@allure.story("Valid credentials")
@pytest.mark.login
def test_login_with_valid_credentials(driver):
    login_page = LoginPage(driver)
    creds = TEST_DATA["login"]["valid"]

    with allure.step("Enter valid username and password, submit login"):
        login_page.login(creds["username"], creds["password"])

    with allure.step("Verify the home screen is displayed after login"):
        assert login_page.is_login_successful(), "Home screen marker not found after login"
