"""
Coherent browser persona profiles for stealth visiting.

Each profile bundles a real user-agent string with matching viewport,
device scale factor, platform, and default language — ensuring no
fingerprint contradictions that detection systems look for.

UA Staleness Tracking:
    Chrome and Firefox release new major versions roughly every 4-6 weeks.
    Run `python personas.py` directly to check whether the UA strings in
    this file are likely stale and need a manual update.
"""

import random
import time
import logging
import json
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Last time the UA strings below were verified against real releases.
# Update this date whenever you refresh the UA strings.
# ──────────────────────────────────────────────────────────────
UA_LAST_VERIFIED = "2026-04-16"

# Chrome and Firefox release cycles in days (approximate)
CHROME_RELEASE_CYCLE_DAYS = 28
FIREFOX_RELEASE_CYCLE_DAYS = 28

# How many days past the release cycle before we warn
STALENESS_GRACE_DAYS = 14

# Current major versions embedded in the UAs below
EMBEDDED_CHROME_VERSION = 131
EMBEDDED_FIREFOX_VERSION = 134

# ──────────────────────────────────────────────────────────────
# 15 coherent persona profiles
# ──────────────────────────────────────────────────────────────

PERSONA_PROFILES = [
    # ── Windows + Chrome (most common combo) ────────────────
    {
        "id": "win-chrome-1080p",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "device_scale_factor": 1,
        "platform": "Win32",
        "languages": ["en-US", "en"],
    },
    {
        "id": "win-chrome-768p",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1366, "height": 768},
        "device_scale_factor": 1,
        "platform": "Win32",
        "languages": ["en-US", "en"],
    },
    {
        "id": "win-chrome-864p",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1536, "height": 864},
        "device_scale_factor": 1.25,
        "platform": "Win32",
        "languages": ["en-US", "en"],
    },
    {
        "id": "win-chrome-1440p",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 2560, "height": 1440},
        "device_scale_factor": 1,
        "platform": "Win32",
        "languages": ["en-US", "en"],
    },
    {
        "id": "win11-chrome-1080p",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "device_scale_factor": 1.5,
        "platform": "Win32",
        "languages": ["en-US", "en"],
    },

    # ── macOS + Chrome ──────────────────────────────────────
    {
        "id": "mac-chrome-retina",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1440, "height": 900},
        "device_scale_factor": 2,
        "platform": "MacIntel",
        "languages": ["en-US", "en"],
    },
    {
        "id": "mac-chrome-1440p",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 2560, "height": 1440},
        "device_scale_factor": 2,
        "platform": "MacIntel",
        "languages": ["en-US", "en"],
    },
    {
        "id": "mac-chrome-13inch",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1280, "height": 800},
        "device_scale_factor": 2,
        "platform": "MacIntel",
        "languages": ["en-US", "en"],
    },

    # ── Windows + Firefox ───────────────────────────────────
    {
        "id": "win-firefox-768p",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
        "viewport": {"width": 1366, "height": 768},
        "device_scale_factor": 1,
        "platform": "Win32",
        "languages": ["en-US", "en"],
    },
    {
        "id": "win-firefox-1080p",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
        "viewport": {"width": 1920, "height": 1080},
        "device_scale_factor": 1,
        "platform": "Win32",
        "languages": ["en-US", "en"],
    },

    # ── macOS + Safari ──────────────────────────────────────
    {
        "id": "mac-safari-retina",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
        "viewport": {"width": 1440, "height": 900},
        "device_scale_factor": 2,
        "platform": "MacIntel",
        "languages": ["en-US", "en"],
    },
    {
        "id": "mac-safari-13inch",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
        "viewport": {"width": 1280, "height": 800},
        "device_scale_factor": 2,
        "platform": "MacIntel",
        "languages": ["en-US", "en"],
    },

    # ── Linux + Chrome ──────────────────────────────────────
    {
        "id": "linux-chrome-1080p",
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "device_scale_factor": 1,
        "platform": "Linux x86_64",
        "languages": ["en-US", "en"],
    },

    # ── Canadian English profiles ───────────────────────────
    {
        "id": "win-chrome-canada",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "device_scale_factor": 1,
        "platform": "Win32",
        "languages": ["en-CA", "en", "fr-CA"],
    },
    {
        "id": "win-firefox-canada",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
        "viewport": {"width": 1366, "height": 768},
        "device_scale_factor": 1,
        "platform": "Win32",
        "languages": ["en-CA", "en", "fr-CA"],
    },
]


def get_random_persona(timezone_id=None, locale_override=None):
    """
    Select a random persona profile with slight viewport jitter.

    Args:
        timezone_id: IANA timezone string to embed (e.g. 'America/New_York').
                     If None, no timezone is set on the profile.
        locale_override: Override the profile's default language list.
                         Pass a list like ['en-CA', 'fr-CA'].

    Returns:
        A dict with all browser context parameters ready to use.
    """
    profile = random.choice(PERSONA_PROFILES)
    # Deep copy to avoid mutating the original
    persona = {
        "id": profile["id"],
        "user_agent": profile["user_agent"],
        "viewport": {
            "width": profile["viewport"]["width"] + random.choice([-10, 0, 0, 0, 10]),
            "height": profile["viewport"]["height"] + random.choice([-5, 0, 0, 0, 5]),
        },
        "device_scale_factor": profile["device_scale_factor"],
        "platform": profile["platform"],
        "languages": locale_override if locale_override else list(profile["languages"]),
    }

    if timezone_id:
        persona["timezone_id"] = timezone_id

    return persona


def check_ua_staleness():
    """
    Check if the embedded UA strings are likely stale.

    Returns:
        A dict with 'is_stale', 'days_since_verified', 'message'.
    """
    verified = datetime.strptime(UA_LAST_VERIFIED, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    days_elapsed = (now - verified).days
    threshold = max(CHROME_RELEASE_CYCLE_DAYS, FIREFOX_RELEASE_CYCLE_DAYS) + STALENESS_GRACE_DAYS

    is_stale = days_elapsed > threshold

    if is_stale:
        message = (
            f"⚠️  UA strings are likely STALE.\n"
            f"   Last verified: {UA_LAST_VERIFIED} ({days_elapsed} days ago)\n"
            f"   Staleness threshold: {threshold} days\n"
            f"   Embedded Chrome: {EMBEDDED_CHROME_VERSION}, Firefox: {EMBEDDED_FIREFOX_VERSION}\n"
            f"\n"
            f"   To update:\n"
            f"   1. Check https://www.whatismybrowser.com/guides/the-latest-user-agent/chrome\n"
            f"   2. Check https://www.whatismybrowser.com/guides/the-latest-user-agent/firefox\n"
            f"   3. Update UA strings in personas.py\n"
            f"   4. Update UA_LAST_VERIFIED, EMBEDDED_CHROME_VERSION, EMBEDDED_FIREFOX_VERSION"
        )
    else:
        remaining = threshold - days_elapsed
        message = (
            f"✅ UA strings are fresh.\n"
            f"   Last verified: {UA_LAST_VERIFIED} ({days_elapsed} days ago)\n"
            f"   Next check recommended in ~{remaining} days\n"
            f"   Embedded Chrome: {EMBEDDED_CHROME_VERSION}, Firefox: {EMBEDDED_FIREFOX_VERSION}"
        )

    return {
        "is_stale": is_stale,
        "days_since_verified": days_elapsed,
        "message": message,
    }


# ──────────────────────────────────────────────────────────────
# CLI: Run `python personas.py` to check UA staleness
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = check_ua_staleness()
    print(result["message"])
    print()
    print(f"Total profiles available: {len(PERSONA_PROFILES)}")
    print("Profile IDs:")
    for p in PERSONA_PROFILES:
        print(f"  - {p['id']}")
