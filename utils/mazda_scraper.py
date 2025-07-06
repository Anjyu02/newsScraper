from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

# ✅ progress_callback を引数に追加
def scrape_mazda_news(year, progress_callback=None):
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

        # ✅ 進捗表示（Streamlitの st.text などを渡す）
        if progress_callback:
            progress_callback(f"📰 {date} - {title}")

        try:
            driver = generate_driver()
            driver.get(url)

            # ✅ 本文エリアが読み込まれるまで最大10秒待機
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.Wysiwyg.column-layout"))
            )

            soup_detail = BeautifulSoup(driver.page_source, "html.parser")
            driver.quit()

            # ✅ 本文は複数のセクションに分かれている
            sections = soup_detail.select("div.Wysiwyg.column-layout")
            texts = []
            for section in sections:
                for tag in section.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
                    text = tag.get_text(separator=" ", strip=True)
                    if text:
                        texts.append(text)

            body = "\n".join(texts) if texts else "❌ 本文が見つかりません"

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
