import streamlit as st
import pandas as pd
import datetime
import traceback
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromiumService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

def generate_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-features=VizDisplayCompositor")
    driver = webdriver.Chrome(
        service=ChromiumService(
            ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
        ),
        options=options
    )
    return driver

def get_page_url(year, page_num):
    if page_num == 1:
        return f"https://www.jtekt.co.jp/news/news{year}.html"
    else:
        return f"https://www.jtekt.co.jp/news/news{year}_{page_num}.html"

def hide_cookie_popup(driver):
    try:
        driver.execute_script("""
            let banner = document.querySelector('#onetrust-banner-sdk');
            if (banner) banner.style.display = 'none';
            let overlay = document.querySelector('.onetrust-pc-dark-filter');
            if (overlay) overlay.style.display = 'none';
        """)
    except Exception as e:
        print(f"⚠️ 非表示処理に失敗しました: {e}")

# ✅ ニュース抽出本体
def scrape_articles(year, start_date, end_date):
    print("🚀 scrape_articles 開始")
    driver = generate_driver()
    data = []
    page_num = 1
    status = st.empty()

    while True:
        url = get_page_url(year, page_num)
        print(f"🌀 アクセスURL: {url}")
        driver.get(url)

        try:
            hide_cookie_popup(driver)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//li[@class="article"]'))
            )
            time.sleep(1)
        except:
            print(f"✅ ページ{page_num}が存在しないため終了")
            break

        articles = driver.find_elements(By.XPATH, '//li[@class="article"]')
        print(f"📄 ページ{page_num} の記事数: {len(articles)}")

        def scrape_articles(year):
    print("🚀 scrape_articles 開始")
    driver = generate_driver()
    data = []
    page_num = 1

    # 🎯 固定の期間指定：2024年5月のみ
    start_date = pd.to_datetime("2024-05-31")
    end_date = pd.to_datetime("2024-05-01")

    while True:
        url = get_page_url(year, page_num)
        print(f"🌀 アクセスURL: {url}")
        driver.get(url)

        try:
            hide_cookie_popup(driver)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//li[@class="article"]'))
            )
            time.sleep(1)
        except:
            print(f"✅ ページ{page_num}が存在しないため終了")
            break

        articles = driver.find_elements(By.XPATH, '//li[@class="article"]')
        print(f"📄 ページ{page_num} の記事数: {len(articles)}")

        for article in articles:
            try:
                link = article.find_element(By.XPATH, './/a').get_attribute('href')
                title = article.find_element(By.XPATH, './/p[@class="article-txt"]').text
                date = article.find_element(By.XPATH, './/time').text

                date_obj = pd.to_datetime(date, format="%Y.%m.%d", errors="coerce")
                print(f"🗓️ 抽出候補: {date} → {date_obj}")

                if pd.isna(date_obj):
                    continue

                # 🎯 2024年5月に絞り込み
                if date_obj > start_date or date_obj < end_date:
                    print(f"⏩ {date} は5月以外 → スキップ")
                    continue

                if any(skip in link for skip in ["/ir/", "/engineering-journal/", "irmovie.jp"]):
                    print(f"📄 スキップ対象リンク: {link}")
                    data.append({"日付": date, "見出し": title, "本文": "スキップ対象", "リンク": link})
                    continue

                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[1])
                driver.get(link)

                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "detail-content"))
                )
                soup = BeautifulSoup(driver.page_source, "html.parser")
                content_div = soup.select_one("div.detail-content")

                if content_div:
                    body_text = "\n".join(
                        tag.get_text(strip=True) for tag in content_div.find_all(["h2", "p"])
                    )
                else:
                    body_text = "本文抽出不可"

                data.append({
                    "日付": date,
                    "見出し": title,
                    "本文": body_text.strip(),
                    "リンク": link
                })

                print(f"✅ 抽出成功: {title}")

                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(1)

            except Exception as e:
                print(f"⚠️ エラー発生: {e}")
                traceback.print_exc()
                try:
                    driver.switch_to.window(driver.window_handles[0])
                except:
                    pass
                continue

        page_num += 1

    driver.quit()
    return pd.DataFrame(data)

#Streamlit UI------
st.title("JTEKTニュース抽出（2024年5月限定）")

if st.button("✅ 2024年5月のニュースを取得"):
    with st.spinner("記事を抽出中です..."):
        df = scrape_articles(2024)
        if df.empty:
            st.warning("記事が見つかりませんでした。")
        else:
            st.success(f"{len(df)}件の記事を抽出しました！")
            st.dataframe(df)
            st.download_button(
                label="📄 CSVダウンロード",
                data=df.to_csv(index=False),
                file_name="jtekt_news_2024_05.csv",
                mime="text/csv"
            )
