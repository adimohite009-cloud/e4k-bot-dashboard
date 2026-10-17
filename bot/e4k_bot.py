#!/usr/bin/env python3
# ============================================================
# bot/e4k_bot.py — Empire: Four Kingdoms Automation Bot
#
# Uses the ggxs library to connect to GGE servers via WebSocket.
# No emulator needed — pure API / game protocol calls.
#
# Features:
#   - login()               : Authenticate with game credentials
#   - attack_robber_barons(): Find and attack RB castles
#   - recruit_troops()      : Auto-recruit troops based on config
#   - recruit_tools()       : Auto-craft siege tools
#   - run_event_samurai()   : Automate Samurai event
#   - run_event_nomads()    : Automate Nomads event
#   - Human-like random delays between all actions
#   - Reads settings.json every cycle
#   - Writes stats.json and logs after every action
# ============================================================

import json
import os
import random
import time
import threading
from datetime import datetime

# Anti-detection: import our 5-layer bypass system
# (graceful fallback if the file somehow isn't present)
try:
    from bot.anti_detection import AntiDetection
    _AD_AVAILABLE = True
except ImportError:
    try:
        from anti_detection import AntiDetection
        _AD_AVAILABLE = True
    except ImportError:
        _AD_AVAILABLE = False

# ────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────
STATS_FILE        = "stats.json"
LOG_FILE          = "logs/attack_log.txt"
SETTINGS_FILE     = "settings.json"
ACCOUNTS_FILE     = "accounts.json"
RECRUIT_FILE      = "recruit_config.json"
TOOLS_FILE        = "tools_config.json"
EVENTS_FILE       = "events_config.json"
STOP_SIGNAL_FILE  = "stop.signal"
TRIGGER_FILE      = "manual_attack.trigger"

# Troop IDs as used in the game API
TROOP_IDS = {
    "swordsman":   1,
    "bowman":      2,
    "cavalry":     3,
    "crossbowman": 4,
    "catapult":    5,
    "knight":      6,
    "longbow":     7,
    "ballista":    8,
    "trebuchet":   9,
}

# Tool IDs as used in the game API
TOOL_IDS = {
    "ladders":      1,
    "shields":      2,
    "rams":         3,
    "mantlets":     4,
    "siege_towers": 5,
}


# ────────────────────────────────────────────────────────────
# Logging helpers
# ────────────────────────────────────────────────────────────
def log(message: str):
    """Write a timestamped log line."""
    os.makedirs("logs", exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ────────────────────────────────────────────────────────────
# Stats helpers
# ────────────────────────────────────────────────────────────
def read_stats() -> dict:
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "running": False,
        "attacks_sent": 0,
        "attacks_won": 0,
        "attacks_failed": 0,
        "troops_lost": 0,
        "uptime_seconds": 0,
        "last_attack": None,
        "last_target": None,
    }


def write_stats(stats: dict):
    os.makedirs("logs", exist_ok=True)
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def update_stat(key: str, delta=1):
    stats = read_stats()
    stats[key] = stats.get(key, 0) + delta
    write_stats(stats)


# ────────────────────────────────────────────────────────────
# Settings / config helpers
# ────────────────────────────────────────────────────────────
def load_settings() -> dict:
    defaults = {
        "game_server":     "e4k-live-int2-game.goodgamestudios.com",
        "zone":            "EmpirefourkingdomsExGG_21",
        "zone_id":         327,
        "player_id":       "16-72-21-8730956",
        "attack_interval": 120,
        "max_attacks":     30,
        "min_rb_level":    1,
        "max_rb_level":    15,
        "troop_type":      "swordsman",
        "troop_count":     500,
        "human_delay":     True,
        "write_stats":     True,
        "write_logs":      True,
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass
    return defaults


def load_active_account() -> dict | None:
    if not os.path.exists(ACCOUNTS_FILE):
        return None
    try:
        with open(ACCOUNTS_FILE) as f:
            accounts = json.load(f)
        for acc in accounts:
            if acc.get("active"):
                return acc
        return accounts[0] if accounts else None
    except Exception:
        return None


def load_recruit_config() -> dict:
    if os.path.exists(RECRUIT_FILE):
        try:
            with open(RECRUIT_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"enabled": False, "threshold": 5, "interval": 300, "troops": {}}


def load_tools_config() -> dict:
    if os.path.exists(TOOLS_FILE):
        try:
            with open(TOOLS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"enabled": False, "threshold": 3, "interval": 600, "tools": {}}


def load_events_config() -> dict:
    if os.path.exists(EVENTS_FILE):
        try:
            with open(EVENTS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "samurai": {"enabled": False, "mode": "auto", "level": 10, "daily_limit": 20},
        "nomads":  {"enabled": False, "min_level": 1, "max_level": 10, "daily_limit": 30, "troop": "cavalry"},
    }


# ────────────────────────────────────────────────────────────
# Human-like delay
# ────────────────────────────────────────────────────────────
def human_delay(min_s=2.0, max_s=8.0, settings=None):
    if settings and not settings.get("human_delay", True):
        return
    delay = random.uniform(min_s, max_s)
    log(f"⏳ Waiting {delay:.1f}s (human delay)…")
    time.sleep(delay)


def stop_requested() -> bool:
    return os.path.exists(STOP_SIGNAL_FILE)


def trigger_requested() -> bool:
    if os.path.exists(TRIGGER_FILE):
        try:
            os.remove(TRIGGER_FILE)
        except Exception:
            pass
        return True
    return False


# ────────────────────────────────────────────────────────────
# E4K Bot Class
# ────────────────────────────────────────────────────────────
class E4KBot:
    """
    Main automation bot for Empire: Four Kingdoms.
    Uses the ggxs library to connect without an emulator.
    """

    def __init__(self):
        self.client = None          # ggxs client instance
        self.logged_in = False
        self.session_start = time.time()
        self.settings = load_settings()
        self.account = None

        # ── Anti-Detection System ──────────────────────────
        # Wraps all timing, rate-limiting, and behavioral
        # simulation to avoid triggering ban systems.
        if _AD_AVAILABLE:
            self.ad = AntiDetection()
            log("🛡️ Anti-detection system loaded (5-layer protection)")
        else:
            self.ad = None
            log("⚠️ Anti-detection module not found — using basic random delays")

    # ──────────────────────────────────────────────────────
    # Login
    # ──────────────────────────────────────────────────────
    def login(self) -> bool:
        """Authenticate with the game server using the active account credentials."""
        self.account = load_active_account()
        if not self.account:
            log("❌ No active account found! Add an account in the Accounts tab.")
            return False

        username = self.account.get("username", "")
        password = self.account.get("password", "")
        server   = self.account.get("server", "INT2")
        log(f"🔑 Logging in as {username} on {server}…")

        try:
            # Try importing ggxs (the Goodgame Empire WebSocket library)
            import ggxs  # type: ignore

            self.settings = load_settings()
            game_server = self.settings.get("game_server", "e4k-live-int2-game.goodgamestudios.com")
            zone        = self.settings.get("zone", "EmpirefourkingdomsExGG_21")
            zone_id     = self.settings.get("zone_id", 327)
            player_id   = self.settings.get("player_id", "16-72-21-8730956")

            # Authenticate and connect
            self.client = ggxs.Client(
                server=game_server,
                zone=zone,
                zone_id=zone_id,
                player_id=player_id,
            )
            self.client.login(username=username, password=password)
            self.logged_in = True

            # Update account last_login
            if os.path.exists(ACCOUNTS_FILE):
                try:
                    with open(ACCOUNTS_FILE) as f:
                        accounts = json.load(f)
                    for acc in accounts:
                        if acc.get("username") == username:
                            acc["last_login"] = datetime.now().isoformat()
                            acc["status"] = "connected"
                    with open(ACCOUNTS_FILE, "w") as f:
                        json.dump(accounts, f, indent=2)
                except Exception:
                    pass

            log(f"✅ Logged in successfully as {username}")
            return True

        except ImportError:
            log("⚠️ ggxs library not installed — running in SIMULATION mode")
            log("   Install with: pip install ggxs")
            self.logged_in = True   # simulation mode
            return True

        except Exception as e:
            log(f"❌ Login failed: {e}")
            self.logged_in = False
            return False

    # ──────────────────────────────────────────────────────
    # Attack Robber Barons
    # ──────────────────────────────────────────────────────
    def attack_robber_barons(self) -> bool:
        """Find and attack a Robber Baron castle on the world map."""
        if not self.logged_in:
            log("❌ Not logged in — skipping attack")
            return False

        self.settings = load_settings()
        min_level   = self.settings.get("min_rb_level", 1)
        max_level   = self.settings.get("max_rb_level", 15)
        troop_type  = self.settings.get("troop_type", "swordsman")
        troop_count = self.settings.get("troop_count", 500)
        troop_id    = TROOP_IDS.get(troop_type, 1)

        log(f"🔍 Searching for Robber Baron castles (level {min_level}–{max_level})…")
        human_delay(1.5, 4.0, self.settings)

        try:
            if self.client:
                # Real ggxs call — scan world map for RB castles
                targets = self.client.scan_map(
                    object_type="robber_baron",
                    min_level=min_level,
                    max_level=max_level,
                )

                if not targets:
                    log("📍 No Robber Baron targets found on current map area")
                    return False

                target = targets[0]
                target_pos = target.get("position", "unknown")
                target_lvl = target.get("level", "?")
                log(f"🎯 Found RB Level {target_lvl} at position {target_pos}")

                human_delay(2.0, 5.0, self.settings)

                # Send attack
                result = self.client.attack(
                    target_id=target.get("id"),
                    troop_type=troop_id,
                    troop_count=troop_count,
                )

                if result.get("success"):
                    log(f"✅ Attack sent to RB Lv.{target_lvl} at {target_pos}")
                    stats = read_stats()
                    stats["attacks_sent"]  = stats.get("attacks_sent", 0) + 1
                    stats["last_attack"]   = datetime.now().isoformat()
                    stats["last_target"]   = f"RB Lv.{target_lvl} @ {target_pos}"
                    if result.get("won"):
                        stats["attacks_won"] = stats.get("attacks_won", 0) + 1
                        log("🏆 Attack WON!")
                    else:
                        stats["attacks_failed"] = stats.get("attacks_failed", 0) + 1
                    write_stats(stats)
                    return True
                else:
                    err = result.get("error", "unknown error")
                    log(f"❌ Attack failed: {err}")
                    update_stat("attacks_failed")
                    return False

            else:
                # Simulation mode
                target_lvl = random.randint(min_level, max_level)
                target_pos = f"({random.randint(100,500)}, {random.randint(100,500)})"
                log(f"🎮 [SIM] Attacking RB Level {target_lvl} at {target_pos}…")
                human_delay(1.0, 3.0, self.settings)
                won = random.random() > 0.3

                stats = read_stats()
                stats["attacks_sent"]  = stats.get("attacks_sent", 0) + 1
                stats["last_attack"]   = datetime.now().isoformat()
                stats["last_target"]   = f"RB Lv.{target_lvl} @ {target_pos}"
                if won:
                    stats["attacks_won"] = stats.get("attacks_won", 0) + 1
                    log(f"✅ [SIM] Attack WON! RB Lv.{target_lvl} defeated")
                else:
                    stats["attacks_failed"] = stats.get("attacks_failed", 0) + 1
                    log(f"❌ [SIM] Attack FAILED. RB Lv.{target_lvl} held off")
                write_stats(stats)
                return won

        except Exception as e:
            log(f"❌ Attack error: {e}")
            update_stat("attacks_failed")
            return False

    # ──────────────────────────────────────────────────────
    # Recruit Troops
    # ──────────────────────────────────────────────────────
    def recruit_troops(self, config: dict = None) -> bool:
        """Queue troop recruitment based on config."""
        if config is None:
            config = load_recruit_config()

        if not config.get("enabled", False):
            return False

        troops_config = config.get("troops", {})
        selected = {k: v for k, v in troops_config.items() if v.get("enabled")}

        if not selected:
            log("🪖 No troops selected for recruitment")
            return False

        log(f"🪖 Starting troop recruitment ({len(selected)} types selected)…")
        human_delay(1.0, 3.0, self.settings)

        recruited = []
        for troop_name, troop_cfg in selected.items():
            qty = troop_cfg.get("qty", 100)
            troop_id = TROOP_IDS.get(troop_name, 1)
            try:
                if self.client:
                    result = self.client.recruit(troop_type=troop_id, count=qty)
                    if result.get("success"):
                        log(f"✅ Queued {qty}x {troop_name.capitalize()}")
                        recruited.append(f"{qty}x {troop_name}")
                    else:
                        log(f"⚠️ Could not recruit {troop_name}: {result.get('error','unknown')}")
                else:
                    log(f"🎮 [SIM] Queued {qty}x {troop_name.capitalize()}")
                    recruited.append(f"{qty}x {troop_name}")

                human_delay(0.5, 2.0, self.settings)

            except Exception as e:
                log(f"❌ Recruit error ({troop_name}): {e}")

        if recruited:
            log(f"✅ Recruitment queued: {', '.join(recruited)}")
        return bool(recruited)

    # ──────────────────────────────────────────────────────
    # Recruit Tools
    # ──────────────────────────────────────────────────────
    def recruit_tools(self, config: dict = None) -> bool:
        """Queue siege tool crafting based on config."""
        if config is None:
            config = load_tools_config()

        if not config.get("enabled", False):
            return False

        tools_config = config.get("tools", {})
        selected = {k: v for k, v in tools_config.items() if v.get("enabled")}

        if not selected:
            log("🔨 No tools selected for crafting")
            return False

        log(f"🔨 Starting tool crafting ({len(selected)} types selected)…")
        human_delay(1.0, 3.0, self.settings)

        crafted = []
        for tool_name, tool_cfg in selected.items():
            qty = tool_cfg.get("qty", 10)
            tool_id = TOOL_IDS.get(tool_name, 1)
            try:
                if self.client:
                    result = self.client.craft_tool(tool_type=tool_id, count=qty)
                    if result.get("success"):
                        log(f"✅ Crafted {qty}x {tool_name.replace('_',' ').capitalize()}")
                        crafted.append(f"{qty}x {tool_name}")
                    else:
                        log(f"⚠️ Could not craft {tool_name}: {result.get('error','unknown')}")
                else:
                    log(f"🎮 [SIM] Crafted {qty}x {tool_name.replace('_',' ').capitalize()}")
                    crafted.append(f"{qty}x {tool_name}")

                human_delay(0.5, 2.0, self.settings)

            except Exception as e:
                log(f"❌ Craft error ({tool_name}): {e}")

        if crafted:
            log(f"✅ Tools crafted: {', '.join(crafted)}")
        return bool(crafted)

    # ──────────────────────────────────────────────────────
    # Samurai Event
    # ──────────────────────────────────────────────────────
    def run_event_samurai(self, config: dict = None) -> bool:
        """Automate the Samurai event."""
        if config is None:
            config = load_events_config().get("samurai", {})

        if not config.get("enabled", False):
            return False

        mode        = config.get("mode", "auto")
        target_lvl  = config.get("level", 10)
        daily_limit = config.get("daily_limit", 20)

        log(f"🥷 Running Samurai event (mode={mode}, level={target_lvl})…")
        human_delay(2.0, 5.0, self.settings)

        try:
            if self.client:
                # Get available samurai stages
                stages = self.client.get_event_stages("samurai")
                if not stages:
                    log("⚠️ No Samurai stages available")
                    return False

                if mode == "auto":
                    stage = stages[-1]  # highest available
                else:
                    stage = next((s for s in stages if s.get("level") == target_lvl), stages[-1])

                result = self.client.attack_event(
                    event_type="samurai",
                    stage_id=stage.get("id"),
                )
                if result.get("success"):
                    log(f"✅ Samurai event stage cleared: Level {stage.get('level','?')}")
                    return True
                else:
                    log(f"⚠️ Samurai attack failed: {result.get('error','unknown')}")
                    return False
            else:
                lvl = target_lvl if mode == "manual" else random.randint(8, 15)
                log(f"🎮 [SIM] Samurai event — cleared Level {lvl}")
                return True

        except Exception as e:
            log(f"❌ Samurai event error: {e}")
            return False

    # ──────────────────────────────────────────────────────
    # Nomads Event
    # ──────────────────────────────────────────────────────
    def run_event_nomads(self, config: dict = None) -> bool:
        """Automate the Nomads event."""
        if config is None:
            config = load_events_config().get("nomads", {})

        if not config.get("enabled", False):
            return False

        min_level   = config.get("min_level", 1)
        max_level   = config.get("max_level", 10)
        daily_limit = config.get("daily_limit", 30)
        troop_type  = config.get("troop", "cavalry")
        troop_id    = TROOP_IDS.get(troop_type, 3)

        log(f"🏕️ Running Nomads event (level {min_level}–{max_level}, troop={troop_type})…")
        human_delay(2.0, 5.0, self.settings)

        try:
            if self.client:
                camps = self.client.scan_map(
                    object_type="nomad_camp",
                    min_level=min_level,
                    max_level=max_level,
                )
                if not camps:
                    log("⚠️ No Nomad camps found in range")
                    return False

                camp = camps[0]
                result = self.client.attack(
                    target_id=camp.get("id"),
                    troop_type=troop_id,
                    troop_count=200,
                )
                if result.get("success"):
                    log(f"✅ Nomad camp attacked at {camp.get('position','?')}")
                    return True
                else:
                    log(f"⚠️ Nomad attack failed: {result.get('error','unknown')}")
                    return False
            else:
                lvl = random.randint(min_level, max_level)
                pos = f"({random.randint(100,500)}, {random.randint(100,500)})"
                log(f"🎮 [SIM] Attacked Nomad camp Lv.{lvl} at {pos}")
                return True

        except Exception as e:
            log(f"❌ Nomads event error: {e}")
            return False

    # ──────────────────────────────────────────────────────
    # Main loop
    # ──────────────────────────────────────────────────────
    def run(self):
        """Main bot loop — runs until stop signal or crash."""
        log("🚀 E4K Bot starting up…")
        self.settings = load_settings()

        # Login
        if not self.login():
            log("❌ Failed to login — exiting bot")
            return

        # Mark as running
        stats = read_stats()
        stats["running"] = True
        stats["session_start"] = datetime.now().isoformat()
        write_stats(stats)

        log("✅ Bot is running! Entering main loop…")
        attacks_this_session = 0

        last_recruit_time = 0.0
        last_tool_time    = 0.0
        last_event_time   = 0.0

        while True:
            # ── Stop check ─────────────────────────────────
            if stop_requested():
                log("⏹ Stop signal detected — shutting down bot")
                try:
                    os.remove(STOP_SIGNAL_FILE)
                except Exception:
                    pass
                break

            # Reload settings each cycle
            self.settings = load_settings()
            attack_interval = self.settings.get("attack_interval", 120)
            max_attacks     = self.settings.get("max_attacks", 30)

            # ── Manual trigger check ────────────────────────
            if trigger_requested():
                log("⚔️ Manual attack trigger received!")
                self.attack_robber_barons()
                attacks_this_session += 1
                human_delay(2.0, 5.0, self.settings)
                continue

            # ── Max attacks check ───────────────────────────
            if attacks_this_session >= max_attacks:
                log(f"🏁 Reached max attacks ({max_attacks}) for this session")
                break

            # ── Auto-attack RBs ─────────────────────────────
            # Anti-detection: check rate limits before attacking.
            # If we've attacked too many times this hour it will
            # pause here automatically until safe to continue.
            if self.ad:
                self.ad.pre_action_check("attack")
            self.attack_robber_barons()
            if self.ad:
                self.ad.post_action("attack")
            attacks_this_session += 1

            # ── Recruit troops (periodic) ───────────────────
            recruit_cfg  = load_recruit_config()
            recruit_ivl  = recruit_cfg.get("interval", 300)
            if recruit_cfg.get("enabled") and (time.time() - last_recruit_time) >= recruit_ivl:
                self.recruit_troops(recruit_cfg)
                last_recruit_time = time.time()

            # ── Recruit tools (periodic) ────────────────────
            tools_cfg    = load_tools_config()
            tools_ivl    = tools_cfg.get("interval", 600)
            if tools_cfg.get("enabled") and (time.time() - last_tool_time) >= tools_ivl:
                self.recruit_tools(tools_cfg)
                last_tool_time = time.time()

            # ── Events (every 300s) ─────────────────────────
            events_cfg = load_events_config()
            if (time.time() - last_event_time) >= 300:
                if events_cfg.get("samurai", {}).get("enabled"):
                    self.run_event_samurai(events_cfg["samurai"])
                    human_delay(1.0, 3.0, self.settings)
                if events_cfg.get("nomads", {}).get("enabled"):
                    self.run_event_nomads(events_cfg["nomads"])
                    human_delay(1.0, 3.0, self.settings)
                last_event_time = time.time()

            # ── Update uptime in stats ──────────────────────
            stats = read_stats()
            stats["uptime_seconds"] = int(time.time() - self.session_start)
            write_stats(stats)

            # ── Wait before next attack ─────────────────────
            # Use the anti-detection timer if available —
            # it applies Gaussian noise, fatigue, and time-of-day
            # factors to make our timing look human.
            if self.ad:
                wait_secs = self.ad.timer.get_attack_interval(attack_interval)
            else:
                wait_secs = attack_interval + random.uniform(-20, 20)
                wait_secs = max(60, wait_secs)

            log(f"⏱️ Waiting {wait_secs:.0f}s before next attack… ({attacks_this_session}/{max_attacks} done)")
            deadline = time.time() + wait_secs
            while time.time() < deadline:
                if stop_requested() or trigger_requested():
                    break
                time.sleep(5)

        # Clean up
        stats = read_stats()
        stats["running"] = False
        write_stats(stats)
        log("🛑 Bot stopped.")


# ────────────────────────────────────────────────────────────
# Entry point
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bot = E4KBot()
    bot.run()
