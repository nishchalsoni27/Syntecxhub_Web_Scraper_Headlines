"""
================================================
  Web Scraper for Headlines
  Author  : Nishchal Soni
  Project : SyntecxHub – Project 2
  Date    : 2026-05-27
================================================
Features:
  • Fetch headlines from news websites (requests + BeautifulSoup)
  • Parse and display title, URL, and time (if available)
  • Save results to JSON or CSV
  • Respect robots.txt + delays and error handling
  • Filter by keyword + support multiple sources
"""

import requests
import csv
import json
import time
import random
import logging
import urllib.robotparser
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# News sources: list of dicts with scraping config
SOURCES = [
    {
        "name": "Hacker News",
        "url": "https://news.ycombinator.com/",
        "article_selector": ".athing",
        "title_selector": ".titleline > a",
        "link_attr": "href",
        "time_selector": None,   # HN shows age text, not datetime
    },
    {
        "name": "BBC News",
        "url": "https://www.bbc.com/news",
        "article_selector": "h3",
        "title_selector": None,   # title is the h3 itself
        "link_attr": None,
        "time_selector": "time",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; NishchalBot/1.0; "
        "+https://github.com/nishchalsoni/headline-scraper)"
    )
}

DELAY_MIN = 1.5   # seconds between requests
DELAY_MAX = 3.5


# ─────────────────────────────────────────────
# ROBOTS.TXT CHECKER
# ─────────────────────────────────────────────
def can_fetch(url: str, user_agent: str = "*") -> bool:
    """Return True if robots.txt permits crawling the given URL."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        allowed = rp.can_fetch(user_agent, url)
        if not allowed:
            logger.warning(f"robots.txt disallows: {url}")
        return allowed
    except Exception as e:
        logger.warning(f"Could not read robots.txt for {robots_url}: {e}")
        return True   # assume allowed if unreachable


# ─────────────────────────────────────────────
# FETCH PAGE
# ─────────────────────────────────────────────
def fetch_page(url: str, retries: int = 3) -> BeautifulSoup | None:
    """Fetch a URL with retries and return a BeautifulSoup object."""
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            logger.info(f"Fetched [{response.status_code}] {url}")
            return BeautifulSoup(response.text, "html.parser")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error on attempt {attempt}: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error on attempt {attempt}: {e}")
        except requests.exceptions.Timeout:
            logger.error(f"Timeout on attempt {attempt} for {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed on attempt {attempt}: {e}")

        if attempt < retries:
            sleep_time = 2 ** attempt + random.uniform(0, 1)
            logger.info(f"Retrying in {sleep_time:.1f}s …")
            time.sleep(sleep_time)

    logger.error(f"All {retries} attempts failed for {url}")
    return None


# ─────────────────────────────────────────────
# PARSE HEADLINES
# ─────────────────────────────────────────────
def parse_headlines(soup: BeautifulSoup, source_config: dict, base_url: str) -> list[dict]:
    """Extract headline dicts from a parsed page using source config."""
    headlines = []
    articles = soup.select(source_config["article_selector"])

    for article in articles:
        # ── Title ──────────────────────────────
        if source_config["title_selector"]:
            title_el = article.select_one(source_config["title_selector"])
        else:
            title_el = article  # element itself is the title container

        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            continue

        # ── URL ────────────────────────────────
        link = ""
        if source_config["link_attr"] and title_el:
            raw_link = title_el.get(source_config["link_attr"], "")
            link = urljoin(base_url, raw_link) if raw_link else ""
        else:
            # Try nearest <a> ancestor/descendant
            a_tag = article.find("a") if hasattr(article, "find") else None
            if a_tag:
                link = urljoin(base_url, a_tag.get("href", ""))

        # ── Time ───────────────────────────────
        timestamp = ""
        if source_config["time_selector"]:
            time_el = (
                article.select_one(source_config["time_selector"])
                or soup.select_one(source_config["time_selector"])
            )
            if time_el:
                timestamp = (
                    time_el.get("datetime")
                    or time_el.get_text(strip=True)
                )

        headlines.append({
            "title": title,
            "url": link,
            "time": timestamp,
            "source": source_config["name"],
            "scraped_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        })

    logger.info(f"  └─ {len(headlines)} headline(s) found from {source_config['name']}")
    return headlines


# ─────────────────────────────────────────────
# KEYWORD FILTER
# ─────────────────────────────────────────────
def filter_by_keyword(headlines: list[dict], keyword: str) -> list[dict]:
    """Return only headlines whose title contains the keyword (case-insensitive)."""
    kw = keyword.lower()
    filtered = [h for h in headlines if kw in h["title"].lower()]
    logger.info(f"Keyword '{keyword}': {len(filtered)}/{len(headlines)} match(es) kept.")
    return filtered


# ─────────────────────────────────────────────
# SAVE RESULTS
# ─────────────────────────────────────────────
def save_json(headlines: list[dict], filename: str = "headlines.json") -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(headlines, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(headlines)} headline(s) → {filename}")


def save_csv(headlines: list[dict], filename: str = "headlines.csv") -> None:
    if not headlines:
        logger.warning("No headlines to save.")
        return
    fields = list(headlines[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(headlines)
    logger.info(f"Saved {len(headlines)} headline(s) → {filename}")


# ─────────────────────────────────────────────
# DISPLAY
# ─────────────────────────────────────────────
def display_headlines(headlines: list[dict]) -> None:
    if not headlines:
        print("\n  (no headlines to display)\n")
        return
    print(f"\n{'═'*60}")
    for i, h in enumerate(headlines, 1):
        print(f"\n  [{i}] {h['title']}")
        if h["url"]:
            print(f"       URL  : {h['url']}")
        if h["time"]:
            print(f"       Time : {h['time']}")
        print(f"       Src  : {h['source']}  |  Scraped: {h['scraped_at']}")
    print(f"\n{'═'*60}\n")


# ─────────────────────────────────────────────
# MAIN SCRAPER
# ─────────────────────────────────────────────
def run_scraper(
    sources: list[dict] | None = None,
    keyword: str | None = None,
    output_format: str = "json",      # "json" | "csv" | "both"
    output_file: str = "headlines",
    max_per_source: int = 20,
) -> list[dict]:
    """
    Run the headline scraper.

    Args:
        sources       : List of source config dicts (defaults to SOURCES).
        keyword       : Optional keyword to filter headlines.
        output_format : "json", "csv", or "both".
        output_file   : Base filename (without extension).
        max_per_source: Max headlines to keep per source.

    Returns:
        List of headline dicts.
    """
    sources = sources or SOURCES
    all_headlines: list[dict] = []

    for source in sources:
        url = source["url"]
        logger.info(f"\n── Scraping: {source['name']} ({url})")

        if not can_fetch(url):
            logger.warning(f"Skipping {source['name']} (robots.txt disallows).")
            continue

        soup = fetch_page(url)
        if soup is None:
            continue

        headlines = parse_headlines(soup, source, base_url=url)
        headlines = headlines[:max_per_source]
        all_headlines.extend(headlines)

        # Polite delay between sources
        delay = random.uniform(DELAY_MIN, DELAY_MAX)
        logger.info(f"  Waiting {delay:.1f}s before next source …")
        time.sleep(delay)

    # Filter
    if keyword:
        all_headlines = filter_by_keyword(all_headlines, keyword)

    # Display
    display_headlines(all_headlines)

    # Save
    fmt = output_format.lower()
    if fmt in ("json", "both"):
        save_json(all_headlines, f"{output_file}.json")
    if fmt in ("csv", "both"):
        save_csv(all_headlines, f"{output_file}.csv")

    return all_headlines


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Web Scraper for Headlines — by Nishchal Soni"
    )
    parser.add_argument(
        "--keyword", "-k",
        type=str, default=None,
        help="Filter headlines by keyword (case-insensitive)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "csv", "both"],
        default="json",
        help="Output format (default: json)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str, default="headlines",
        help="Base output filename without extension (default: headlines)"
    )
    parser.add_argument(
        "--max", "-m",
        type=int, default=20,
        help="Max headlines per source (default: 20)"
    )
    args = parser.parse_args()

    run_scraper(
        keyword=args.keyword,
        output_format=args.format,
        output_file=args.output,
        max_per_source=args.max,
    )
