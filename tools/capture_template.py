# ============================================================
# tools/capture_template.py — Helper Tool
#
# Run this script to CAPTURE template images from the game.
# This is how you create the images that the bot looks for!
#
# Usage:
#   1. Open LDPlayer with Empire: Four Kingdoms
#   2. Navigate to where you want to capture (e.g., world map)
#   3. Run: python tools/capture_template.py
#   4. Follow the on-screen instructions
# ============================================================

import subprocess
import os
import sys
from PIL import Image  # Pillow — for cropping the screenshot

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def take_screenshot_via_adb():
    """Takes a screenshot from the emulator and saves it."""
    print("📸 Taking screenshot from emulator...")
    
    subprocess.run([config.ADB_PATH, "-s", config.DEVICE_ID,
                    "shell", "screencap", "-p", "/sdcard/screen.png"])
    subprocess.run([config.ADB_PATH, "-s", config.DEVICE_ID,
                    "pull", "/sdcard/screen.png", "full_screen.png"])
    subprocess.run([config.ADB_PATH, "-s", config.DEVICE_ID,
                    "shell", "rm", "/sdcard/screen.png"])
    
    if os.path.exists("full_screen.png"):
        print("✅ Screenshot saved as: full_screen.png")
        return True
    return False


def crop_template(output_name, x, y, width, height):
    """
    Crops a region from the full screenshot and saves it as a template.
    
    Args:
        output_name: name to save as (e.g., "robber_baron_icon")
        x, y: top-left corner of the region to crop
        width, height: size of the region
    """
    img = Image.open("full_screen.png")
    
    # Define crop box: (left, top, right, bottom)
    crop_box = (x, y, x + width, y + height)
    cropped = img.crop(crop_box)
    
    os.makedirs("assets", exist_ok=True)
    output_path = f"assets/{output_name}.png"
    cropped.save(output_path)
    print(f"✅ Template saved: {output_path}  (size: {width}x{height} px)")


def interactive_capture():
    """
    Interactive mode: asks the user for crop coordinates.
    
    TIP: Open full_screen.png in Paint or any image viewer,
    hover over the element you want, and note the pixel coordinates.
    """
    print("""
╔══════════════════════════════════════════════════════╗
║            TEMPLATE CAPTURE TOOL                    ║
╚══════════════════════════════════════════════════════╝

This tool helps you capture template images from the game.

Steps:
  1. A screenshot will be taken from LDPlayer
  2. Open 'full_screen.png' in Windows Paint or any image editor
  3. Hover over the element you want to capture
  4. Note the X, Y coordinates and size
  5. Enter them below to crop and save the template
""")
    
    if not take_screenshot_via_adb():
        print("❌ Screenshot failed. Check ADB connection.")
        return
    
    print("\nOpen 'full_screen.png' in an image viewer and find the coordinates.")
    print("Then enter the details below:\n")
    
    templates = [
        ("map_button",           "World Map button (bottom menu)"),
        ("robber_baron_icon",    "Robber Baron castle icon on world map"),
        ("attack_button",        "'Attack' button in castle popup"),
        ("send_troops_button",   "'Send' / confirm troops button"),
        ("max_troops_button",    "'Max' troops button (optional, press ENTER to skip)"),
    ]
    
    for (name, description) in templates:
        print(f"\n📌 Capture: {description}")
        print(f"   Will save as: assets/{name}.png")
        
        x_str = input("   X (left edge, pixels): ").strip()
        if not x_str:
            print("   Skipped.")
            continue
        
        y_str = input("   Y (top edge, pixels): ").strip()
        w_str = input("   Width (pixels): ").strip()
        h_str = input("   Height (pixels): ").strip()
        
        try:
            x, y, w, h = int(x_str), int(y_str), int(w_str), int(h_str)
            crop_template(name, x, y, w, h)
        except ValueError:
            print("   ❌ Invalid numbers — skipping this template")

    print("\n✅ Done! Run main.py to start the bot.")
    print("   If a button is not detected, re-capture it with a tighter crop.")


if __name__ == "__main__":
    interactive_capture()
