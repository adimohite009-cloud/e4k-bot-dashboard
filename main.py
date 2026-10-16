# ============================================================
# main.py — Entry Point for the Empire Bot
#
# This is the file you run to start the bot.
# Usage: python main.py
# ============================================================

import sys
import os

# Make sure we can import our bot modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from bot import adb
from bot.attack_bot import run_attack_loop


def check_assets():
    """
    Checks if all required template images exist in the assets/ folder.
    Warns the user about any missing images before starting.
    """
    required_assets = [
        "assets/map_button.png",
        "assets/robber_baron_icon.png",
        "assets/attack_button.png",
        "assets/send_troops_button.png",
    ]

    optional_assets = [
        "assets/max_troops_button.png",
        "assets/close_button.png",
        "assets/back_button.png",
    ]

    print("\n📁 Checking asset images...")
    all_ok = True

    for asset in required_assets:
        if os.path.exists(asset):
            print(f"   ✅ {asset}")
        else:
            print(f"   ❌ MISSING (required): {asset}")
            all_ok = False

    for asset in optional_assets:
        if os.path.exists(asset):
            print(f"   ✅ {asset}")
        else:
            print(f"   ⚠️  MISSING (optional): {asset}")

    return all_ok


def print_instructions():
    """Prints startup instructions for the user."""
    print("""
╔══════════════════════════════════════════════════════╗
║        EMPIRE: FOUR KINGDOMS — ATTACK BOT           ║
║              by [Your Name] — Learning Project      ║
╚══════════════════════════════════════════════════════╝

HOW TO USE:
  1. Open LDPlayer and launch Empire: Four Kingdoms
  2. Make sure you are logged in and the game is on the main screen
  3. Make sure all template images are in the assets/ folder
  4. Press ENTER to start the bot

CONTROLS:
  • Press CTRL+C at any time to stop the bot safely

LOGS:
  • Activity is saved to: logs/attack_log.txt
""")


def main():
    """Main function — runs all startup checks then launches the bot."""
    
    print_instructions()

    # --- Step 1: Check ADB connection ---
    print("🔌 Checking ADB connection to LDPlayer...")
    if not adb.is_connected():
        print("\n❌ Cannot connect to emulator. Please:")
        print("   1. Make sure LDPlayer is running")
        print("   2. Enable ADB in LDPlayer: Settings → Other Settings → ADB")
        print("   3. Check that ADB_PATH in config.py is correct")
        print(f"      Current path: {config.ADB_PATH}")
        sys.exit(1)

    # --- Step 2: Check template images ---
    assets_ok = check_assets()
    if not assets_ok:
        print("\n❌ Some required images are missing!")
        print("   Please take screenshots of the game UI and save them in assets/")
        print("   See README.md for detailed instructions on how to do this.")
        print("\n   Do you want to continue anyway? (y/n): ", end="")
        answer = input().strip().lower()
        if answer != "y":
            sys.exit(0)

    # --- Step 3: Make sure logs folder exists ---
    os.makedirs("logs", exist_ok=True)

    # --- Step 4: Start the bot ---
    print("\n" + "="*50)
    print("🚀 Starting attack bot...")
    print(f"   Max attacks: {config.MAX_ATTACKS_PER_SESSION}")
    print(f"   Interval between rounds: {config.ATTACK_INTERVAL_SECONDS}s")
    print(f"   Confidence threshold: {config.CONFIDENCE_THRESHOLD}")
    print("="*50 + "\n")

    input("Press ENTER to start (or CTRL+C to cancel)...")

    try:
        run_attack_loop()
    except KeyboardInterrupt:
        print("\n\n⛔ Bot stopped by user (CTRL+C)")
        print("   Check logs/attack_log.txt for activity history")


if __name__ == "__main__":
    main()
