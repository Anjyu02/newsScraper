from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

        try:
            driver = generate_driver()
            driver.get(url)

            # ✅ 本文エリアが読み込まれるまで最大10秒待機
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.Wysiwyg.column-layout"))
            )

            soup_detail = BeautifulSoup(driver.page_source, "html.parser")
            driver.quit()

            content_div = soup_detail.select_one("div.Wysiwyg.column-layout")
            if not content_div:
                body = "❌ 本文が見つかりません"
            else:
                # ✅ 中身をすべてテキスト化（改行付き）
                body = content_div.get_text(separator="\n", strip=True)

        except Exception as e:
            driver.quit()
            print(f"⚠️ 本文抽出失敗: {url} → {e}")
            body = f"⚠️ 本文抽出エラー: {e}"

        news_data.append({
            "日付": date,
            "見出し": title,
            "本文": body,
            "リンク": url
        })

    return pd.DataFrame(news_data)
