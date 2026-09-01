import base64
from datetime import datetime
from pathlib import Path

from utilities.logger import get_logger

logger = get_logger(__name__)

VIDEO_DIR = Path(__file__).resolve().parents[1] / "videos"
VIDEO_DIR.mkdir(exist_ok=True)


def start_recording(driver):
    """Starts an Appium/uiautomator2 screen recording for the current step.
    Android's screenrecord has a hard 3-minute cap per recording (Appium
    enforces the same limit) - safe here since this suite records one video
    PER TEST METHOD (one logical UI step), not per whole scenario; a full
    17-step scenario can run several minutes end to end, but no single step
    does. Never raises - a recording problem must not fail the actual test."""
    try:
        driver.start_recording_screen(timeLimit=180)
    except Exception as e:
        logger.warning(f"Could not start screen recording: {e}")


def stop_recording_and_save(driver, name: str) -> str | None:
    """Stops the recording and saves it to videos/. Returns the saved path,
    or None if recording wasn't available/failed."""
    try:
        video_b64 = driver.stop_recording_screen()
        if not video_b64:
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        filepath = VIDEO_DIR / f"{safe_name}_{timestamp}.mp4"
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(video_b64))
        return str(filepath)
    except Exception as e:
        logger.warning(f"Could not save screen recording: {e}")
        return None
