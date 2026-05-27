# 📰 Web Scraper for Headlines

> **SyntecxHub — Project 3**
> **Author:** Nishchal Soni
> **Date:** 2026-05-27

A clean, ethical Python web scraper that fetches headlines from multiple news sources, filters them by keyword, and saves results to JSON or CSV — all while respecting `robots.txt` and being polite to servers.

---

## 📁 Project Structure

```
headline-scraper/
├── web_scraper_headlines.py   # Main scraper script
├── headlines.json             # Output file (auto-generated)
├── headlines.csv              # Output file (auto-generated)
└── README.md                  # This file
```

---

## ⚙️ Requirements

- Python **3.10+**
- Install dependencies:

```bash
pip install requests beautifulsoup4
```

All other modules (`csv`, `json`, `time`, `logging`, `urllib`) are part of Python's standard library — no extra installs needed.

---

## 🚀 How to Run

### Basic usage (scrape all sources, save as JSON)

```bash
python web_scraper_headlines.py
```

This will:
1. Check `robots.txt` for each source
2. Fetch and parse headlines
3. Display them in the terminal
4. Save results to `headlines.json`

---

## 🔧 Command-Line Options

| Flag | Short | Description | Default |
|---|---|---|---|
| `--keyword` | `-k` | Filter headlines by keyword (case-insensitive) | None (all headlines) |
| `--format` | `-f` | Output format: `json`, `csv`, or `both` | `json` |
| `--output` | `-o` | Base filename for output (no extension) | `headlines` |
| `--max` | `-m` | Max headlines to keep per source | `20` |

---

## 📌 Usage Examples

### 1. Filter by keyword
```bash
python web_scraper_headlines.py --keyword "AI"
```
Only keeps headlines whose title contains "AI" (case-insensitive).

### 2. Save as CSV
```bash
python web_scraper_headlines.py --format csv
```

### 3. Save as both JSON and CSV
```bash
python web_scraper_headlines.py --format both
```

### 4. Custom output filename
```bash
python web_scraper_headlines.py --output todays_news
# Creates: todays_news.json
```

### 5. Limit to 10 headlines per source
```bash
python web_scraper_headlines.py --max 10
```

### 6. Combine all options
```bash
python web_scraper_headlines.py -k "Python" -f both -o python_news -m 15
```

---

## 📄 Output Format

Each headline entry looks like this:

```json
{
  "title": "OpenAI releases new model",
  "url": "https://example.com/article",
  "time": "2026-05-27T10:30:00",
  "source": "Hacker News",
  "scraped_at": "2026-05-27T08:45:00Z"
}
```

| Field | Description |
|---|---|
| `title` | The headline text |
| `url` | Link to the full article |
| `time` | Publication time (if available on the page) |
| `source` | Name of the news source |
| `scraped_at` | UTC timestamp of when it was scraped |

---

## 🌐 Default News Sources

The scraper comes pre-configured with two sources:

| Source | URL |
|---|---|
| Hacker News | https://news.ycombinator.com/ |
| BBC News | https://www.bbc.com/news |

---

## ➕ Adding a New Source

Open `web_scraper_headlines.py` and add a new entry to the `SOURCES` list:

```python
SOURCES = [
    # ... existing sources ...
    {
        "name": "My News Site",
        "url": "https://example-news.com/",
        "article_selector": "article.story",   # CSS selector for each article block
        "title_selector": "h2.headline",        # CSS selector for the title inside the block
        "link_attr": "href",                    # Attribute on the title tag that holds the URL
        "time_selector": "time",                # CSS selector for timestamp (or None)
    },
]
```

Use your browser's **Inspect Element** (F12) to find the correct CSS selectors for any website.

---

## 🛡️ Ethical Scraping

This scraper is designed to be a **good web citizen**:

- ✅ Reads and respects `robots.txt` before crawling any site
- ✅ Adds a random delay of **1.5 – 3.5 seconds** between requests
- ✅ Sends a descriptive `User-Agent` header identifying the bot
- ✅ Retries failed requests with **exponential back-off** (up to 3 attempts)
- ✅ Skips a source entirely if `robots.txt` disallows it

---

## 🧩 Use as a Python Module

You can also import and call the scraper from your own scripts:

```python
from web_scraper_headlines import run_scraper, SOURCES

# Use default sources
results = run_scraper(keyword="climate", output_format="both")

# Use a custom source list
my_sources = [SOURCES[0]]  # Only Hacker News
results = run_scraper(sources=my_sources, max_per_source=10)

# Access results as a list of dicts
for item in results:
    print(item["title"], "→", item["url"])
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: bs4` | Run `pip install beautifulsoup4` |
| No headlines printed | The site's HTML structure may have changed — update the CSS selectors in `SOURCES` |
| Source skipped | `robots.txt` on that site disallows crawling — this is by design |
| Timeout errors | Check your internet connection; the scraper retries automatically |

---

## 📜 License

This project is for **educational purposes** as part of the SyntecxHub internship program. Always check a website's Terms of Service before scraping.

---

*Made with ❤️ by **Nishchal Soni** — SyntecxHub Project 2*
