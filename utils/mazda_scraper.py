from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_mazda_news(year, start_date, end_date, progress_callback=None):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

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
            date_obj = pd.to_datetime(date, format="%Y.%m.%d", errors="coerce")
            if pd.isna(date_obj):
                print(f"⏭️ 日付変換失敗 → '{date}' / 見出し: {title}")
                continue
        except Exception as e:
            print(f"⚠️ 日付変換エラー → {e}")
            continue

        if date_obj < end_date:
            print(f"🛑 {date} は終了日 {end_date.date()} より古いため打ち切り")
            break

        if date_obj > start_date:
            print(f"⏩ {date} は開始日 {start_date.date()} より新しいためスキップ")
            continue

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
                for tag in section.find_all(["h1", "h2", "h3", "h4", "p", "li", "strong", "table"]):
                    if tag.name == "table":
                        for row in tag.find_all("tr"):
                            cells = row.find_all(["th", "td"])
                            row_text = "｜".join(cell.get_text(strip=True) for cell in cells)
                            texts.append(row_text)
                    else:
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
