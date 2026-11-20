import json
import sqlite3
import time

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://github.com/orgs/google/repositories"
HEADERS = {"User-Agent": "Mozilla/5.0 (class assignment scraper)"}
DB_NAME = "repos.db"
PAGE_LIMIT = 300  # 無限ループ防止の保険


def fetch(page: int) -> requests.Response:
    """429(アクセス過多)のときは待ってから再試行する"""
    for attempt in range(6):
        res = requests.get(BASE_URL, params={"page": page}, headers=HEADERS, timeout=10)
        if res.status_code == 429:
            wait = 60 * (attempt + 1)
            print(f"  429 Too Many Requests. {wait}秒待ってやり直します...")
            time.sleep(wait)
            continue
        res.raise_for_status()
        return res
    raise RuntimeError(f"page {page}: 何度やっても429でした")


def scrape_page(page: int) -> list[tuple[str, str, int]]:
    res = fetch(page)
    soup = BeautifulSoup(res.text, "html.parser")

    # ページに埋め込まれているJSONを読む
    script = soup.find("script", attrs={"data-target": "react-app.embeddedData"})
    if script is None or not script.string:
        return []
    data = json.loads(script.string)
    repos = data["payload"]["orgReposPageRoute"]["repositories"]

    rows = []
    for repo in repos:
        lang_info = repo.get("primaryLanguage")
        language = lang_info["name"] if lang_info else "N/A"
        rows.append((repo["name"], language, repo["starsCount"]))
    return rows


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            language TEXT,
            stars INTEGER
        )
        """
    )


def main() -> None:
    conn = sqlite3.connect(DB_NAME)
    init_db(conn)

    seen = set()
    page = 1
    while page <= PAGE_LIMIT:
        rows = scrape_page(page)
        new_rows = [r for r in rows if r[0] not in seen]
        if not new_rows:  # 0件、または同じ内容の繰り返し = 最後まで来た
            print(f"page {page}: no new repos. finished.")
            break

        seen.update(r[0] for r in new_rows)
        print(f"page {page}: {len(new_rows)} repos")
        conn.executemany(
            "INSERT OR REPLACE INTO repositories (name, language, stars) VALUES (?, ?, ?)",
            new_rows,
        )
        conn.commit()
        page += 1
        time.sleep(1)  # 必須

    print("--- SELECT ---")
    count = conn.execute("SELECT COUNT(*) FROM repositories").fetchone()[0]
    print(f"total: {count}")
    for row in conn.execute(
        "SELECT name, language, stars FROM repositories ORDER BY stars DESC LIMIT 20"
    ):
        print(row)
    conn.close()


if __name__ == "__main__":
    main()