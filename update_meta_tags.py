import os
import re
from pytrends.request import TrendReq
from github import Github

# Настройки
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "AiCoinETH/AiCoin_Website"
HTML_PATH = "index.html"

# Получение трендов Google
pytrends = TrendReq(hl='en-US', tz=0)
pytrends.build_payload(kw_list=["AI Coin"], timeframe="now 7-d", geo="")
related = pytrends.related_queries()
top = related.get("AI Coin", {}).get("top")
keywords = top.head(3)["query"].tolist() if top is not None else ["AI Coin"]

# Формирование мета-тегов
title = f"{keywords[0]} — новости и аналитика AI Coin"
description = f"Последние тренды: {', '.join(keywords)}. Узнайте о AI Coin, криптотокенах и нейронных трендах сегодня."
keywords_meta = ", ".join(keywords + ["AI Coin", "crypto", "blockchain"])

# Получение содержимого index.html
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)
file = repo.get_contents(HTML_PATH)
content = file.decoded_content.decode("utf-8")

# Обновление мета-тегов в <head>
content = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', content, flags=re.IGNORECASE)

if 'name="description"' in content:
    content = re.sub(r'<meta name="description".*?>',
                     f'<meta name="description" content="{description}">',
                     content, flags=re.IGNORECASE)
else:
    content = content.replace("</head>", f'  <meta name="description" content="{description}">\n</head>')

if 'name="keywords"' in content:
    content = re.sub(r'<meta name="keywords".*?>',
                     f'<meta name="keywords" content="{keywords_meta}">',
                     content, flags=re.IGNORECASE)
else:
    content = content.replace("</head>", f'  <meta name="keywords" content="{keywords_meta}">\n</head>')

# Коммит изменений
repo.update_file(HTML_PATH,
                 f"Update meta tags for trends: {', '.join(keywords)}",
                 content,
                 file.sha)

print("✅ Мета-теги обновлены:", keywords)
