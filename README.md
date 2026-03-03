# LinkedIn Profile Scraper

A command-line LinkedIn profile scraper that uses **Google dorking** (`site:linkedin.com/in/`) to find employee names, titles, and profile URLs for specific roles across a list of companies.

> No LinkedIn login required — works entirely through Google Search.

---

## Features

- **Google-powered search** — bypasses LinkedIn's network restrictions by searching Google instead
- **CSV input** — reads company names from any `.csv` file with a `Company` column  
- **Custom roles** — prompts you to enter roles to search (or use defaults like Founder, PR, CSR, etc.)
- **Incremental CSV output** — results are saved to `results.csv` after every search (safe to open mid-run)
- **Pause / Resume** — press `P + Enter` at any time to pause or resume  
- **Anti-detection** — uses `playwright-stealth` and randomized delays  
- **CAPTCHA handling** — pauses automatically if Google shows a CAPTCHA, lets you solve it, then continues

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/linkedinScraper.git
cd linkedinScraper
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Playwright browsers

```bash
playwright install chromium
```

---

## How to Run (CMD)

### Basic usage

```cmd
python main.py
```

The script will:
1. Ask you for the path to your **CSV file** (or use `companies.csv` in the same folder)
2. Show you the **default roles** and let you customize them
3. Open a Chromium browser and start searching Google
4. Save results to `results.csv` as it goes

### Provide CSV file directly

```cmd
python main.py path\to\your\companies.csv
```

> **Tip:** File paths with spaces work too — no need for quotes.

### Example with a file on the Desktop

```cmd
python main.py C:\Users\YourName\Desktop\my companies.csv
```

---

## CSV File Format

Your input CSV must have a column named `Company` (case-insensitive). Example:

| Company |
|---|
| Insolation Energy |
| Tata Motors |
| Infosys |

---

## Configuration

Edit `config.py` to change:

| Setting | Default | Description |
|---|---|---|
| `TARGET_ROLES` | 10 roles | Default roles shown in the prompt |
| `MAX_RESULTS_PER_SEARCH` | `10` | Max profiles per company×role search |
| `INTER_COMPANY_DELAY` | `(3, 5)` | Seconds to wait between companies |
| `INTER_ROLE_DELAY` | `(1, 3)` | Seconds to wait between role searches |

---

## Output

Results are saved to `results.csv` with these columns:

| Column | Description |
|---|---|
| Company | Company name from input CSV |
| Target Role | Role that was searched |
| Employee Name | Name extracted from Google |
| Employee Title | Title/snippet from Google |
| Profile Link | Full LinkedIn profile URL |

---

## Controls During Scraping

| Key | Action |
|---|---|
| `P + Enter` | Pause / Resume the scraper |
| `Ctrl + C` | Stop the scraper immediately |

---

## Project Structure

```
linkedinScraper/
├── main.py              # CLI entry point
├── scraper.py           # Core scraper (Google dorking)
├── config.py            # Configuration (roles, delays, paths)
├── utils.py             # Helper functions (scroll, delay)
├── requirements.txt     # Python dependencies
├── sample_companies.csv # Example input file
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

---

## Dependencies

- Python 3.10+
- [Playwright](https://playwright.dev/python/)
- [playwright-stealth](https://pypi.org/project/playwright-stealth/)

---

## Disclaimer

This tool is for educational and research purposes only. Use responsibly and in compliance with LinkedIn's and Google's terms of service.
