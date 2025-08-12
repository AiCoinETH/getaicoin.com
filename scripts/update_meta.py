name: update-meta-tags

on:
  workflow_dispatch:            # запуск вручную из вкладки Actions
  schedule:
    - cron: '0 9 */3 * *'       # КАЖДЫЕ 3 ДНЯ в 09:00 UTC
  push:
    paths:
      - scripts/update_meta.py  # автозапуск при изменении скрипта

permissions:
  contents: write               # нужно для коммитов в репозиторий

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install deps
        run: pip install pytrends PyGithub

      - name: Update meta tags
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          REPO_NAME: AiCoinETH/getaicoin.com   # твой репозиторий
          HTML_PATH: index.html
        run: python scripts/update_meta.py