# ============================================================
# bot/adb.py — ADB Helper
# ADB = Android Debug Bridge
# This file handles ALL communication with your emulator.
# Think of it as a "remote control" for LDPlayer.
# ============================================================

import subprocess  # lets Python run terminal commands
import os
import sys

# Add parent folder to path so we can import config.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def run_adb(command_args):
    """
    Runs an ADB command and returns the output.
    
    Example:
        run_adb(["devices"])  →  runs: adb devices
        run_adb(["shell", "input", "tap", "500", "800"])  →  taps screen at (500, 800)
    """
    # Build the full command: [adb_path, -s, device_id, ...your_command...]
    full_command = [config.ADB_PATH, "-s", config.DEVICE_ID] + command_args

    try:
        result = subprocess.run(
            full_command,
            capture_output=True,   # capture what the command prints
            text=True              # return output as text (not bytes)
        )
        return result.stdout.strip()  # return output without extra spaces
    except FileNotFoundError:
        print(f"❌ ERROR: ADB not found at: {config.ADB_PATH}")
        print("   Please update ADB_PATH in config.py")
        return None


def get_devices():
    """
    Lists all connected ADB devices (emulators).
    Run this first to check if LDPlayer is detected.
    
    Returns: list of device IDs
    """
    output = run_adb(["devices"])
    if output:
        lines = output.split("\n")
        devices = []
        for line in lines[1:]:  # skip the header line "List of devices attached"
            if "device" in line:
                device_id = line.split("\t")[0]
                devices.append(device_id)
        return devices
    return []


def is_connected():
    """
    Checks if the emulator is connected and ready.
    Returns True or False.
    """
    devices = get_devices()
    if config.DEVICE_ID in devices:
        print(f"✅ Emulator connected: {config.DEVICE_ID}")
        return True
    else:
        print(f"❌ Emulator NOT found. Make sure LDPlayer is running.")
        print(f"   Expected device ID: {config.DEVICE_ID}")
        print(f"   Found devices: {devices}")
        return False


def take_screenshot():
    """
    Takes a screenshot of the emulator screen and saves it as a .png file.
    
    Steps:
    1. Tell Android to take a screenshot and save it on the emulator
    2. Copy that file from the emulator to your PC
    3. Delete the temp file from the emulator
    
    Returns: True if screenshot was saved, False if failed
    """
    # Step 1: Take screenshot on the emulator and save to /sdcard/screen.png
    run_adb(["shell", "screencap", "-p", "/sdcard/screen.png"])

    # Step 2: Pull (copy) the file from emulator to your PC
    run_adb(["pull", "/sdcard/screen.png", config.SCREENSHOT_PATH])

    # Step 3: Delete the screenshot from the emulator (cleanup)
    run_adb(["shell", "rm", "/sdcard/screen.png"])

    # Check if the file was successfully saved on PC
    if os.path.exists(config.SCREENSHOT_PATH):
        return True
    else:
        print("❌ Screenshot failed!")
        return False


def tap(x, y):
    """
    Taps the emulator screen at position (x, y).
    
    x = horizontal position (pixels from left)
    y = vertical position (pixels from top)
    
    Example: tap(500, 800) clicks the center-bottom of a 1000x1600 screen
    """
    print(f"   👆 Tapping at ({x}, {y})")
    run_adb(["shell", "input", "tap", str(x), str(y)])


def swipe(x1, y1, x2, y2, duration_ms=500):
    """
    Swipes from (x1, y1) to (x2, y2) on the emulator screen.
    Used to scroll the world map to find more Robber Barons.
    
    duration_ms = how long the swipe takes (milliseconds)
    """
    print(f"   👆 Swiping from ({x1},{y1}) to ({x2},{y2})")
    run_adb(["shell", "input", "swipe",
             str(x1), str(y1), str(x2), str(y2), str(duration_ms)])


def press_back():
    """
    Presses the Android BACK button.
    Useful for closing popups or going back to previous screen.
    """
    print("   ⬅️  Pressing BACK button")
    run_adb(["shell", "input", "keyevent", "4"])  # keyevent 4 = BACK


# ============================================================
# QUICK TEST — run this file directly to test ADB connection
# Usage: python bot/adb.py
# ============================================================
if __name__ == "__main__":
    print("=== Testing ADB Connection ===")
    print(f"ADB Path: {config.ADB_PATH}")
    print(f"Device ID: {config.DEVICE_ID}")
    print()

    if is_connected():
        print("\nTaking test screenshot...")
        if take_screenshot():
            print(f"✅ Screenshot saved to: {config.SCREENSHOT_PATH}")
        else:
            print("❌ Screenshot failed")
    else:
        print("\n⚠️  Fix connection before running the bot!")
