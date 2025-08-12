 # scripts/update_meta.py
import os, re
from pytrends.request import TrendReq
from github import Github

REPO_NAME = os.getenv("REPO_NAME")           # owner/repo
HTML_PATH  = os.getenv("HTML_PATH", "index.html")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_keywords():
    try:
        py = TrendReq(hl='en-US', tz=0)
        py.build_payload(["AI Coin"], timeframe="now 7-d", geo="")
        related = py.related_queries()
        top = (related.get("AI Coin") or {}).get("top")
        if top is not None and not top.empty:
            return [q for q in top["query"].head(3).tolist() if isinstance(q, str) and q.strip()] or ["AI Coin"]
    except Exception:
        pass
    return ["AI Coin"]

def update_html(content, title, desc, kw):
    content = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', content, flags=re.I|re.S)
    if re.search(r'<meta[^>]+name=["\']description["\']', content, flags=re.I):
        content = re.sub(r'<meta[^>]+name=["\']description["\'][^>]*>',
                         f'<meta name="description" content="{desc}">', content, flags=re.I)
    else:
        content = content.replace('</head>', f'  <meta name="description" content="{desc}">\n</head>')
    if re.search(r'<meta[^>]+name=["\']keywords["\']', content, flags=re.I):
        content = re.sub(r'<meta[^>]+name=["\']keywords["\'][^>]*>',
                         f'<meta name="keywords" content="{kw}">', content, flags=re.I)
    else:
        content = content.replace('</head>', f'  <meta name="keywords" content="{kw}">\n</head>')
    return content

def main():
    kws = get_keywords()
    title = f"{kws[0]} — новости и аналитика AI Coin"
    desc  = f"Последние тренды: {', '.join(kws)}. Узнайте об AI Coin, криптотокенах и нейротрендах сегодня."
    kwstr = ", ".join(kws + ["AI Coin", "crypto", "blockchain"])

    gh = Github(GITHUB_TOKEN)
    repo = gh.get_repo(REPO_NAME)
    file = repo.get_contents(HTML_PATH)
    html = file.decoded_content.decode("utf-8")

    new_html = update_html(html, title, desc, kwstr)
    if new_html != html:
        repo.update_file(HTML_PATH,
                         f"Update meta tags by trends: {', '.join(kws)}",
                         new_html,
                         file.sha)
        print("✅ Updated:", kws)
    else:
        print("ℹ️ No changes")

if __name__ == "__main__":
    main()