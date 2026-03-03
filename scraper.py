"""
scraper.py — LinkedIn Profile Scraper via Google Dorking.

Instead of searching LinkedIn directly (which hides profiles outside your
network), this scraper uses Google with  site:linkedin.com/in/  queries
to find profile names, titles, and URLs.

Uses Playwright with stealth to automate a real browser.
"""

import csv
import os
import re
import asyncio
import urllib.parse
import threading

from playwright.async_api import async_playwright, Page, BrowserContext
from playwright_stealth import Stealth

from config import (
    MAX_RESULTS_PER_SEARCH,
    INTER_COMPANY_DELAY,
    INTER_ROLE_DELAY,
    OUTPUT_CSV,
    BROWSER_DATA_DIR,
)
from utils import human_scroll, random_delay

# Regex: a valid LinkedIn profile path like /in/john-doe-123
_PROFILE_RE = re.compile(r'/in/[\w-]{3,}', re.IGNORECASE)


def _clean_profile_link(raw: str) -> str:
    """
    Return a clean, full LinkedIn profile URL or '' if invalid.
    Rejects paths like /search, /feed, /jobs, etc.
    """
    if not raw:
        return ""
    raw = raw.split("?")[0].split("#")[0]
    m = _PROFILE_RE.search(raw)
    if not m:
        return ""
    path = m.group(0)
    return f"https://www.linkedin.com{path}"


class LinkedInScraper:
    """Scrapes LinkedIn profiles via Google search (no LinkedIn login needed)."""

    def __init__(self):
        self.total_extracted: int = 0
        self.results: list[dict] = []
        self._paused = False
        self._pause_lock = threading.Event()
        self._pause_lock.set()

    # ── pause / resume ─────────────────────────────────────────────
    def _start_keyboard_listener(self) -> None:
        """Background thread: press P in the CMD window to pause/resume."""
        def _listener():
            while True:
                try:
                    key = input()
                except EOFError:
                    break
                if key.strip().lower() == "p":
                    if self._paused:
                        self._paused = False
                        self._pause_lock.set()
                        print("\n  >>  RESUMED — scraping continues.\n")
                    else:
                        self._paused = True
                        self._pause_lock.clear()
                        print("\n  ||  PAUSED — press P + Enter again to resume.\n")

        t = threading.Thread(target=_listener, daemon=True)
        t.start()

    async def _check_pause(self) -> None:
        if not self._pause_lock.is_set():
            print("  ||  Scraper is paused. Press P + Enter to resume...")
        while not self._pause_lock.is_set():
            await asyncio.sleep(0.5)

    # ── browser helpers ────────────────────────────────────────────
    async def _launch_context(self, playwright) -> BrowserContext:
        """Launch a persistent Chromium context with stealth patches."""
        os.makedirs(BROWSER_DATA_DIR, exist_ok=True)
        stealth = Stealth()
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=BROWSER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        for p in context.pages:
            await stealth.apply_stealth_async(p)
        context.on(
            "page",
            lambda p: asyncio.ensure_future(stealth.apply_stealth_async(p)),
        )
        return context

    # ── Google search & parse ──────────────────────────────────────
    async def _google_search(self, page: Page, company: str, role: str) -> list[dict]:
        """
        Google: site:linkedin.com/in/ "role" "company"
        Extract name, title snippet, and profile URL from results.
        """
        query = f'site:linkedin.com/in/ "{role}" "{company}"'
        google_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num={MAX_RESULTS_PER_SEARCH + 5}"

        print(f"  Searching Google: {query}")
        rows: list[dict] = []

        try:
            await page.goto(google_url, wait_until="domcontentloaded", timeout=20000)
        except Exception as exc:
            print(f"    [!] Navigation error: {exc}")
            return rows

        await asyncio.sleep(2)
        await human_scroll(page)

        # ── Check for CAPTCHA / consent ──
        try:
            body_text = await page.inner_text("body")
        except Exception:
            body_text = ""

        if "unusual traffic" in body_text.lower() or "captcha" in body_text.lower():
            print("    [!] Google CAPTCHA detected — please solve it in the browser.")
            print("        After solving, come back here and press ENTER.")
            await asyncio.get_event_loop().run_in_executor(None, input, "        Press ENTER to continue...")
            await asyncio.sleep(1)

        # Handle Google consent page ("Before you continue to Google")
        try:
            consent_btn = page.locator('button:has-text("Accept all"), button:has-text("Reject all"), button:has-text("I agree")').first
            if await consent_btn.count() > 0:
                await consent_btn.click()
                await asyncio.sleep(2)
        except Exception:
            pass

        # ── Parse Google results (link-first approach) ──
        await asyncio.sleep(1)

        # Find all anchors pointing to linkedin.com/in/
        all_links = page.locator('a[href*="linkedin.com/in/"]')
        link_count = await all_links.count()
        print(f"    Found {link_count} LinkedIn link(s) on page")

        if link_count == 0:
            all_links = page.locator('a[href*="/in/"]')
            link_count = await all_links.count()
            print(f"    Broader search: {link_count} /in/ link(s)")

        if link_count == 0:
            print("    [!] No LinkedIn links found on page.")
            try:
                html = await page.content()
                debug_path = os.path.join(os.path.dirname(__file__), "debug_page.html")
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"    [debug] Page HTML saved to {debug_path}")
            except Exception:
                pass
            return rows

        seen_links: set[str] = set()

        for i in range(link_count):
            if len(rows) >= MAX_RESULTS_PER_SEARCH:
                break

            a_el = all_links.nth(i)

            try:
                href = await a_el.get_attribute("href") or ""
            except Exception:
                continue

            link = _clean_profile_link(href)
            if not link or link in seen_links:
                continue
            seen_links.add(link)

            # ── Extract name from the link's text or nested h3 ──
            name = ""
            try:
                h3_inside = a_el.locator('h3')
                if await h3_inside.count() > 0:
                    raw = (await h3_inside.first.inner_text()).strip()
                    parts = re.split(r'\s*[-–—|]\s*', raw)
                    name = parts[0].strip()
                    if name.lower() in ("linkedin", ""):
                        name = parts[1].strip() if len(parts) > 1 else ""
            except Exception:
                pass

            if not name:
                try:
                    link_text = (await a_el.inner_text()).strip()
                    if link_text and "linkedin" not in link_text.lower():
                        parts = re.split(r'\s*[-–—|]\s*', link_text)
                        name = parts[0].strip()
                except Exception:
                    pass

            # ── Extract snippet/title from nearby text ──
            title = ""
            try:
                parent = a_el.locator('xpath=ancestor::div[contains(@class,"g") or contains(@class,"tF2Cxc") or contains(@class,"MjjYud") or @data-hveid][1]')
                if await parent.count() > 0:
                    for snip_sel in ['div.VwiC3b', 'span.aCOpRe', 'div[data-sncf]', 'div.IsZvec', 'span.st']:
                        snip_el = parent.locator(snip_sel).first
                        if await snip_el.count() > 0:
                            title = (await snip_el.inner_text()).strip()
                            if title:
                                if len(title) > 200:
                                    title = title[:200] + "..."
                                break
            except Exception:
                pass

            print(f"      [{len(rows)+1}] {name or '(no name)'} | {title[:60] + '...' if len(title) > 60 else title} | {link}")

            rows.append({
                "Company": company,
                "Target Role": role,
                "Employee Name": name,
                "Employee Title": title,
                "Profile Link": link,
            })

        return rows

    # ── CSV writer ─────────────────────────────────────────────────
    def _write_rows_to_csv(self, rows: list[dict]) -> None:
        """Append a batch of rows to the output CSV immediately."""
        if not rows:
            return
        file_exists = os.path.exists(OUTPUT_CSV)
        fieldnames = [
            "Company", "Target Role", "Employee Name",
            "Employee Title", "Profile Link",
        ]
        with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            writer.writerows(rows)

    # ── main entry point ───────────────────────────────────────────
    async def run(self, companies: list[str], roles: list[str]) -> None:
        """
        For each company × role, Google-dork for LinkedIn profiles and
        save results to CSV after every search.
        """
        self._start_keyboard_listener()
        print("Tip: Press P + Enter at any time to PAUSE / RESUME the scraper.\n")

        async with async_playwright() as pw:
            context = await self._launch_context(pw)
            page = context.pages[0] if context.pages else await context.new_page()

            for idx, company in enumerate(companies):
                print(f"\n{'='*60}")
                print(f"  Company [{idx+1}/{len(companies)}]: {company}")
                print(f"{'='*60}")

                for role in roles:
                    await self._check_pause()
                    rows = await self._google_search(page, company, role)

                    for row in rows:
                        self.results.append(row)
                        self.total_extracted += 1

                    self._write_rows_to_csv(rows)

                    print(f"\n    ** Results so far: {self.total_extracted} profile(s) | Saved to: {OUTPUT_CSV}")
                    print(f"    {'─'*50}")

                    await random_delay(*INTER_ROLE_DELAY)

                if idx < len(companies) - 1:
                    print(f"\n  [cooldown] Waiting between companies ...")
                    await random_delay(*INTER_COMPANY_DELAY)

            await context.close()

        if self.total_extracted > 0:
            print(f"\n{'='*60}")
            print(f"  DONE! {self.total_extracted} profile(s) saved to {OUTPUT_CSV}")
            print(f"{'='*60}")
        else:
            print("\nNo results extracted.")
