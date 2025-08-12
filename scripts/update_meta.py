# scripts/update_meta.py
import os, re, sys, html
from typing import List, Dict
from pytrends.request import TrendReq
from github import Github

# === ENV ===
REPO_NAME    = os.getenv("REPO_NAME") or os.getenv("GITHUB_REPOSITORY")  # owner/repo
HTML_PATH    = os.getenv("HTML_PATH", "index.html")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
X_BEARER     = os.getenv("X_BEARER_TOKEN")  # опционально: Twitter API v2 Bearer

if not REPO_NAME:
    sys.exit("❌ REPO_NAME env is empty. Example: AiCoinETH/getaicoin.com")
if not GITHUB_TOKEN:
    sys.exit("❌ GITHUB_TOKEN env is empty. Use ${{ secrets.GITHUB_TOKEN }} in workflow.")

# === Локали и шаблоны ===
LOCALES: Dict[str, Dict] = {
  "en": {"hl":"en-US","geo":"US",
         "title":"{kw} — news & insights on AI Coin",
         "desc": "Latest trends: {kws}. Learn about AI Coin, crypto tokens, and AI trends today."},
  "ru": {"hl":"ru-RU","geo":"RU",
         "title":"{kw} — новости и аналитика AI Coin",
         "desc": "Последние тренды: {kws}. Узнайте об AI Coin, криптотокенах и нейротрендах сегодня."},
  "de": {"hl":"de-DE","geo":"DE",
         "title":"{kw} — News und Analysen zu AI Coin",
         "desc": "Aktuelle Trends: {kws}. Erfahren Sie mehr über AI Coin, Kryptotoken und KI-Trends."},
  "es": {"hl":"es-ES","geo":"ES",
         "title":"{kw} — noticias y análisis de AI Coin",
         "desc": "Tendencias recientes: {kws}. Conozca AI Coin, los criptoactivos y las tendencias de IA."},
  "fr": {"hl":"fr-FR","geo":"FR",
         "title":"{kw} — actualités et analyses d’AI Coin",
         "desc": "Tendances récentes : {kws}. En savoir plus sur AI Coin, les cryptos et les tendances IA."},
  "it": {"hl":"it-IT","geo":"IT",
         "title":"{kw} — notizie e analisi su AI Coin",
         "desc": "Trend recenti: {kws}. Scopri AI Coin, i token crypto e i trend dell’IA."},
  "pt": {"hl":"pt-PT","geo":"PT",
         "title":"{kw} — notícias e análises do AI Coin",
         "desc": "Tendências recentes: {kws}. Saiba mais sobre AI Coin, criptoativos e tendências de IA."},
  "ja": {"hl":"ja-JP","geo":"JP",
         "title":"{kw} — AI Coin のニュースと分析",
         "desc": "最新トレンド: {kws}。AI Coin、暗号トークン、AIトレンドについて。"},
  "zh": {"hl":"zh-CN","geo":"CN",
         "title":"{kw} — AI Coin 新闻与分析",
         "desc": "最新趋势：{kws}。了解 AI Coin、加密代币与人工智能趋势。"},
}
BASE_KEYWORDS = ["AI Coin","crypto","blockchain","Web3"]

def get_trends_keywords(topic: str, hl: str, geo: str) -> List[str]:
    """Google Trends: до 3 релевантных запросов; фоллбек на topic."""
    try:
        py = TrendReq(hl=hl, tz=0)
        py.build_payload([topic], timeframe="now 7-d", geo=geo or "")
        related = py.related_queries()
        top = (related.get(topic) or {}).get("top")
        if top is not None and not top.empty:
            qs = [q for q in top["query"].tolist() if isinstance(q, str) and q.strip()]
            qs = [re.sub(r"\s+", " ", q).strip() for q in qs]
            return qs[:3] or [topic]
    except Exception:
        pass
    return [topic]

def get_x_keywords(topic: str, bearer: str) -> List[str]:
    """Опционально: добираем топ-хэштеги из X/Twitter (API v2)."""
    if not bearer: return []
    import json, urllib.parse, urllib.request
    try:
        q = urllib.parse.quote(f'"{topic}" OR $Ai (lang:en) -is:retweet')
        url = f"https://api.twitter.com/2/tweets/search/recent?query={q}&max_results=50&tweet.fields=entities"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {bearer}"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode("utf-8"))
        bag = []
        for t in data.get("data", []):
            for h in t.get("entities", {}).get("hashtags", []):
                tag = (h.get("tag","") or "").strip()
                if tag and len(tag) <= 25:
                    bag.append("#"+tag)
        out = []
        for tag in sorted(set(bag), key=lambda z: bag.count(z), reverse=True):
            out.append(tag)
            if len(out) >= 5: break
        return out
    except Exception:
        return []

def esc(s:str) -> str:
    return html.escape(s, quote=True)

def ensure_meta_lang(content: str, name: str, lang: str, value: str) -> str:
    """Заменяет/добавляет <meta name="..."> с lang="..". Порядок атрибутов неважен."""
    pattern = re.compile(
        rf'<meta(?=[^>]*\bname=["\']{re.escape(name)}["\'])(?=[^>]*\blang=["\']{re.escape(lang)}["\'])[^>]*>',
        flags=re.I
    )
    tag = f'<meta name="{name}" lang="{lang}" content="{esc(value)}">'
    if pattern.search(content):
        return pattern.sub(tag, content, count=1)
    return content.replace("</head>", f"  {tag}\n</head>")

def ensure_meta_default(content: str, name: str, value: str) -> str:
    pattern = re.compile(rf'<meta[^>]*\bname=["\']{re.escape(name)}["\'][^>]*>', flags=re.I)
    tag = f'<meta name="{name}" content="{esc(value)}">'
    if pattern.search(content):
        return pattern.sub(tag, content, count=1)
    return content.replace("</head>", f"  {tag}\n</head>")

def set_title(content: str, value: str) -> str:
    tag = f"<title>{esc(value)}</title>"
    if re.search(r"<title>.*?</title>", content, flags=re.I|re.S):
        return re.sub(r"<title>.*?</title>", tag, content, count=1, flags=re.I|re.S)
    return content.replace("</head>", f"  {tag}\n</head>")

def main():
    gh   = Github(GITHUB_TOKEN)
    repo = gh.get_repo(REPO_NAME)
    file = repo.get_contents(HTML_PATH)
    html_in = file.decoded_content.decode("utf-8")

    # === дефолт EN ===
    kws_en = get_trends_keywords("AI Coin", LOCALES["en"]["hl"], LOCALES["en"]["geo"])
    kws_en += get_x_keywords("AI Coin", X_BEARER)
    kws_en = [k for k in kws_en if k][:3] or ["AI Coin"]
    kwstr_en = ", ".join(kws_en + BASE_KEYWORDS)
    title_en = LOCALES["en"]["title"].format(kw=kws_en[0])
    desc_en  = LOCALES["en"]["desc"].format(kws=", ".join(kws_en))

    out = html_in
    out = set_title(out, title_en)
    out = ensure_meta_default(out, "description", desc_en)
    out = ensure_meta_default(out, "keywords", kwstr_en)

    # === локали с lang=".." ===
    for lang, cfg in LOCALES.items():
        if lang == "en":
            continue
        ks = get_trends_keywords("AI Coin", cfg["hl"], cfg["geo"])
        tags_x = get_x_keywords("AI Coin", X_BEARER)
        if tags_x:
            ks = (ks + tags_x)[:5]
        kwstr = ", ".join(ks + BASE_KEYWORDS)
        title = cfg["title"].format(kw=ks[0])
        desc  = cfg["desc"].format(kws=", ".join(ks))
        out = ensure_meta_lang(out, "description", lang, desc)
        out = ensure_meta_lang(out, "keywords",    lang, kwstr)
        # (title локализованный обычно не дублируем — оставляем один <title> EN)

    if out != html_in:
        repo.update_file(HTML_PATH, "Update i18n meta tags by trends", out, file.sha)
        print("✅ Meta updated for locales:", ", ".join(LOCALES.keys()))
    else:
        print("ℹ️ No changes")

if __name__ == "__main__":
    main()