import os

import openpyxl
import pytest

from utilities.driver_manager import DriverManager
from utilities.logger import get_logger
from utilities.screenshot_helper import take_screenshot

logger = get_logger(__name__)


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default=None,
        help="Target environment defined in config/config.yaml (e.g. emulator, real_device)",
    )


# ------------------ Dynamic markers from Excel Tags sheet ------------------
# Mirrors khub-web-tests' conftest.py: data/test_data.xlsx's "Tags" sheet has
# one row per test file (FilePath | smoke | regression | Date Added). A "Yes"
# in a marker column auto-applies that pytest marker to every item collected
# from that file, so `pytest -m smoke` / `-m regression` are driven by the
# spreadsheet instead of hardcoded decorators. New test file -> add a row
# here (exact relative path, matched as a path suffix) or it gets no markers.

def _load_tags_from_excel():
    """Read the Tags sheet and return {filepath: [marker_names]}."""
    excel_path = os.path.join(os.path.dirname(__file__), "data", "test_data.xlsx")
    if not os.path.exists(excel_path):
        return {}
    wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
    if "Tags" not in wb.sheetnames:
        wb.close()
        return {}
    ws = wb["Tags"]
    headers = [cell.value for cell in ws[1]]
    marker_names = headers[1:]  # skip FilePath column
    tag_map = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        filepath = row[0]
        if not filepath:
            continue
        filepath = filepath.replace("\\", "/")
        markers = []
        for i, val in enumerate(row[1:]):
            if val and str(val).strip().lower() == "yes" and i < len(marker_names):
                markers.append(marker_names[i])
        if markers:
            tag_map[filepath] = markers
    wb.close()
    return tag_map


def pytest_collection_modifyitems(config, items):
    """Auto-apply markers from the Excel Tags sheet to collected test items."""
    tag_map = _load_tags_from_excel()
    if not tag_map:
        return
    applied_count = 0
    for item in items:
        item_path = str(item.fspath).replace("\\", "/")
        for tagged_path, markers in tag_map.items():
            if item_path.endswith(tagged_path):
                for marker_name in markers:
                    item.add_marker(getattr(pytest.mark, marker_name))
                applied_count += 1
                break
    if applied_count:
        print(f"\n[INFO] Applied Excel tags to {applied_count} test items from {len(tag_map)} tagged files")


# Holds whatever driver is currently active so the failure-screenshot hook
# below can find it regardless of the requesting fixture's scope (a
# class-scoped `driver` sets request.node to the *class* node, not the
# function `item` the hook receives — so we track it here instead of trying
# to stash it on a node object whose identity depends on scope).
_active_driver = {"instance": None}


@pytest.fixture(scope="class")
def driver(request):
    env_name = request.config.getoption("--env")
    manager = DriverManager(env_name)
    manager.reset_app_data()  # every class starts logged out, regardless of run order
    driver_instance = manager.start_driver()  # app renders landscape by default, no forcing needed
    _active_driver["instance"] = driver_instance
    yield driver_instance
    _active_driver["instance"] = None
    manager.stop_driver()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        driver_instance = _active_driver["instance"]
        if driver_instance is not None:
            screenshot_path = take_screenshot(driver_instance, item.name)
            logger.error(f"Test failed: {item.name}. Screenshot saved to {screenshot_path}")
            try:
                import allure
                with open(screenshot_path, "rb") as image_file:
                    allure.attach(
                        image_file.read(),
                        name="failure_screenshot",
                        attachment_type=allure.attachment_type.PNG,
                    )
            except ImportError:
                pass
