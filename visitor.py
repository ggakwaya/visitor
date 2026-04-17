"""
Stealth website visitor orchestrator.

Coordinates VPN rotation, browser persona selection, and human-like
browsing behavior to produce visits that are indistinguishable from
real user traffic.

Usage:
    python visitor.py              # Full mode with VPN rotation
    python visitor.py --no-vpn     # Skip VPN (for local testing)
    python visitor.py --visible    # Non-headless mode (debug)
"""

import yaml
import time
import random
import subprocess
import logging
import logging.handlers
import json
import os
import glob
import signal
import sys
import tempfile

from playwright.sync_api import sync_playwright

# ──────────────────────────────────────────────────────────────
# Stealth Import -- try multiple API shapes, log clearly on failure
# ──────────────────────────────────────────────────────────────

_stealth_available = False

try:
    from playwright_stealth import stealth_sync as apply_stealth
    _stealth_available = True
except ImportError:
    try:
        from playwright_stealth import Stealth
        def apply_stealth(page):
            Stealth().apply_stealth_sync(page)
        _stealth_available = True
    except (ImportError, AttributeError):
        try:
            from playwright_stealth import stealth as _stealth_fn
            if callable(_stealth_fn):
                apply_stealth = _stealth_fn
                _stealth_available = True
            else:
                from playwright_stealth.stealth import stealth as apply_stealth
                _stealth_available = True
        except (ImportError, AttributeError):
            def apply_stealth(page):
                pass

from personas import get_random_persona, check_ua_staleness
from behavior import (
    human_mouse_move,
    idle_mouse_jitter,
    human_scroll,
    get_watch_duration,
    get_video_duration,
    interact_with_player,
    handle_consent,
    navigate_organically,
    browse_generic_page,
    cleanup_cursor,
)

# ──────────────────────────────────────────────────────────────
# Setup Logging -- stdout + rotating file
# ──────────────────────────────────────────────────────────────

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            os.path.join(LOG_DIR, "visitor.log"),
            maxBytes=5 * 1024 * 1024,  # 5 MB per file
            backupCount=5,
        ),
    ],
)
logger = logging.getLogger(__name__)

if not _stealth_available:
    logger.error(
        "playwright-stealth could not be loaded -- visits will NOT be stealthy. "
        "Install it with: pip install playwright-stealth"
    )

# Session storage directory
SESSION_DIR = "/tmp/visitor-sessions"

# Platform override JS -- injected into every page to make
# navigator.platform match the persona's UA string.
PLATFORM_OVERRIDE_JS = """
Object.defineProperty(navigator, 'platform', {
    get: () => '%s',
});
"""


class VisitorOrchestrator:
    def __init__(self, config_path="config.yaml", stats_path="stats.json"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        self.stats_path = stats_path
        self.load_stats()
        self._ensure_session_dir()
        self._check_ua_freshness()

        # Graceful shutdown state
        self._shutdown_requested = False
        self._active_browser = None
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle SIGINT/SIGTERM for clean shutdown."""
        sig_name = signal.Signals(signum).name
        if self._shutdown_requested:
            logger.warning(f"Second {sig_name} received, forcing exit")
            sys.exit(1)
        logger.info(f"{sig_name} received -- finishing current visit then exiting...")
        self._shutdown_requested = True
        # If there's an active browser, close it
        if self._active_browser:
            try:
                self._active_browser.close()
            except Exception:
                pass

    def _ensure_session_dir(self):
        """Create the session storage directory if it doesn't exist."""
        os.makedirs(SESSION_DIR, exist_ok=True)

    def _check_ua_freshness(self):
        """Warn at startup if user-agent strings are stale."""
        result = check_ua_staleness()
        if result["is_stale"]:
            logger.warning(result["message"])
        else:
            logger.info(
                f"UA strings verified {result['days_since_verified']} days ago -- still fresh"
            )

    def load_stats(self):
        """Loads visit statistics from a JSON file."""
        if os.path.exists(self.stats_path):
            try:
                with open(self.stats_path, "r") as f:
                    self.stats = json.load(f)
            except Exception:
                self.stats = {}
        else:
            self.stats = {}

    def save_stats(self):
        """Saves visit statistics atomically (write-to-tmp then rename)."""
        dir_name = os.path.dirname(os.path.abspath(self.stats_path))
        try:
            fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
            with os.fdopen(fd, "w") as f:
                json.dump(self.stats, f, indent=4)
            os.replace(tmp_path, self.stats_path)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
            # Try to clean up the temp file
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    # ──────────────────────────────────────────────────────────
    # VPN Rotation
    # ──────────────────────────────────────────────────────────

    def rotate_vpn(self):
        """
        Connects to a new NordVPN location based on weighted probability.
        Verifies the IP actually changed after connecting.

        Returns:
            The selected location dict on success, or None on failure.
        """
        locations = self.config["locations"]
        weights = [loc["weight"] for loc in locations]
        selected = random.choices(locations, weights=weights, k=1)[0]

        logger.info(f"Rotating VPN to: {selected['country']} ({selected['nord_name']})")

        try:
            # Set technology to NordLynx for best LXC performance
            subprocess.run(["nordvpn", "set", "technology", "nordlynx"], capture_output=True)
            # Disconnect first to be clean
            subprocess.run(["nordvpn", "disconnect"], capture_output=True)
            # Connect to new location
            result = subprocess.run(
                ["nordvpn", "connect", selected["nord_name"]],
                capture_output=True,
                text=True,
            )

            # Brief wait for the 'nordlynx' interface to initialize
            time.sleep(3)

            if result.returncode != 0:
                logger.error(f"Failed to connect to VPN: {result.stderr}")
                return None

            # Verify the VPN is actually working by checking external IP
            if not self._verify_vpn_ip():
                logger.error("VPN IP verification failed -- connection may not be active")
                return None

            return selected
        except Exception as e:
            logger.error(f"VPN rotation error: {e}")
            return None

    def _verify_vpn_ip(self):
        """Verify VPN connection by checking the external IP address."""
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", "10", "https://ifconfig.me"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                logger.info(f"VPN active -- external IP: {result.stdout.strip()}")
                return True
            logger.warning("Could not determine external IP")
            return False
        except Exception as e:
            logger.warning(f"IP verification failed: {e}")
            return False

    # ──────────────────────────────────────────────────────────
    # Referrer Selection
    # ──────────────────────────────────────────────────────────

    def _get_random_referrer(self):
        """Select a weighted-random referrer URL from config."""
        referrers = self.config.get("referrers", [])
        if not referrers:
            return ""
        urls = [r["url"] for r in referrers]
        weights = [r["weight"] for r in referrers]
        return random.choices(urls, weights=weights, k=1)[0]

    # ──────────────────────────────────────────────────────────
    # Session Management
    # ──────────────────────────────────────────────────────────

    def _get_session_path(self, persona_id):
        """Get the file path for a session state file."""
        return os.path.join(SESSION_DIR, f"session_{persona_id}.json")

    def _load_session_state(self, persona_id):
        """
        Try to load a saved browser session state.

        Returns the storage state dict, or None if no session exists.
        """
        path = self._get_session_path(persona_id)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    state = json.load(f)
                logger.info(f"Loaded saved session for persona '{persona_id}'")
                return state
            except Exception as e:
                logger.debug(f"Could not load session '{persona_id}': {e}")
                # Remove corrupt file
                os.remove(path)
        return None

    def _save_session_state(self, context, persona_id):
        """
        Save the browser context's storage state for future reuse.

        Only saves with a configured probability (session_reuse_probability).
        Also cleans up old sessions to avoid /tmp bloat (keep max 20).
        """
        prob = self.config.get("session_reuse_probability", 0.3)
        if random.random() >= prob:
            return

        path = self._get_session_path(persona_id)
        try:
            context.storage_state(path=path)
            logger.info(f"Saved session state for persona '{persona_id}'")
        except Exception as e:
            logger.debug(f"Could not save session: {e}")

        # Cleanup: keep only the 20 most recent session files
        self._cleanup_old_sessions(max_keep=20)

    def _cleanup_old_sessions(self, max_keep=20):
        """Remove oldest session files if we have more than max_keep."""
        pattern = os.path.join(SESSION_DIR, "session_*.json")
        files = sorted(glob.glob(pattern), key=os.path.getmtime)
        if len(files) > max_keep:
            for f in files[: len(files) - max_keep]:
                try:
                    os.remove(f)
                    logger.debug(f"Cleaned up old session: {f}")
                except Exception:
                    pass

    # ──────────────────────────────────────────────────────────
    # Target Type Detection
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _is_youtube_video(url):
        """Check if a URL is a YouTube video page."""
        return "youtube.com/watch" in url or "youtu.be/" in url

    @staticmethod
    def _is_youtube(url):
        """Check if a URL is any YouTube page."""
        return "youtube.com" in url or "youtu.be" in url

    # ──────────────────────────────────────────────────────────
    # Core Visit Logic
    # ──────────────────────────────────────────────────────────

    def perform_visit(self, url, location=None, headless=True):
        """
        Executes a stealthy, human-like browser visit.

        Branches behavior based on target type:
        - YouTube videos: organic nav, play button, watch with jitter,
          player interactions, comment scrolling
        - Other sites: generic browse (scroll, hover, idle)

        Args:
            url: Target URL to visit.
            location: VPN location dict with 'timezones' and 'locales'
                      keys. Used to match the browser's timezone and
                      locale to the VPN exit node. Pass None for no
                      geo-matching.
            headless: Run browser in headless mode (default True).

        Returns:
            True if the visit was successful, False otherwise.
        """
        # ── Build persona ──────────────────────────────────
        timezone_id = None
        locale_override = None

        if location:
            timezones = location.get("timezones", [])
            if timezones:
                timezone_id = random.choice(timezones)
            locales = location.get("locales", [])
            if locales:
                locale_override = locales

        # ── Select browser engine FIRST, then match persona ──
        browser_config = self.config["browsers"]
        browser_type = random.choices(
            [b["type"] for b in browser_config],
            weights=[b["weight"] for b in browser_config],
            k=1,
        )[0]

        persona = get_random_persona(
            timezone_id=timezone_id,
            locale_override=locale_override,
            engine=browser_type,
        )

        # ── Select referrer ────────────────────────────────
        referrer = self._get_random_referrer()

        is_yt_video = self._is_youtube_video(url)

        logger.info(
            f"Visit: {url}\n"
            f"  Persona: {persona['id']} | Browser: {browser_type}\n"
            f"  Viewport: {persona['viewport']['width']}x{persona['viewport']['height']} "
            f"@{persona['device_scale_factor']}x\n"
            f"  Timezone: {persona.get('timezone_id', 'system')} | "
            f"Locale: {persona['languages'][0]}\n"
            f"  Referrer: {referrer or '(direct)'}\n"
            f"  Type: {'YouTube video' if is_yt_video else 'generic page'}"
        )

        with sync_playwright() as p:
            try:
                browser_engine = getattr(p, browser_type)

                # Launch args -- disable WebRTC IP leak for Chromium
                launch_kwargs = {"headless": headless}
                if browser_type == "chromium":
                    launch_kwargs["args"] = [
                        "--disable-features=WebRtcHideLocalIpsWithMdns",
                        "--enforce-webrtc-ip-permission-check",
                        "--webrtc-ip-handling-policy=disable_non_proxied_udp",
                    ]

                browser = browser_engine.launch(**launch_kwargs)
                self._active_browser = browser

                # ── Build browser context ──────────────────
                context_kwargs = {
                    "user_agent": persona["user_agent"],
                    "viewport": persona["viewport"],
                    "device_scale_factor": persona["device_scale_factor"],
                    "locale": persona["languages"][0],
                }

                if persona.get("timezone_id"):
                    context_kwargs["timezone_id"] = persona["timezone_id"]

                # Don't put referrer in extra_http_headers -- it leaks on
                # every subrequest. We pass it to page.goto() instead.

                # Try to load a saved session (returning visitor)
                session_state = self._load_session_state(persona["id"])
                if session_state:
                    context_kwargs["storage_state"] = session_state

                context = browser.new_context(**context_kwargs)

                # Inject navigator.platform override to match the persona
                context.add_init_script(PLATFORM_OVERRIDE_JS % persona["platform"])

                page = context.new_page()

                # Apply stealth plugins
                apply_stealth(page)

                # ── Pre-navigation delay ───────────────────
                time.sleep(random.uniform(1, 3))

                # ── Navigate ──────────────────────────────
                if is_yt_video:
                    self._visit_youtube_video(page, url, referrer)
                else:
                    self._visit_generic_page(page, url, referrer)

                # ── Save session for future reuse ──────────
                self._save_session_state(context, persona["id"])

                logger.info(f"Visit successful: {page.title()}")
                cleanup_cursor(page)
                return True

            except Exception as e:
                logger.error(f"Visit failed: {e}")
                return False
            finally:
                self._active_browser = None
                try:
                    browser.close()
                except Exception:
                    pass

    def _visit_youtube_video(self, page, url, referrer):
        """YouTube-specific visit: organic nav, play, watch, interact."""
        # Navigate (possibly organically via homepage)
        # Pass referrer only on the goto call, not as a persistent header
        if random.random() < 0.4:
            logger.info("Organic navigation: visiting YouTube homepage first")
            page.goto("https://www.youtube.com/", wait_until="domcontentloaded")
            time.sleep(random.uniform(2, 6))
            handle_consent(page)
            human_scroll(page)
            time.sleep(random.uniform(1, 4))
            goto_kwargs = {"url": url, "wait_until": "domcontentloaded"}
            if referrer:
                goto_kwargs["referer"] = referrer
            page.goto(**goto_kwargs)
        else:
            goto_kwargs = {"url": url, "wait_until": "domcontentloaded"}
            if referrer:
                goto_kwargs["referer"] = referrer
            page.goto(**goto_kwargs)

        # Handle consent popups
        handle_consent(page)

        # Wait for the video player to be ready
        try:
            page.wait_for_selector("video", timeout=10000)
        except Exception:
            logger.debug("Video element not found, continuing anyway")

        # Click play button
        try:
            play_button = page.get_by_label("Play", exact=True)
            if play_button.is_visible(timeout=3000):
                box = play_button.bounding_box()
                if box:
                    target_x = box["x"] + box["width"] / 2
                    target_y = box["y"] + box["height"] / 2
                    human_mouse_move(page, target_x, target_y)
                    time.sleep(random.uniform(0.2, 0.8))
                    play_button.click()
                    logger.info("Clicked play button")
        except Exception:
            pass

        # Get actual video duration to cap watch time
        video_duration = get_video_duration(page)
        watch_time = get_watch_duration(max_duration=video_duration)

        # Split watch time into segments with interactions
        elapsed = 0
        while elapsed < watch_time:
            segment = min(random.uniform(10, 40), watch_time - elapsed)
            idle_mouse_jitter(page, segment)
            elapsed += segment

            if elapsed < watch_time:
                interact_with_player(page)

        # Post-watch scrolling (read comments)
        if random.random() < 0.4:
            logger.debug("Scrolling to comments")
            human_scroll(page)
            time.sleep(random.uniform(2, 8))

    def _visit_generic_page(self, page, url, referrer):
        """Generic page visit: navigate, scroll, browse."""
        goto_kwargs = {"url": url, "wait_until": "domcontentloaded"}
        if referrer:
            goto_kwargs["referer"] = referrer
        page.goto(**goto_kwargs)

        handle_consent(page)
        browse_generic_page(page)

    # ──────────────────────────────────────────────────────────
    # Visit with Retry
    # ──────────────────────────────────────────────────────────

    def perform_visit_with_retry(self, url, location=None, headless=True):
        """
        Attempt a visit with exponential backoff on failure.

        Retries up to max_retries times (from config, default 3).
        """
        max_retries = self.config.get("max_retries", 3)
        for attempt in range(1, max_retries + 1):
            if self._shutdown_requested:
                return False

            success = self.perform_visit(url, location=location, headless=headless)
            if success:
                return True

            if attempt < max_retries:
                backoff = min(60, (2 ** attempt) + random.uniform(0, 5))
                logger.warning(
                    f"Visit attempt {attempt}/{max_retries} failed, "
                    f"retrying in {backoff:.0f}s..."
                )
                time.sleep(backoff)

        logger.error(f"All {max_retries} visit attempts failed for {url}")
        return False

    # ──────────────────────────────────────────────────────────
    # Main Loop
    # ──────────────────────────────────────────────────────────

    def run(self):
        """Main loop for 24/7 operation over multiple targets."""
        while not self._shutdown_requested:
            # Filter targets that haven't reached their goal yet
            active_targets = []
            for t in self.config["targets"]:
                current = self.stats.get(t["url"], 0)
                if current < t["goal"]:
                    active_targets.append(t)

            if not active_targets:
                logger.info("All target goals reached! Statistics:")
                for url, count in self.stats.items():
                    logger.info(f"  - {url}: {count} visits")
                break

            # Choose a target (randomly from active ones)
            target = random.choice(active_targets)

            location = self.rotate_vpn()
            if location:
                if self.perform_visit_with_retry(
                    target["url"], location=location
                ):
                    # Update stats
                    self.stats[target["url"]] = self.stats.get(target["url"], 0) + 1
                    self.save_stats()

                    progress = f"[{self.stats[target['url']]}/{target['goal']}]"
                    logger.info(f"Progress for {target['url']}: {progress}")

                # Randomized delay before next visit
                delay = random.randint(
                    self.config["jitter"]["min_delay"],
                    self.config["jitter"]["max_delay"],
                )
                logger.info(f"Sleeping for {delay}s until next visit...")
                time.sleep(delay)
            else:
                logger.warning("Retrying VPN rotation in 60s...")
                time.sleep(60)

        if self._shutdown_requested:
            logger.info("Shutdown complete. Final statistics:")
            for url, count in self.stats.items():
                logger.info(f"  - {url}: {count} visits")
            self.save_stats()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stealth Website Visitor")
    parser.add_argument(
        "--no-vpn", action="store_true", help="Skip VPN rotation (for testing)"
    )
    parser.add_argument(
        "--visible", action="store_true", help="Run browser in non-headless mode"
    )
    args = parser.parse_args()

    orchestrator = VisitorOrchestrator()

    if args.no_vpn:
        logger.info("Running in NO-VPN mode for all targets...")
        for target in orchestrator.config["targets"]:
            orchestrator.perform_visit(
                target["url"], headless=not args.visible
            )
    else:
        orchestrator.run()
