# ============================================================
# bot/login_bot.py — Auto Game Login via ADB
#
# Detects if the game is on the login screen,
# then types your username & password automatically
# and taps the Login button — just like KINGS bot!
# ============================================================

import time
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from bot import adb, screen

ACCOUNTS_FILE = "accounts.json"

# Login screen template images (screenshot these from your game)
LOGIN_ASSETS = {
    "login_screen":    "assets/login_screen.png",     # any unique element on login screen
    "username_field":  "assets/username_field.png",   # the username text input box
    "password_field":  "assets/password_field.png",   # the password text input box
    "login_button":    "assets/login_button.png",     # the Login / Sign In button
    "home_screen":     "assets/home_screen.png",      # something visible after login succeeds
}


# ============================================================
# ACCOUNT STORAGE
# ============================================================

def load_accounts():
    """Load saved game accounts from accounts.json."""
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as f:
            return json.load(f)
    return []


def save_accounts(accounts):
    """Save accounts to accounts.json."""
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=2)
    print(f"✅ Accounts saved to {ACCOUNTS_FILE}")


def add_account(display_name, username, password, server):
    """Add a new game account."""
    accounts = load_accounts()

    # Check if account already exists
    for acc in accounts:
        if acc["username"] == username:
            print(f"⚠️  Account '{username}' already exists. Updating...")
            acc["password"] = password
            acc["server"]   = server
            acc["name"]     = display_name
            save_accounts(accounts)
            return acc

    new_acc = {
        "id":       len(accounts) + 1,
        "name":     display_name,
        "username": username,
        "password": password,
        "server":   server,
        "status":   "disconnected",
        "last_login": None,
    }
    accounts.append(new_acc)
    save_accounts(accounts)
    print(f"✅ Account '{display_name}' added!")
    return new_acc


def get_active_account():
    """Returns the first account marked as active, or the first account."""
    accounts = load_accounts()
    if not accounts:
        return None
    for acc in accounts:
        if acc.get("active"):
            return acc
    return accounts[0]  # default to first account


# ============================================================
# TYPE TEXT VIA ADB
# ============================================================

def clear_field():
    """Select all text in a field and delete it."""
    # CTRL+A to select all
    adb.run_adb(["shell", "input", "keyevent", "KEYCODE_CTRL_A"])
    time.sleep(0.3)
    # Delete
    adb.run_adb(["shell", "input", "keyevent", "KEYCODE_DEL"])
    time.sleep(0.3)


def type_text(text):
    """
    Type text into the currently focused field via ADB.
    Handles spaces and special characters safely.
    """
    # Replace spaces with %s for ADB input text
    safe_text = text.replace(" ", "%s").replace("'", "\\'")
    adb.run_adb(["shell", "input", "text", safe_text])
    time.sleep(0.5)


def tap_field_and_type(field_template, text):
    """
    Find a text field on screen, tap it, clear it, then type text.

    Args:
        field_template: path to template image of the field
        text: text to type into the field
    """
    pos = screen.wait_for_image(field_template, timeout=8)
    if not pos:
        print(f"❌ Could not find field: {field_template}")
        return False

    adb.tap(pos[0], pos[1])
    time.sleep(0.8)
    clear_field()
    time.sleep(0.3)
    type_text(text)
    time.sleep(0.5)
    return True


# ============================================================
# MAIN LOGIN FUNCTION
# ============================================================

def is_on_login_screen():
    """Check if the game is currently showing the login screen."""
    return screen.is_visible(LOGIN_ASSETS["login_screen"])


def is_logged_in():
    """Check if we're already logged in (home screen visible)."""
    return screen.is_visible(LOGIN_ASSETS["home_screen"])


def login_with_account(account):
    """
    Perform the full login flow for a game account.

    Steps:
      1. Check if already logged in → skip if yes
      2. Wait for login screen
      3. Enter username
      4. Enter password
      5. Tap Login button
      6. Verify login success

    Returns: True if login succeeded, False if failed
    """
    print(f"\n🔐 Logging in as: {account['name']} ({account['username']})")
    print(f"   Server: {account['server']}")

    # Already logged in? No need to do anything
    if is_logged_in():
        print("✅ Already logged in — skipping login")
        return True

    # Wait for login screen to appear
    print("⏳ Waiting for login screen...")
    login_visible = screen.wait_for_image(LOGIN_ASSETS["login_screen"], timeout=15)
    if not login_visible:
        print("❌ Login screen not detected.")
        print("   Make sure Empire: Four Kingdoms is open and on login screen.")
        return False

    print("✅ Login screen detected!")
    time.sleep(1)

    # Enter username
    print(f"   ✏️  Entering username: {account['username']}")
    if not tap_field_and_type(LOGIN_ASSETS["username_field"], account["username"]):
        return False

    # Enter password
    print(f"   ✏️  Entering password: {'*' * len(account['password'])}")
    if not tap_field_and_type(LOGIN_ASSETS["password_field"], account["password"]):
        return False

    # Tap Login button
    print("   👆 Tapping Login button...")
    login_btn = screen.wait_for_image(LOGIN_ASSETS["login_button"], timeout=5)
    if not login_btn:
        print("❌ Login button not found!")
        return False
    adb.tap(login_btn[0], login_btn[1])

    # Wait and check for success
    print("⏳ Waiting for login to complete...")
    time.sleep(5)

    if is_logged_in():
        print(f"🎉 Login SUCCESS! Welcome, {account['name']}!")
        # Update account status
        accounts = load_accounts()
        for acc in accounts:
            if acc["username"] == account["username"]:
                acc["status"] = "connected"
                from datetime import datetime
                acc["last_login"] = datetime.now().isoformat()
        save_accounts(accounts)
        return True
    else:
        print("❌ Login FAILED — wrong username/password or server?")
        print("   Check your credentials in the dashboard.")
        return False


def auto_login():
    """
    Auto-login using the first saved account.
    Called automatically when bot starts.
    """
    account = get_active_account()
    if not account:
        print("⚠️  No accounts saved. Add one in the dashboard first!")
        return False
    return login_with_account(account)


# ============================================================
# TEST
# ============================================================
if __name__ == "__main__":
    print("=== Login Bot Test ===")
    accounts = load_accounts()
    if accounts:
        print(f"Found {len(accounts)} account(s):")
        for a in accounts:
            print(f"  - {a['name']} ({a['username']}) [{a['server']}] status: {a.get('status','?')}")
    else:
        print("No accounts saved yet. Add one via the dashboard.")
