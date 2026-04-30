"""Screen OCR and automation for extracting base64 encoded content."""

from __future__ import annotations

import base64
import io
import re
import time
from dataclasses import dataclass

import pyautogui
from PIL import Image

from ..capture.screenshot import grab
from ..logger import get

logger = get("openchronicle.screen_ocr")


@dataclass
class OCRResult:
    text: str
    base64_content: str | None = None


def perform_ocr(image) -> str:
    """Perform OCR on the given image."""
    try:
        import pytesseract
    except ImportError as exc:
        logger.error("pytesseract not installed: %s", exc)
        return ""

    try:
        text = pytesseract.image_to_string(image)
        return text
    except Exception as exc:
        logger.error("OCR failed: %s", exc)
        return ""


def extract_base64(text: str) -> str | None:
    """Extract base64 encoded content from the text."""
    # Look for base64 patterns
    base64_pattern = r'[A-Za-z0-9+/=]{100,}'
    matches = re.findall(base64_pattern, text)
    
    if matches:
        # Return the longest match, likely the full base64 content
        return max(matches, key=len)
    return None


def scroll_screen(duration: float = 2.0, steps: int = 10):
    """Scroll the screen to capture more content."""
    step_duration = duration / steps
    for _ in range(steps):
        pyautogui.scroll(-100)  # Scroll down
        time.sleep(step_duration)


def capture_and_process() -> OCRResult:
    """Capture screen, perform OCR, and extract base64 content."""
    # Capture screenshot
    screenshot = grab()
    if not screenshot:
        logger.error("Failed to capture screenshot")
        return OCRResult(text="")

    # Convert base64 to image for OCR
    try:
        image_data = base64.b64decode(screenshot.image_base64)
        image = Image.open(io.BytesIO(image_data))
    except Exception as exc:
        logger.error("Failed to process image: %s", exc)
        return OCRResult(text="")

    # Perform OCR
    text = perform_ocr(image)
    logger.info(f"OCR extracted {len(text)} characters")

    # Extract base64 content
    base64_content = extract_base64(text)
    if base64_content:
        logger.info(f"Found base64 content of length {len(base64_content)}")

    return OCRResult(text=text, base64_content=base64_content)


def automated_extraction(max_scrolls: int = 3) -> str:
    """Automated extraction with scrolling."""
    all_text = ""
    all_base64 = []

    for i in range(max_scrolls):
        logger.info(f"Capture attempt {i+1}/{max_scrolls}")
        result = capture_and_process()
        all_text += result.text
        
        if result.base64_content:
            all_base64.append(result.base64_content)
        
        if i < max_scrolls - 1:
            scroll_screen()

    # Combine all base64 content (if multiple parts)
    if all_base64:
        # Try to find the longest continuous base64 string
        combined_base64 = "".join(all_base64)
        return combined_base64

    return ""
