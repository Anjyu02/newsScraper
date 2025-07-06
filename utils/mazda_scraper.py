from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup

# ✅ WebDriver（PCサイズ表示）
def generate_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920x1080')
    return webdriver.Chrome(options=options)

# ✅ マツダニュース抽出関数
def scrape_mazda_news(year):
    base_url = f"https://www.mazda.co.jp/news_list/{year}/"
    driver = generate_driver()
    driver.get(base_url)

    # ✅ 全ての月（アコーディオン）を展開
    accordions = driver.find_elements(By.CSS_SELECTOR, "dl.Accordion")
    for accordion in accordions:
        classes = accordion.get_attribute("class")
        if "open" not in classes:
            try:
                accordion.find_element(By.CSS_SELECTOR, "dt > a").click()
                time.sleep(0.5)  # ⏳ アニメーション or DOM変化待ち
            except:
                print("⚠️ アコーディオン展開に失敗しました")

    # ✅ ページソースを取得してパース
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

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
            news_data.append({
                "日付": date,
                "見出し": title,
                "リンク": url
            })

    return news_data
