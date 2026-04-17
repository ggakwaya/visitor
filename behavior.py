"""
Human behavior simulation for stealth browser visits.

This module provides functions that mimic real human interaction patterns:
- Bezier-curve mouse movement (not linear) with persistent cursor tracking
- Idle jitter (hand resting on mouse while watching)
- Variable-speed scrolling with occasional scroll-back
- Weighted watch duration distribution
- YouTube player interactions (hover, fullscreen)
- Cookie consent banner handling
- Organic multi-step navigation (arrive via homepage, not direct)
- Generic website browsing behavior (for non-YouTube targets)
"""

import math
import time
import random
import logging

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Cursor State -- tracks the last known mouse position per page
# ──────────────────────────────────────────────────────────────

_cursor_positions = {}


def _get_cursor(page):
    """Get the current cursor position for a page, or a plausible default."""
    page_id = id(page)
    if page_id in _cursor_positions:
        return _cursor_positions[page_id]
    viewport = page.viewport_size or {"width": 1920, "height": 1080}
    x = random.uniform(viewport["width"] * 0.3, viewport["width"] * 0.7)
    y = random.uniform(viewport["height"] * 0.3, viewport["height"] * 0.7)
    _cursor_positions[page_id] = (x, y)
    return (x, y)


def _set_cursor(page, x, y):
    """Update the tracked cursor position for a page."""
    _cursor_positions[id(page)] = (x, y)


def cleanup_cursor(page):
    """Remove cursor tracking for a page (call on page close)."""
    _cursor_positions.pop(id(page), None)


# ──────────────────────────────────────────────────────────────
# Mouse Movement
# ──────────────────────────────────────────────────────────────

def human_mouse_move(page, target_x, target_y, steps=None):
    """
    Move the mouse along a cubic Bezier curve with variable speed.

    Uses the tracked cursor position as the start point (not a random
    location), so consecutive moves form a continuous path.

    Args:
        page: Playwright page object.
        target_x: Target X coordinate.
        target_y: Target Y coordinate.
        steps: Number of steps (auto-calculated from distance if None).
    """
    start_x, start_y = _get_cursor(page)

    if steps is None:
        distance = math.hypot(target_x - start_x, target_y - start_y)
        steps = max(10, int(distance / random.uniform(5, 15)))

    # Random control points for the Bezier curve
    cp1_x = start_x + random.uniform(-150, 150)
    cp1_y = start_y + random.uniform(-150, 150)
    cp2_x = target_x + random.uniform(-80, 80)
    cp2_y = target_y + random.uniform(-80, 80)

    for i in range(steps + 1):
        t = i / steps
        # Cubic Bezier interpolation
        x = ((1 - t) ** 3 * start_x
             + 3 * (1 - t) ** 2 * t * cp1_x
             + 3 * (1 - t) * t ** 2 * cp2_x
             + t ** 3 * target_x)
        y = ((1 - t) ** 3 * start_y
             + 3 * (1 - t) ** 2 * t * cp1_y
             + 3 * (1 - t) * t ** 2 * cp2_y
             + t ** 3 * target_y)

        page.mouse.move(x, y)
        # Variable speed: slower near the target (deceleration)
        time.sleep(random.uniform(0.004, 0.018) * (1 + t * 0.5))

    _set_cursor(page, target_x, target_y)
    logger.debug(f"Mouse moved to ({target_x}, {target_y}) in {steps} steps")


def idle_mouse_jitter(page, duration_seconds):
    """
    Simulate subtle mouse movements while the user is watching content.

    Real humans don't hold a mouse perfectly still. Their hand rests on
    it, causing tiny occasional shifts. This function alternates between
    long pauses (watching) and small gaussian-distributed nudges.

    Args:
        page: Playwright page object.
        duration_seconds: How long to jitter for (seconds).
    """
    end_time = time.time() + duration_seconds
    viewport = page.viewport_size or {"width": 1920, "height": 1080}

    current_x, current_y = _get_cursor(page)

    while time.time() < end_time:
        # Long pause -- person is watching the video
        pause = random.uniform(3, 20)
        time.sleep(min(pause, max(0, end_time - time.time())))

        if time.time() >= end_time:
            break

        # Decide what to do: mostly nothing, sometimes jitter, rarely a bigger move
        action = random.random()

        if action < 0.6:
            # Tiny jitter -- hand vibration on the mouse (sigma=3px)
            dx = random.gauss(0, 3)
            dy = random.gauss(0, 3)
            current_x = max(0, min(viewport["width"], current_x + dx))
            current_y = max(0, min(viewport["height"], current_y + dy))
            page.mouse.move(current_x, current_y)

        elif action < 0.85:
            # Slightly bigger drift -- repositioning hand (sigma=15px)
            dx = random.gauss(0, 15)
            dy = random.gauss(0, 15)
            current_x = max(0, min(viewport["width"], current_x + dx))
            current_y = max(0, min(viewport["height"], current_y + dy))
            page.mouse.move(current_x, current_y)

        # else: do absolutely nothing (hand is off the mouse)

    _set_cursor(page, current_x, current_y)


# ──────────────────────────────────────────────────────────────
# Scrolling
# ──────────────────────────────────────────────────────────────

def human_scroll(page):
    """
    Scroll down the page in variable increments with natural pauses.

    Includes occasional scroll-back (15% chance per step) and stops at
    a random depth between 30-70% of the total page height.

    Args:
        page: Playwright page object.
    """
    try:
        total = page.evaluate("document.body.scrollHeight")
    except Exception:
        logger.debug("Could not get scroll height, skipping scroll")
        return

    target_depth = total * random.uniform(0.3, 0.7)
    current = 0

    while current < target_depth:
        delta = random.randint(50, 300)
        page.mouse.wheel(0, delta)
        current += delta
        time.sleep(random.uniform(0.3, 2.0))

        # Occasionally scroll back up slightly
        if random.random() < 0.15:
            back = random.randint(20, 100)
            page.mouse.wheel(0, -back)
            current -= back
            time.sleep(random.uniform(0.5, 1.5))

    logger.debug(f"Scrolled to ~{current}px / {total}px total")


# ──────────────────────────────────────────────────────────────
# Watch Duration
# ──────────────────────────────────────────────────────────────

def get_watch_duration(max_duration=None):
    """
    Generate a watch duration from a weighted distribution that mimics
    real viewer behavior, optionally capped by the actual video length.

    Distribution:
        15%  ->  8-20s   (quick bounce -- not interested)
        45%  -> 30-90s   (medium engagement -- typical casual viewer)
        25%  -> 90-240s  (good engagement -- interested viewer)
        15%  -> 240-600s (deep watcher -- very engaged)

    Args:
        max_duration: If set, cap the result to this value (e.g. video length).

    Returns:
        Watch duration in seconds (float).
    """
    r = random.random()
    if r < 0.15:
        duration = random.uniform(8, 20)
    elif r < 0.60:
        duration = random.uniform(30, 90)
    elif r < 0.85:
        duration = random.uniform(90, 240)
    else:
        duration = random.uniform(240, 600)

    if max_duration and duration > max_duration:
        # Cap but add slight jitter so it doesn't always stop at exactly max
        duration = max_duration * random.uniform(0.85, 1.0)

    logger.info(f"Watch duration: {duration:.1f}s" +
                (f" (capped from video length {max_duration:.0f}s)" if max_duration and duration >= max_duration * 0.84 else ""))
    return duration


# ──────────────────────────────────────────────────────────────
# YouTube Player Interactions
# ──────────────────────────────────────────────────────────────

def interact_with_player(page):
    """
    Perform occasional in-player interactions during playback.

    Actions (weighted):
        70% -- do nothing (most natural)
        15% -- hover over the player area (triggers controls overlay)
         5% -- toggle fullscreen (press 'f')
         5% -- hover over the timeline/progress bar
         5% -- press space (pause/unpause, then immediately unpause)

    Args:
        page: Playwright page object.
    """
    viewport = page.viewport_size or {"width": 1920, "height": 1080}
    r = random.random()

    if r < 0.70:
        # Do nothing -- most people just watch
        return

    elif r < 0.85:
        # Hover over the player area
        player_x = random.randint(int(viewport["width"] * 0.15), int(viewport["width"] * 0.85))
        player_y = random.randint(int(viewport["height"] * 0.15), int(viewport["height"] * 0.50))
        human_mouse_move(page, player_x, player_y, steps=random.randint(8, 20))
        time.sleep(random.uniform(0.5, 2.0))
        logger.debug("Hovered over player")

    elif r < 0.90:
        # Toggle fullscreen
        page.keyboard.press("f")
        time.sleep(random.uniform(3, 10))
        page.keyboard.press("f")  # Exit fullscreen
        logger.debug("Toggled fullscreen")

    elif r < 0.95:
        # Hover over the progress bar (bottom of player)
        bar_x = random.randint(int(viewport["width"] * 0.1), int(viewport["width"] * 0.9))
        bar_y = int(viewport["height"] * 0.48)  # Near bottom of typical player area
        human_mouse_move(page, bar_x, bar_y, steps=random.randint(6, 15))
        time.sleep(random.uniform(0.3, 1.5))
        logger.debug("Hovered over progress bar")

    else:
        # Brief pause/unpause
        page.keyboard.press("Space")
        time.sleep(random.uniform(0.5, 2.0))
        page.keyboard.press("Space")
        logger.debug("Brief pause/unpause")


# ──────────────────────────────────────────────────────────────
# Cookie Consent
# ──────────────────────────────────────────────────────────────

def handle_consent(page):
    """
    Handle YouTube / Google cookie consent dialogs (GDPR).

    Tries multiple known selectors for the consent banner.
    Waits briefly and clicks "Accept all" if found.

    Args:
        page: Playwright page object.
    """
    consent_selectors = [
        # YouTube's consent dialog variants
        'button:has-text("Accept all")',
        'button:has-text("Accept All")',
        'button:has-text("Tout accepter")',       # French
        'button:has-text("Alle akzeptieren")',     # German
        'button:has-text("I agree")',
        'button[aria-label="Accept all"]',
        # Google consent frame
        '#yDmH0d button:has-text("Accept")',
    ]

    for selector in consent_selectors:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=2000):
                time.sleep(random.uniform(0.5, 2.0))
                btn.click()
                logger.info("Accepted cookie consent banner")
                time.sleep(random.uniform(0.5, 1.5))
                return True
        except Exception:
            continue

    logger.debug("No consent banner found (or already dismissed)")
    return False


# ──────────────────────────────────────────────────────────────
# Organic Navigation
# ──────────────────────────────────────────────────────────────

def navigate_organically(page, target_url, probability=0.4):
    """
    Optionally visit YouTube homepage first before navigating to the
    target video. This avoids every visit being a suspicious direct
    navigation.

    With `probability` chance, the function will:
    1. Go to youtube.com
    2. Scroll around briefly
    3. Then navigate to the actual target

    Otherwise, it navigates directly.

    Args:
        page: Playwright page object.
        target_url: The final target URL.
        probability: Chance of doing the organic path (0.0-1.0).
    """
    if "youtube.com" in target_url and random.random() < probability:
        logger.info("Organic navigation: visiting YouTube homepage first")
        page.goto("https://www.youtube.com/", wait_until="domcontentloaded")
        time.sleep(random.uniform(2, 6))

        # Handle consent on homepage if it appears
        handle_consent(page)

        # Scroll around the homepage
        human_scroll(page)
        time.sleep(random.uniform(1, 4))

        # Now navigate to the target
        page.goto(target_url, wait_until="domcontentloaded")
    else:
        page.goto(target_url, wait_until="domcontentloaded")


# ──────────────────────────────────────────────────────────────
# Generic Website Browsing
# ──────────────────────────────────────────────────────────────

def browse_generic_page(page):
    """
    Simulate realistic browsing behavior on a non-YouTube page.

    Actions: read the page (scroll), maybe click an internal link,
    hover over a few elements.

    Args:
        page: Playwright page object.
    """
    viewport = page.viewport_size or {"width": 1920, "height": 1080}

    # Initial reading pause
    time.sleep(random.uniform(2, 5))

    # Scroll through the page
    human_scroll(page)
    time.sleep(random.uniform(1, 4))

    # Maybe move the mouse to a few random points (reading/exploring)
    for _ in range(random.randint(1, 3)):
        target_x = random.randint(int(viewport["width"] * 0.1), int(viewport["width"] * 0.9))
        target_y = random.randint(int(viewport["height"] * 0.1), int(viewport["height"] * 0.7))
        human_mouse_move(page, target_x, target_y)
        time.sleep(random.uniform(0.5, 3.0))

    # Idle on the page for a bit
    idle_mouse_jitter(page, random.uniform(5, 30))

    logger.debug("Finished generic page browsing")


def get_video_duration(page):
    """
    Try to extract the video duration from a YouTube page.

    Returns:
        Duration in seconds, or None if it cannot be determined.
    """
    try:
        duration = page.evaluate("""
            () => {
                const el = document.querySelector('video');
                if (el && el.duration && isFinite(el.duration)) return el.duration;
                return null;
            }
        """)
        if duration:
            logger.debug(f"Detected video duration: {duration:.0f}s")
        return duration
    except Exception:
        return None
