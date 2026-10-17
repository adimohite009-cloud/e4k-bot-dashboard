# ============================================================
# tools/test_connection.py — Test Direct E4K Server Connection
#
# Uses the ggxs library to connect directly to the game server
# NO emulator needed — pure Python WebSocket connection!
# ============================================================

import asyncio
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Discovered from YOUR traffic capture ──────────────────────
YOUR_SERVER   = "e4k-live-int2-game.goodgamestudios.com"
YOUR_ZONE     = "EmpirefourkingdomsExGG_21"
YOUR_ZONE_ID  = 327
YOUR_PLAYER_ID = "16-72-21-8730956"
# ──────────────────────────────────────────────────────────────

ACCOUNTS_FILE = "accounts.json"

def load_account():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE) as f:
            accounts = json.load(f)
        if accounts:
            return accounts[0]
    return None

async def test_connection(username, password):
    print(f"\n🔌 Connecting to E4K server...")
    print(f"   Server:  {YOUR_SERVER}")
    print(f"   Zone:    {YOUR_ZONE}")
    print(f"   User:    {username}")
    print()

    try:
        from ggxs import GGXS

        class E4KClient(GGXS):
            def __init__(self):
                super().__init__(
                    url=f"wss://{YOUR_SERVER}/",
                    server_header=YOUR_ZONE,
                    username=username,
                    password=password,
                )

            async def run_jobs(self):
                print("✅ Connected! Getting castle info...")
                try:
                    castles = await self.get_detailed_castles()
                    print(f"🏰 Found {len(castles)} castle(s)!")
                    for c in castles:
                        print(f"   - {c}")
                except Exception as e:
                    print(f"   Castle fetch: {e}")

                print("\n✅ Connection test SUCCESSFUL!")
                print("   The bot can now run 24/7 without emulator!")

        client = E4KClient()
        await client.connect()

    except ImportError:
        print("❌ ggxs not installed. Run: pip install ggxs")
    except Exception as e:
        print(f"❌ Connection error: {type(e).__name__}: {e}")
        print("\n💡 This might mean:")
        print("   - Wrong username/password")
        print("   - Server uses different auth than browser Empire")
        print("   - Need to use GNIP token auth instead")

async def main():
    account = load_account()
    if account:
        print(f"📂 Using saved account: {account['name']}")
        await test_connection(account['username'], account['password'])
    else:
        print("⚠️  No saved account found.")
        print("   Go to Dashboard → Accounts tab and add your account first!")
        print("   OR enter credentials directly below:\n")
        username = input("Game username: ").strip()
        password = input("Game password: ").strip()
        await test_connection(username, password)

if __name__ == "__main__":
    asyncio.run(main())
