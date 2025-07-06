from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

# ✅ end_date を追加し、進捗用の progress_callback も保持
def scrape_mazda_news(year, end_date, progress_callback=None):
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

        # ✅ 日付を datetime に変換（変換失敗時はスキップ）
        try:
            date_obj = pd.to_datetime(date, format="%Y.%m.%d", errors="coerce")
            if pd.isna(date_obj):
                print(f"⏭️ 日付変換失敗のためスキップ → '{date}' / 見出し: {title}")
                continue
        except Exception as e:
            print(f"⚠️ 日付処理中に例外発生 → {e}")
            continue

        # ✅ ここで終了日より古ければ打ち切り
        if date_obj < end_date:
            print(f"🛑 {date} は終了日 {end_date.date()} より古いため打ち切り")
            break

        # ✅ 進捗表示（Streamlitなどで）
        if progress_callback:
            progress_callback(f"📰 {date} - {title}")

        try:
            driver = generate_driver()
            driver.get(url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.Wysiwyg.column-layout"))
            )

            soup_detail = BeautifulSoup(driver.page_source, "html.parser")
            driver.quit()

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
