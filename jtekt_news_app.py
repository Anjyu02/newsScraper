import streamlit as st
import pandas as pd
import time
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

def scrape_articles():
    driver = generate_driver()
    driver.get(get_page_url(2024, 1))
    hide_cookie_popup(driver)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div//p[@class="article-txt"]'))
    )
    time.sleep(2)

    data = []
    articles = driver.find_elements(By.XPATH, '//li[@class="article"]')

def scrape_articles(year):
    driver = generate_driver()
    driver.get(get_page_url(year, 1))  # ← 年度を渡すように修正
    hide_cookie_popup(driver)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div//p[@class="article-txt"]'))
    )
    time.sleep(2)

    data = []
    articles = driver.find_elements(By.XPATH, '//li[@class="article"]')

def scrape_articles(year):
    driver = generate_driver()
    driver.get(get_page_url(year, 1))
    hide_cookie_popup(driver)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div//p[@class="article-txt"]'))
    )
    time.sleep(2)

    data = []
    articles = driver.find_elements(By.XPATH, '//li[@class="article"]')

    for article in articles:
        try:
            link = article.find_element(By.XPATH, './/a').get_attribute('href')
            title = article.find_element(By.XPATH, './/p[@class="article-txt"]').text
            date = article.find_element(By.XPATH, './/time').text

            if any(skip in link for skip in ["/ir/", "/engineering-journal/", "irmovie.jp"]):
                data.append({"日付": date, "見出し": title, "本文": "スキップ対象", "リンク": link})
                continue

            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            driver.get(link)
            WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            hide_cookie_popup(driver)
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//div[@class="detail-content"]'))
            )

            soup = BeautifulSoup(driver.page_source, "html.parser")
            content_div = soup.select_one("div.detail-content")
            body_text = "\n".join(
                tag.get_text(strip=True) for tag in content_div.find_all(["h2", "p"])
            )

            data.append({
                "日付": date,
                "見出し": title,
                "本文": body_text.strip(),
                "リンク": link
            })

            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)

        except Exception as e:
            traceback.print_exc()
            try:
                driver.switch_to.window(driver.window_handles[0])
            except:
                pass
            continue

    driver.quit()
    return pd.DataFrame(data)

# ===============================
# ✅ Streamlitアプリ本体
# ===============================
import datetime

st.title("JTEKTニュース抽出アプリ")

# 今日の日付取得
today = datetime.date.today()
start_of_year = datetime.date(today.year, 1, 1)

# 📅 UI設定：開始日はその年の年始、終了日は今日
start_date = st.date_input("開始日", start_of_year)
end_date = st.date_input("終了日", today)

# エラーチェック：終了日が開始日より前でないか
if start_date > end_date:
    st.error("⚠️ 終了日は開始日以降の日付を選択してください。")
else:
    if st.button("✅ ニュースを抽出する"):
        with st.spinner("記事を抽出中です..."):
            df = scrape_articles(start_date.year)  # ← 開始日を関数に渡す
            if df.empty:
                st.warning("記事が見つかりませんでした。")
            else:
                try:
                    # "YYYY.MM.DD" を datetime に変換
                    df["日付_dt"] = pd.to_datetime(df["日付"], format="%Y.%m.%d", errors="coerce")

                    # フィルター：選択した期間内の記事のみ抽出
                    df_filtered = df[(df["日付_dt"] >= pd.to_datetime(start_date)) &
                                     (df["日付_dt"] <= pd.to_datetime(end_date))]

                    if df_filtered.empty:
                        st.warning("指定した期間に該当する記事はありませんでした。")
                    else:
                        st.success(f"{len(df_filtered)}件の記事を抽出しました！")
                        st.dataframe(df_filtered.drop(columns=["日付_dt"]))
                        st.download_button(
                            label="📄 CSVダウンロード",
                            data=df_filtered.drop(columns=["日付_dt"]).to_csv(index=False),
                            file_name=f"jtekt_news_{start_date}_{end_date}.csv",
                            mime="text/csv"
                        )
                except Exception as e:
                    st.error(f"日付処理中にエラーが発生しました: {e}")
