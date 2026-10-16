# ============================================================
# config.py — All settings in ONE place
# Change values here without touching the rest of the code!
# ============================================================

# --- ADB Settings ---
# The ADB executable path (comes with LDPlayer)
ADB_PATH = r"C:\LDPlayer\LDPlayer9\adb.exe"

# Device ID — run `adb devices` in terminal to find yours
# Usually "emulator-5554" for LDPlayer
DEVICE_ID = "emulator-5554"

# --- Screenshot Settings ---
# Temporary file where the bot saves its screenshots
SCREENSHOT_PATH = "screen.png"

# --- Image Recognition Settings ---
# How confident OpenCV must be to say "yes, I found the button"
# 0.0 = accept anything, 1.0 = perfect match required
# 0.8 is a good starting value
CONFIDENCE_THRESHOLD = 0.8

# --- Attack Bot Settings ---
# How long to wait between each attack loop (in seconds)
ATTACK_INTERVAL_SECONDS = 120   # 2 minutes between attacks

# Maximum number of attacks to do before stopping (safety limit)
MAX_ATTACKS_PER_SESSION = 30

# How long to wait after clicking Attack before clicking Send (seconds)
ATTACK_POPUP_WAIT = 3

# How long to wait for troops to march & come back (seconds)
TROOP_RETURN_WAIT = 60

# --- Logging ---
LOG_FILE = "logs/attack_log.txt"
