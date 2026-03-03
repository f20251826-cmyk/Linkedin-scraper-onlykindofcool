"""
main.py — CLI entry point for the LinkedIn Search Scraper.

Usage (from CMD prompt):
    python main.py                          # prompts you for the CSV path
    python main.py path\\to\\companies.csv   # uses the given file directly
"""

import sys
import os
import csv
import asyncio

from config import INPUT_CSV, TARGET_ROLES
from scraper import LinkedInScraper


def load_companies(path: str) -> list[str]:
    """
    Read a CSV and return every value from the 'Company' column.
    Handles Excel BOM, auto-detects delimiter, and matches the
    column header case-insensitively.
    """
    companies: list[str] = []

    with open(path, newline="", encoding="utf-8-sig") as f:
        # Sniff the delimiter (comma, tab, semicolon, etc.)
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = "excel"           # fall back to comma-separated

        reader = csv.DictReader(f, dialect=dialect)

        # Find the actual header that matches "company" (case-insensitive)
        headers = reader.fieldnames or []
        print(f"  CSV headers detected: {headers}")
        col_name = None
        for h in headers:
            if h.strip().lower() == "company":
                col_name = h
                break

        if col_name is None:
            print(f"[!] Could not find a 'Company' column. Found: {headers}")
            return companies

        for row in reader:
            name = row.get(col_name, "").strip()
            if name:
                companies.append(name)

    return companies


def resolve_csv_path() -> str:
    """
    Determine the CSV file to use:
      1. If a command-line argument was given, use it.
      2. Else if the default companies.csv exists, use it.
      3. Otherwise, prompt the user to type / paste a path.
    """
    # 1. CLI argument (join all args to handle paths with spaces)
    if len(sys.argv) > 1:
        path = " ".join(sys.argv[1:])
        if os.path.isfile(path):
            return path
        print(f"[!] File not found: {path}")

    # 2. Default file
    if os.path.isfile(INPUT_CSV):
        return INPUT_CSV

    # 3. Interactive prompt
    print("\nNo CSV file found. Please provide the path to your companies CSV.")
    print("The CSV must have a column header named 'Company'.\n")
    while True:
        path = input("Enter CSV file path: ").strip().strip('"').strip("'")
        if os.path.isfile(path):
            return path
        print(f"  [!] File not found: {path}  — try again.\n")


def prompt_roles() -> list[str]:
    """
    Show the default roles and let the user keep them, edit them,
    or enter a completely custom list.
    """
    print("Default roles to search for:")
    for i, role in enumerate(TARGET_ROLES, 1):
        print(f"  {i}. {role}")

    print("\nOptions:")
    print("  Press ENTER to use these defaults.")
    print("  Or type your own roles separated by commas.")
    print("  Example: CTO, Head of Marketing, VP Sales\n")

    user_input = input("Roles: ").strip()

    if not user_input:
        print("Using default roles.\n")
        return list(TARGET_ROLES)

    custom_roles = [r.strip() for r in user_input.split(",") if r.strip()]
    if custom_roles:
        print(f"\nCustom roles set: {', '.join(custom_roles)}\n")
        return custom_roles

    print("No valid roles entered — using defaults.\n")
    return list(TARGET_ROLES)


def main() -> None:
    csv_path = resolve_csv_path()
    print(f"\nLoading companies from: {csv_path}")
    companies = load_companies(csv_path)

    if not companies:
        print("[!] No companies found in the CSV. Exiting.")
        sys.exit(1)

    print(f"Found {len(companies)} company(ies): {', '.join(companies)}\n")

    roles = prompt_roles()

    scraper = LinkedInScraper()

    # Run the async scraper on the default event loop
    asyncio.run(scraper.run(companies, roles))


if __name__ == "__main__":
    main()
