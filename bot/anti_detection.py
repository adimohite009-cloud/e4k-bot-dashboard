# ============================================================
# bot/anti_detection.py — Bot Detection Bypass System
#
# Implements all known countermeasures against E4K's
# 5 main detection methods:
#
#   1. Randomized timing (no fixed intervals)
#   2. Behavioral simulation (idle time, fake browsing)
#   3. Realistic session fingerprinting
#   4. Tracking event spoofing (mimics real client)
#   5. Action rate limiting (never exceed human limits)
# ============================================================

import random
import time
import math
import json
import os
import requests
from datetime import datetime, timedelta


# ============================================================
# 1. SMART RANDOMIZED TIMING
#    Never attack on a fixed schedule — humans are unpredictable
# ============================================================

class HumanTimer:
    """
    Generates human-like timing patterns.

    Real players:
    - Are faster at some times of day (morning coffee = focused)
    - Are slower at others (tired at night = long pauses)
    - Take random breaks (bathroom, phone call, distraction)
    - Never perfectly repeat the same interval
    """

    def __init__(self):
        self.action_count  = 0
        self.session_start = datetime.now()
        self.last_break    = datetime.now()
        self.fatigue_level = 0.0   # 0.0 = fresh, 1.0 = very tired

    def get_attack_interval(self, base_interval: int) -> float:
        """
        Returns a randomized attack interval based on:
        - Base interval from settings (e.g. 120s)
        - Gaussian noise (±25%)
        - Fatigue factor (slower over time)
        - Time of day (slower at night)
        """
        # Gaussian noise around the base interval
        noise = random.gauss(0, base_interval * 0.15)

        # Fatigue: gets slower as session goes on
        fatigue_factor = 1.0 + (self.fatigue_level * 0.4)

        # Time-of-day factor (1.0 = normal, 1.5 = night slowdown)
        hour = datetime.now().hour
        if 0 <= hour < 6:
            tod_factor = 1.5   # very late night — very slow
        elif 6 <= hour < 9:
            tod_factor = 1.1   # early morning
        elif 9 <= hour < 22:
            tod_factor = 1.0   # normal day
        else:
            tod_factor = 1.2   # late evening

        interval = (base_interval + noise) * fatigue_factor * tod_factor

        # Never go below 60s (would look robotic if too fast)
        interval = max(60, interval)

        # Random spike — sometimes humans take much longer
        if random.random() < 0.08:  # 8% chance of a long pause
            interval += random.uniform(60, 300)

        self._update_fatigue()
        return round(interval, 1)

    def _update_fatigue(self):
        """Increase fatigue over time, reset on break."""
        self.action_count += 1
        # Fatigue increases with actions
        self.fatigue_level = min(1.0, self.fatigue_level + 0.02)
        # Naturally recover a tiny bit
        minutes_since_start = (datetime.now() - self.session_start).seconds / 60
        if minutes_since_start > 60:
            self.fatigue_level = min(1.0, self.fatigue_level + 0.01)

    def micro_delay(self):
        """
        Tiny delay between sub-actions (like clicking a button).
        Real humans take 200-1500ms between clicks.
        """
        time.sleep(random.uniform(0.2, 1.5))

    def typing_delay(self, text_length: int):
        """Simulate realistic typing speed (40-80 WPM)."""
        chars_per_second = random.uniform(4, 10)  # 40-80 WPM
        time.sleep(text_length / chars_per_second)

    def should_take_break(self) -> bool:
        """
        Returns True if the bot should take a human break.
        Breaks: 5-15 min every 30-90 min of play.
        """
        minutes_since_break = (datetime.now() - self.last_break).seconds / 60
        # After 30-90 minutes, take a break
        break_threshold = random.uniform(30, 90)
        return minutes_since_break >= break_threshold

    def take_break(self):
        """
        Simulate a human taking a break (5-15 minutes).
        During this time, the bot sends idle/heartbeat signals only.
        """
        break_minutes = random.uniform(5, 15)
        print(f"☕ Taking a human break for {break_minutes:.0f} minutes...")
        time.sleep(break_minutes * 60)
        self.last_break    = datetime.now()
        self.fatigue_level = max(0.0, self.fatigue_level - 0.3)  # refreshed!
        print("✅ Break over — resuming bot")

    def session_end_chance(self) -> bool:
        """
        Real players eventually log off.
        After 4-8 hours, high chance of ending session.
        """
        hours_played = (datetime.now() - self.session_start).seconds / 3600
        if hours_played < 4:
            return False
        # Probability of ending session increases after 4h
        prob = (hours_played - 4) * 0.15
        return random.random() < prob


# ============================================================
# 2. BEHAVIORAL SIMULATION
#    Fake idle activities to look like a real player
# ============================================================

class BehaviorSimulator:
    """
    Simulates realistic human browsing behavior between attacks.
    Sends fake UI interaction events to the tracking server.
    """

    # The game tracks every screen the player visits
    SCREENS = [
        "overview",
        "castle_interior",
        "world_map",
        "alliance_menu",
        "shop_menu",
        "castle_details",
        "barracks",
        "forge",
        "research_lab",
        "castle_wall",
        "throne_room",
        "event_menu",
    ]

    def __init__(self, player_id: str, session: requests.Session):
        self.player_id = player_id
        self.session   = session
        self.tracking_url = "https://e4k-client-tracking.goodgamestudios.com/clienttracker.php"

    def simulate_browsing(self, duration_seconds: float):
        """
        Simulate a player browsing menus for a given duration.
        Sends realistic screen-view events to tracking server.
        """
        end_time = time.time() + duration_seconds
        visited  = []

        while time.time() < end_time:
            # Pick a random screen to "visit"
            screen = random.choice(self.SCREENS)
            visited.append(screen)

            # Send tracking event (like real client does)
            self._send_screen_event(screen)

            # Spend realistic time on that screen (5-45 seconds)
            screen_time = random.uniform(5, 45)
            time.sleep(min(screen_time, end_time - time.time()))

        return visited

    def _send_screen_event(self, screen_name: str):
        """
        Send a client tracking event — exactly what the real game client sends.
        From our Fiddler capture: e4k-client-tracking.goodgamestudios.com
        """
        try:
            payload = {
                "player_id": self.player_id,
                "screen":    screen_name,
                "timestamp": int(time.time() * 1000),
                "session":   id(self),
                "platform":  "android",
                "version":   "4143095",
            }
            self.session.post(
                self.tracking_url,
                json=payload,
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
        except Exception:
            pass  # tracking failures are silent — don't break bot

    def simulate_typing_in_chat(self):
        """Simulate typing something in alliance chat (realistic behavior)."""
        messages = [
            "anyone need help?",
            "going for RB farm",
            "nice castle",
            "gg",
            "attacking now",
        ]
        msg = random.choice(messages)
        time.sleep(random.uniform(2, 8))  # think before typing


# ============================================================
# 3. REALISTIC SESSION FINGERPRINTING
#    Make our HTTP session look like a real Android game client
# ============================================================

class SessionFactory:
    """
    Creates HTTP sessions that look like a real E4K Android client.
    The game checks User-Agent, headers, and cookie patterns.
    """

    # Real Android game client User-Agents (rotate these)
    USER_AGENTS = [
        "Dalvik/2.1.0 (Linux; U; Android 11; SM-G991B Build/RP1A.200720.012)",
        "Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/SD1A.210817.036)",
        "Dalvik/2.1.0 (Linux; U; Android 11; OnePlus 9 Build/RKQ1.201022.002)",
        "Dalvik/2.1.0 (Linux; U; Android 13; SM-S908B Build/TP1A.220624.014)",
        "Dalvik/2.1.0 (Linux; U; Android 12; POCO X4 Pro Build/SKQ1.211006.001)",
    ]

    @classmethod
    def create(cls) -> requests.Session:
        """Create a realistic game client HTTP session."""
        session = requests.Session()

        # Pick a random device to impersonate
        ua = random.choice(cls.USER_AGENTS)

        session.headers.update({
            "User-Agent":       ua,
            "Accept":           "application/json, text/plain, */*",
            "Accept-Language":  "en-US,en;q=0.9",
            "Accept-Encoding":  "gzip, deflate, br",
            "X-Requested-With": "com.goodgamestudios.empirefourkingdoms",
            "Connection":       "keep-alive",
            "Cache-Control":    "no-cache",
        })

        return session


# ============================================================
# 4. ACTION RATE LIMITER
#    Enforce human-realistic limits on actions per hour
# ============================================================

class RateLimiter:
    """
    Tracks actions per time period and enforces human-realistic limits.

    Human players in E4K typically:
    - Attack 10-30 times per hour (max)
    - Recruit 5-15 times per hour
    - Never exceed 60 total actions/hour
    """

    LIMITS = {
        "attacks_per_hour":  25,   # max RB attacks per hour
        "recruits_per_hour": 15,   # max recruitment actions per hour
        "total_per_hour":    60,   # max total actions per hour
        "attacks_per_day":   200,  # max per day (humans sleep!)
    }

    def __init__(self):
        self.actions = []   # list of (timestamp, action_type)

    def record(self, action_type: str):
        """Record an action."""
        self.actions.append((time.time(), action_type))
        # Clean old entries (> 24h)
        cutoff = time.time() - 86400
        self.actions = [(t, a) for t, a in self.actions if t > cutoff]

    def can_act(self, action_type: str) -> tuple[bool, str]:
        """
        Check if we can perform an action.
        Returns (allowed, reason_if_not).
        """
        now = time.time()
        one_hour_ago = now - 3600
        one_day_ago  = now - 86400

        hourly = [(t, a) for t, a in self.actions if t > one_hour_ago]
        daily  = [(t, a) for t, a in self.actions if t > one_day_ago]

        # Check hourly limits
        hourly_type = [a for t, a in hourly if a == action_type]
        limit_key   = f"{action_type}s_per_hour"

        if limit_key in self.LIMITS and len(hourly_type) >= self.LIMITS[limit_key]:
            return False, f"Hourly {action_type} limit reached ({self.LIMITS[limit_key]}/hr)"

        # Check total hourly
        if len(hourly) >= self.LIMITS["total_per_hour"]:
            return False, f"Total hourly action limit reached ({self.LIMITS['total_per_hour']}/hr)"

        # Check daily attack limit
        if action_type == "attack":
            daily_attacks = [a for t, a in daily if a == "attack"]
            if len(daily_attacks) >= self.LIMITS["attacks_per_day"]:
                return False, f"Daily attack limit reached ({self.LIMITS['attacks_per_day']}/day)"

        return True, ""

    def stats(self) -> dict:
        """Return current rate stats for dashboard display."""
        now = time.time()
        one_hour_ago = now - 3600
        hourly = [(t, a) for t, a in self.actions if t > one_hour_ago]
        return {
            "attacks_this_hour":  sum(1 for t, a in hourly if a == "attack"),
            "recruits_this_hour": sum(1 for t, a in hourly if a == "recruit"),
            "total_this_hour":    len(hourly),
        }


# ============================================================
# 5. ANTI-PATTERN SHUFFLER
#    Randomize the ORDER of actions so patterns can't be detected
# ============================================================

class ActionShuffler:
    """
    Real players don't always do things in the same order.
    This shuffles the bot's action sequence each cycle.
    """

    @staticmethod
    def get_action_order(attack_enabled: bool, recruit_enabled: bool,
                          tools_enabled: bool, events_enabled: bool) -> list:
        """
        Returns a shuffled list of actions to perform this cycle.
        Sometimes skips optional actions (like a real player would).
        """
        actions = []

        if attack_enabled:
            actions.append("attack")

        if recruit_enabled and random.random() > 0.15:  # skip 15% of the time
            actions.append("recruit_troops")

        if tools_enabled and random.random() > 0.20:    # skip 20% of the time
            actions.append("recruit_tools")

        if events_enabled and random.random() > 0.30:   # skip 30% of the time
            actions.append("event")

        # Sometimes insert a "browse" action (just wanders menus)
        if random.random() < 0.25:
            actions.insert(random.randint(0, len(actions)), "browse")

        # Shuffle — players don't always do things in the same order
        random.shuffle(actions)

        return actions


# ============================================================
# MAIN ANTI-DETECTION MANAGER
# Combine all systems into one easy-to-use class
# ============================================================

class AntiDetection:
    """
    Master anti-detection system. Use this in the bot main loop.

    Example usage:
        ad = AntiDetection(player_id="16-72-21-8730956")
        interval = ad.timer.get_attack_interval(120)
        ad.rate.record("attack")
        ok, reason = ad.rate.can_act("attack")
        ad.behavior.simulate_browsing(30)
    """

    def __init__(self, player_id: str):
        self.player_id = player_id
        self.timer     = HumanTimer()
        self.rate      = RateLimiter()
        self.session   = SessionFactory.create()
        self.behavior  = BehaviorSimulator(player_id, self.session)
        self.shuffler  = ActionShuffler()

    def pre_action_check(self, action_type: str) -> bool:
        """
        Run before every action. Returns True if safe to proceed.
        Handles: rate limiting, breaks, session end.
        """
        # Check rate limits
        allowed, reason = self.rate.can_act(action_type)
        if not allowed:
            print(f"⏸️  Rate limit: {reason} — waiting 10 minutes...")
            time.sleep(600)
            return False

        # Check if we should take a break
        if self.timer.should_take_break():
            # Browse menus during the break (looks natural)
            self.behavior.simulate_browsing(30)
            self.timer.take_break()

        # Random micro-delay before action (human reaction time)
        self.timer.micro_delay()
        return True

    def post_action(self, action_type: str):
        """Call after every action to record and update state."""
        self.rate.record(action_type)

    def get_cycle_actions(self, settings: dict) -> list:
        """Get the randomized action order for this cycle."""
        return self.shuffler.get_action_order(
            attack_enabled=settings.get("auto_attack", True),
            recruit_enabled=settings.get("auto_recruit", False),
            tools_enabled=settings.get("auto_tools", False),
            events_enabled=settings.get("auto_events", False),
        )

    def get_rate_stats(self) -> dict:
        return self.rate.stats()


if __name__ == "__main__":
    print("=== Anti-Detection System Test ===")
    ad = AntiDetection("16-72-21-8730956")

    print("\n📊 Action order this cycle:")
    settings = {"auto_attack": True, "auto_recruit": True,
                "auto_tools": True, "auto_events": True}
    for i in range(3):
        order = ad.get_cycle_actions(settings)
        print(f"  Cycle {i+1}: {' → '.join(order)}")

    print("\n⏱️  Sample attack intervals (base=120s):")
    for i in range(5):
        interval = ad.timer.get_attack_interval(120)
        print(f"  Attack {i+1}: wait {interval}s")

    print("\n✅ Anti-detection system ready!")
