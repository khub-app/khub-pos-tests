import os
import shutil
import subprocess

from appium import webdriver
from appium.options.android import UiAutomator2Options

from config.config_reader import ConfigReader
from utilities.logger import get_logger

logger = get_logger(__name__)


class DriverManager:
    """Builds capabilities from config/config.yaml and owns the Appium session lifecycle."""

    def __init__(self, env_name: str | None = None):
        self.env_name = env_name
        self.config = ConfigReader().get_environment(env_name)
        self.driver = None

    def reset_app_data(self):
        """Clear the app's local storage via adb so every test starts logged out.

        Needed because this app persists its login session across restarts
        (noReset keeps it that way) — without this, test order would affect
        whether a test sees the Login screen or an already-authenticated app.
        """
        app_package = self.config.get("app_package")
        if not app_package:
            return

        adb = self._adb_path()
        cmd = [adb]
        if self.config.get("udid"):
            cmd += ["-s", self.config["udid"]]
        cmd += ["shell", "pm", "clear", app_package]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"adb pm clear failed for {app_package}: {result.stderr.strip()}")
        else:
            logger.info(f"Cleared app data for {app_package}")

    @staticmethod
    def _adb_path() -> str:
        exe_name = "adb.exe" if os.name == "nt" else "adb"
        candidate_roots = [
            os.environ.get("ANDROID_HOME"),
            os.environ.get("ANDROID_SDK_ROOT"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk") if os.name == "nt" else None,
        ]
        for root in candidate_roots:
            if not root:
                continue
            candidate = os.path.join(root, "platform-tools", exe_name)
            if os.path.isfile(candidate):
                return candidate
        return shutil.which("adb") or exe_name

    def start_driver(self):
        options = UiAutomator2Options()
        options.platform_name = self.config.get("platform_name", "Android")
        options.automation_name = self.config.get("automation_name", "UiAutomator2")
        options.device_name = self.config["device_name"]
        options.app_package = self.config["app_package"]
        options.app_activity = self.config["app_activity"]
        options.no_reset = self.config.get("no_reset", True)
        options.full_reset = self.config.get("full_reset", False)
        options.new_command_timeout = self.config.get("new_command_timeout", 120)
        options.auto_grant_permissions = self.config.get("auto_grant_permissions", True)
        # This app takes 15-20s+ to report its first frame drawn on a loaded
        # emulator; Appium's 20s default adbExecTimeout is too tight for that.
        options.set_capability("adbExecTimeout", self.config.get("adb_exec_timeout", 60000))
        # Needed for any test that drives the NMI card-entry webview (Split
        # Payment's Credit/Debit Card flow): without it, switching into that
        # webview context fails with "No Chromedriver found that can
        # automate Chrome ...". Also requires the Appium server itself to be
        # started with --allow-insecure uiautomator2:chromedriver_autodownload
        # (see COMMANDS.md) - this capability alone is not sufficient.
        options.set_capability("chromedriverAutodownload", True)
        # This app's checkout screens render landscape by default (matches
        # real POS tablet usage) — no orientation forcing needed. All
        # coordinate-based taps/swipes (search result rows, age-verification
        # swipe region) are calibrated against the 2560x1600 landscape
        # viewport that shows up out of the box.

        if self.config.get("app_path"):
            options.app = self.config["app_path"]
        if self.config.get("udid"):
            options.udid = self.config["udid"]
        if self.config.get("platform_version"):
            options.platform_version = self.config["platform_version"]

        server_url = self.config.get("appium_server", "http://127.0.0.1:4723")
        logger.info(f"Starting Appium session on {server_url} (env={self.env_name or 'default'})")
        self.driver = webdriver.Remote(server_url, options=options)
        return self.driver

    def stop_driver(self):
        if self.driver is not None:
            logger.info("Quitting Appium session")
            self.driver.quit()
            self.driver = None
