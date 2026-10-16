# ============================================================
# tools/capture_traffic.py — Capture E4K Game API Traffic
#
# This tool sets up a proxy that captures all HTTP requests
# the game makes when you play normally. Run this ONCE,
# play the game for 5 minutes, then the bot knows all the
# API endpoints it needs!
#
# HOW TO USE:
#   1. Run: python tools/capture_traffic.py
#   2. Configure LDPlayer to use proxy 127.0.0.1:8888
#   3. Open Empire: Four Kingdoms in LDPlayer
#   4. Login, open world map, attack a Robber Baron
#   5. Press CTRL+C to stop capture
#   6. Check captured_traffic/ folder for the API calls
# ============================================================

import subprocess
import sys
import os
import json
import re

# Install mitmproxy if needed
def install_mitmproxy():
    print("📦 Installing mitmproxy...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mitmproxy"])
    print("✅ mitmproxy installed!")

try:
    import mitmproxy
except ImportError:
    install_mitmproxy()

import json
import os
from datetime import datetime

OUTPUT_DIR = "captured_traffic"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# mitmproxy addon — captures and saves all game requests
# ============================================================

ADDON_SCRIPT = '''
import json, os, re
from datetime import datetime
from mitmproxy import http

OUTPUT_DIR = "captured_traffic"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Keywords that indicate game-related traffic
GAME_KEYWORDS = [
    "goodgame", "empire", "e4k", "ggs-", "gamigo",
    "castle", "attack", "troop", "resource"
]

captured = []

def response(flow: http.HTTPFlow):
    """Called for every HTTP response the game receives."""
    url = flow.request.url.lower()

    # Only capture game-related traffic
    if not any(kw in url for kw in GAME_KEYWORDS):
        return

    entry = {
        "timestamp": datetime.now().isoformat(),
        "method":    flow.request.method,
        "url":       flow.request.url,
        "headers":   dict(flow.request.headers),
        "body":      flow.request.get_text(strict=False),
        "response_status": flow.response.status_code,
        "response_body":   flow.response.get_text(strict=False)[:2000],  # first 2000 chars
    }

    captured.append(entry)

    # Save to file after each request
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/request_{len(captured):04d}_{ts}.json"
    with open(filename, "w") as f:
        json.dump(entry, f, indent=2)

    print(f"✅ Captured [{flow.request.method}] {flow.request.url[:80]}")

def done():
    """Called when mitmproxy shuts down — save summary."""
    summary_file = f"{OUTPUT_DIR}/summary.json"
    with open(summary_file, "w") as f:
        json.dump(captured, f, indent=2)
    print(f"\\n📁 Saved {len(captured)} requests to {OUTPUT_DIR}/")
    print(f"   Summary: {summary_file}")
'''

# Write the addon script
addon_path = os.path.join(OUTPUT_DIR, "addon.py")
with open(addon_path, "w") as f:
    f.write(ADDON_SCRIPT)

print("""
╔══════════════════════════════════════════════════════╗
║        E4K Traffic Capture Tool                     ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  STEP 1: This tool will start a proxy on port 8888  ║
║                                                      ║
║  STEP 2: In LDPlayer settings, go to:               ║
║    Settings → Network → Use Proxy                   ║
║    Host: 127.0.0.1   Port: 8888                     ║
║                                                      ║
║  STEP 3: Open Empire: Four Kingdoms                  ║
║    - Log in to your account                         ║
║    - Open the world map                             ║
║    - Attack at least 1 Robber Baron castle          ║
║                                                      ║
║  STEP 4: Press CTRL+C to stop                       ║
║    Captured API calls saved to: captured_traffic/   ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
""")

input("Press ENTER to start the proxy...")

# Start mitmproxy
print("\n🚀 Starting proxy on http://127.0.0.1:8888 ...")
print("   (A browser window may open — you can close it)\n")

os.system(f'mitmdump -p 8888 -s "{addon_path}" --ssl-insecure')
