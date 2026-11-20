# Google repo scraper

GitHubのGoogle組織のリポジトリ（リポジトリ名・主要言語・スター数）を全件スクレイピングして、SQLiteに保存するプログラムです。

## 実行方法

    uv sync
    uv run scraper.py

## 補足

- GitHub APIは使わず、リポジトリ一覧ページのHTMLを取得して解析しています
- アクセスごとに `time.sleep(1)` を入れています
- アクセス過多（429）のときは待ってから再試行します
- 結果は `repos.db`（テーブル: repositories）に保存され、最後にSELECT文で表示します