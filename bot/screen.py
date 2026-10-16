# ============================================================
# bot/screen.py — Image Recognition using OpenCV
#
# This is where "Computer Vision" happens!
# OpenCV compares a small template image (like a button)
# to your current screenshot and tells you WHERE it is.
#
# This technique is called "Template Matching".
# ============================================================

import cv2        # OpenCV — for image recognition
import numpy as np  # NumPy — for math on image pixel arrays
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from bot import adb


def load_image(image_path):
    """
    Loads an image file and returns it as a NumPy array.
    OpenCV works with images as arrays of pixel values.
    
    Returns: image array, or None if file not found
    """
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return None
    return cv2.imread(image_path)


def find_on_screen(template_path, screenshot_path=None):
    """
    Looks for a small template image inside the current screen.
    
    HOW IT WORKS (Template Matching):
    - Takes your screenshot (big image = "haystack")
    - Takes your template (small image = "needle")  
    - Slides the needle across the haystack pixel by pixel
    - Calculates similarity score at each position
    - Returns the position where score > CONFIDENCE_THRESHOLD
    
    Args:
        template_path: path to the small image you're looking for
        screenshot_path: path to screenshot (auto-captures if None)
    
    Returns:
        (x, y) — center coordinates if found
        None    — if not found
    """
    # Take a fresh screenshot if no path was given
    if screenshot_path is None:
        if not adb.take_screenshot():
            return None
        screenshot_path = config.SCREENSHOT_PATH

    # Load both images
    screenshot = load_image(screenshot_path)
    template = load_image(template_path)

    if screenshot is None or template is None:
        return None

    # Convert to grayscale — works better for matching
    # (colors don't matter for finding button shapes)
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    # Get the template's size (height, width)
    template_h, template_w = template_gray.shape

    # Run template matching!
    # TM_CCOEFF_NORMED gives a score from -1.0 to 1.0
    result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)

    # Find the position with the BEST (maximum) score
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    print(f"   🔍 Searching for: {os.path.basename(template_path)}")
    print(f"   📊 Best match score: {max_val:.2f} (need > {config.CONFIDENCE_THRESHOLD})")

    # Check if the best score meets our confidence threshold
    if max_val >= config.CONFIDENCE_THRESHOLD:
        # max_loc is the TOP-LEFT corner of the match
        # We want the CENTER of the matched area
        top_left = max_loc
        center_x = top_left[0] + template_w // 2
        center_y = top_left[1] + template_h // 2
        print(f"   ✅ Found at center: ({center_x}, {center_y})")
        return (center_x, center_y)
    else:
        print(f"   ❌ Not found (score too low)")
        return None


def find_all_on_screen(template_path, screenshot_path=None):
    """
    Finds ALL occurrences of a template on the screen.
    
    Useful for finding MULTIPLE Robber Baron castles on the map at once.
    
    Returns:
        list of (x, y) tuples — one for each match found
        empty list [] — if none found
    """
    if screenshot_path is None:
        if not adb.take_screenshot():
            return []
        screenshot_path = config.SCREENSHOT_PATH

    screenshot = load_image(screenshot_path)
    template = load_image(template_path)

    if screenshot is None or template is None:
        return []

    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    template_h, template_w = template_gray.shape

    result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)

    # Get ALL positions where score exceeds threshold
    locations = np.where(result >= config.CONFIDENCE_THRESHOLD)

    matches = []
    for pt in zip(*locations[::-1]):  # zip y-coords with x-coords
        center_x = pt[0] + template_w // 2
        center_y = pt[1] + template_h // 2
        matches.append((center_x, center_y))

    # Remove duplicate matches that are very close together
    matches = deduplicate_matches(matches, min_distance=30)

    print(f"   🔍 Found {len(matches)} instance(s) of {os.path.basename(template_path)}")
    return matches


def deduplicate_matches(matches, min_distance=30):
    """
    Removes duplicate match positions that are too close together.
    
    Why? Template matching sometimes finds the same object multiple times
    with slightly different positions. We only want ONE result per object.
    
    Args:
        matches: list of (x, y) positions
        min_distance: minimum pixels between two different matches
    
    Returns: cleaned list of (x, y) positions
    """
    if not matches:
        return []

    unique = [matches[0]]  # start with first match

    for candidate in matches[1:]:
        # Check if this candidate is far enough from all existing unique matches
        is_duplicate = False
        for existing in unique:
            distance = ((candidate[0] - existing[0])**2 + (candidate[1] - existing[1])**2) ** 0.5
            if distance < min_distance:
                is_duplicate = True
                break
        if not is_duplicate:
            unique.append(candidate)

    return unique


def wait_for_image(template_path, timeout=10, interval=1.0):
    """
    Waits until a template image appears on screen.
    
    Use this to wait for popups, loading screens, buttons to appear.
    
    Args:
        template_path: image to look for
        timeout: max seconds to wait before giving up
        interval: how often to check (seconds)
    
    Returns: (x, y) if found within timeout, None otherwise
    """
    print(f"   ⏳ Waiting for: {os.path.basename(template_path)} (timeout={timeout}s)")
    elapsed = 0
    while elapsed < timeout:
        result = find_on_screen(template_path)
        if result:
            return result
        time.sleep(interval)
        elapsed += interval

    print(f"   ⌛ Timed out waiting for: {os.path.basename(template_path)}")
    return None


def is_visible(template_path):
    """
    Quick check: is this image currently visible on screen?
    Returns True or False.
    """
    return find_on_screen(template_path) is not None


# ============================================================
# QUICK TEST — run this file to test image detection
# Usage: python bot/screen.py
# ============================================================
if __name__ == "__main__":
    print("=== Testing Screen Detection ===")
    print("Taking screenshot...")
    
    if adb.take_screenshot():
        print(f"✅ Screenshot saved: {config.SCREENSHOT_PATH}")
        print("\nNow test finding an image.")
        print("Make sure you have an image in assets/ folder.")
        
        test_image = "assets/robber_baron_icon.png"
        if os.path.exists(test_image):
            result = find_on_screen(test_image)
            if result:
                print(f"✅ Found at: {result}")
            else:
                print("❌ Image not found on screen")
        else:
            print(f"⚠️  No test image at {test_image}")
            print("   Add a template image first, then re-run.")
    else:
        print("❌ Screenshot failed — check ADB connection")
