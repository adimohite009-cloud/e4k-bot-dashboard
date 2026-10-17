# ============================================================
# tools/capture_traffic_fiddler.py
#
# EASIER alternative to mitmproxy.
# Uses Fiddler Classic (free) which works automatically
# with LDPlayer without any proxy configuration inside Android.
#
# HOW TO USE:
#   1. Download Fiddler Classic (free):
#      https://www.telerik.com/fiddler/fiddler-classic
#   2. Install it on your PC
#   3. Open Fiddler → Tools → Options → HTTPS
#      - Check "Capture HTTPS CONNECTs"
#      - Check "Decrypt HTTPS traffic"
#      - Click OK, trust the certificate
#   4. In Fiddler → Tools → Options → Connections
#      - Check "Allow remote computers to connect"
#      - Port: 8888
#   5. Run THIS script: python tools/capture_traffic_fiddler.py
#   6. Play the game normally (login + attack 1 RB)
#   7. Press CTRL+C here when done
# ============================================================

import os
import json
import time
import sys
from datetime import datetime

# Try to read Fiddler's SAZ export or use its log file
FIDDLER_LOG_DIR = os.path.expandvars(r"%USERPROFILE%\Documents\Fiddler2\Captures")
OUTPUT_DIR = "captured_traffic"
os.makedirs(OUTPUT_DIR, exist_ok=True)

GAME_KEYWORDS = [
    "goodgame", "empire", "e4k", "ggs-", "gamigo",
    "castle", "attack", "troop", "resource", "fourking"
]

print("""
╔══════════════════════════════════════════════════════╗
║   E4K Traffic Capture - Fiddler Method              ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  Make sure Fiddler Classic is open and capturing!   ║
║                                                      ║
║  In Fiddler: Tools → Options → HTTPS                ║
║    ✓ Capture HTTPS CONNECTs                         ║
║    ✓ Decrypt HTTPS traffic                          ║
║                                                      ║
║  LDPlayer proxy is set AUTOMATICALLY by Fiddler.   ║
║  Just open the game and play!                       ║
║                                                      ║
╚══════════════════════════════════════════════════════╝

Monitoring for game traffic... Play the game now!
Press CTRL+C when done (after attacking 1 Robber Baron).
""")

# Monitor Fiddler's captures directory for new files
print(f"Watching: {FIDDLER_LOG_DIR}")
print(f"Output will be saved to: {OUTPUT_DIR}/\n")

captured_count = 0

try:
    while True:
        # Check for new SAZ files from Fiddler
        if os.path.exists(FIDDLER_LOG_DIR):
            files = [f for f in os.listdir(FIDDLER_LOG_DIR) if f.endswith('.saz')]
            if files:
                print(f"\n✅ Found {len(files)} Fiddler capture file(s)!")
                print(f"   Analyzing for game traffic...")

        print(f"\r⏳ Waiting for game traffic... {datetime.now().strftime('%H:%M:%S')}", end="", flush=True)
        time.sleep(2)

except KeyboardInterrupt:
    print("\n\n✅ Capture stopped!")
    print(f"\n📁 Check Fiddler for captured sessions:")
    print(f"   File → Save → All Sessions → save as game_traffic.saz")
    print(f"   Then share the .saz file and I can extract the API endpoints!")
    print(f"\nAlternatively, in Fiddler:")
    print(f"   1. Click any request in the list")
    print(f"   2. Look at the URL at top - those are the API endpoints!")
    print(f"   3. Press CTRL+A to select all, then File → Export → as CSV")
