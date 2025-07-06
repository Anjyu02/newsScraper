import requests
from bs4 import BeautifulSoup
import pandas as pd

# ✅ マツダニュース抽出関数（Seleniumなし版）
def scrape_mazda_news(year):
    base_url = f"https://www.mazda.co.jp/news_list/{year}/"
    res = requests.get(base_url, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # ✅ 記事データ抽出
    articles = soup.select("div.Notification__list__box2")
    news_data = []

    for article in articles:
        link_tag = article.select_one("a.Notification__list__link")
        if link_tag:
            url = "https://www.mazda.co.jp" + link_tag["href"]
            date_tag = link_tag.select_one("p.Notification__list__date")
            title_tag = link_tag.select_one("p.Notification__list__text-pc")
            date = date_tag.text.strip() if date_tag else ""
            title = title_tag.text.strip() if title_tag else ""

            # ✅ 本文ページにアクセスして、本文を取得
            body = scrape_article_body(url)

            news_data.append({
                "日付": date,
                "見出し": title,
                "本文": body,
                "リンク": url
            })

    return pd.DataFrame(news_data)

# ✅ 本文抽出関数
def scrape_article_body(url):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # ✅ h2, h4, p, strong, table のテキストを順に抽出
        content_div = soup.select_one("div.OneColumnLayout__column")
        if not content_div:
            return ""

        elements = content_div.select("h2, h4, p, strong, table")
        texts = []

        for elem in elements:
            if elem.name == "table":
                texts.append(elem.get_text(strip=True, separator=" "))
            else:
                text = elem.get_text(strip=True)
                if text:
                    texts.append(text)

        return "\n".join(texts)

    except Exception as e:
        print(f"⚠️ 本文抽出失敗: {url} → {e}")
        return ""
