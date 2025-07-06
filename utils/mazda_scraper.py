from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_mazda_news(year):
    def generate_driver():
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920x1080")
        return webdriver.Chrome(options=options)

    base_url = f"https://www.mazda.co.jp/news_list/{year}/"
    driver = generate_driver()
    driver.get(base_url)
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    articles = soup.select("div.Notification__list__box2")
    news_data = []

    for article in articles:
        link_tag = article.select_one("a.Notification__list__link")
        if not link_tag:
            continue

        url = "https://www.mazda.co.jp" + link_tag["href"]
        date_tag = link_tag.select_one("p.Notification__list__date")
        title_tag = link_tag.select_one("p.Notification__list__text-pc")
        date = date_tag.text.strip() if date_tag else ""
        title = title_tag.text.strip() if title_tag else ""

        # 本文抽出（別タブで開かず、個別にSeleniumで取得）
        driver = generate_driver()
        driver.get(url)
        time.sleep(1)
        soup_detail = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        content_div = soup_detail.select_one("div.OneColumnLayout__column")
        if not content_div:
            body = "❌ 本文が見つかりません"
        else:
            elements = content_div.select("h2, h4, p, strong, table")
            texts = []
            for elem in elements:
                if elem.name == "table":
                    texts.append(elem.get_text(strip=True, separator=" "))
                else:
                    text = elem.get_text(strip=True)
                    if text:
                        texts.append(text)
            body = "\n".join(texts)

        news_data.append({
            "日付": date,
            "見出し": title,
            "本文": body,
            "リンク": url
        })

    return pd.DataFrame(news_data)
