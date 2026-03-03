"""
utils.py — Human-mimicry helpers and safe extraction utilities.
"""

import asyncio
import random

from config import SCROLL_RANGE, SCROLL_PAUSE, SCROLL_STEPS


async def human_scroll(page) -> None:
    """
    Scroll the page in random increments to simulate a human reading
    through search results.
    """
    steps = random.randint(*SCROLL_STEPS)
    for _ in range(steps):
        distance = random.randint(*SCROLL_RANGE)
        await page.mouse.wheel(0, distance)
        await asyncio.sleep(random.uniform(*SCROLL_PAUSE))


async def random_delay(lo: float, hi: float) -> None:
    """Async sleep for a random duration between *lo* and *hi* seconds."""
    delay = random.uniform(lo, hi)
    print(f"  [delay] Waiting {delay:.1f}s ...")
    await asyncio.sleep(delay)


def safe_text(locator) -> str:
    """Return the inner text of a locator, or '' on any failure."""
    try:
        return locator.inner_text().strip()
    except Exception:
        return ""


def safe_attr(locator, attr: str) -> str:
    """Return an attribute value from a locator, or '' on any failure."""
    try:
        val = locator.get_attribute(attr)
        return val.strip() if val else ""
    except Exception:
        return ""
