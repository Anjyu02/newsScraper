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
from datetime import datetime

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

def scrape_articles(year, start_date, end_date):
    print(f"🚀 scrape_articles 開始: {year}年（{start_date.date()}〜{end_date.date()}）")
    driver = generate_driver()
    data = []
    page_num = 1

    # ✅ Streamlit 表示用エリア
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

        for article in articles:
            try:
                link = article.find_element(By.XPATH, './/a').get_attribute('href')
                title = article.find_element(By.XPATH, './/p[@class="article-txt"]').text
                date = article.find_element(By.XPATH, './/time').text
                date_obj = pd.to_datetime(date, format="%Y.%m.%d", errors="coerce")

                print(f"🗓️ 抽出候補: {date} → {date_obj}")
                if pd.isna(date_obj):
                    continue

                status.text(f"📅 現在処理中の日付: {date}")

                # ✅ 期間判定（新しい順に並ぶ構造前提）
                if date_obj < end_date:
                    print(f"🛑 {date} は範囲より古いため打ち切り")
                    driver.quit()
                    return pd.DataFrame(data)
                elif date_obj > start_date:
                    print(f"⏩ {date} は範囲より新しいためスキップ")
                    continue

                # ✅ スキップ対象リンク処理
                skip_reason = None
                if "/ir/" in link:
                    skip_reason = "IRページのため本文抽出スキップ"
                elif "/engineering-journal/" in link:
                    skip_reason = "Engineering Journalページのため本文抽出スキップ"
                elif "irmovie.jp" in link:
                    skip_reason = "外部サイトのため本文抽出スキップ"

                if skip_reason:
                    print(f"📄 {skip_reason} → {link}")
                    data.append({
                        "日付": date,
                        "見出し": title,
                        "本文": skip_reason,
                        "リンク": link
                    })
                    continue

                # ✅ 本文抽出
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
    
# ===============================
# ✅ Streamlit アプリ本体（任意期間対応）
# ===============================

st.title("JTEKTニュース抽出（任意期間）")

# ✅ ユーザーが指定する期間（開始日と終了日）
start_date = st.date_input("開始日（新しい日付）", datetime.today())
end_date = st.date_input("終了日（古い日付）", datetime.today())

if start_date > end_date:
    if st.button("✅ ニュースを抽出する"):
        with st.spinner("記事を抽出中です..."):

            # 1. 年ごとの処理範囲を取得
            year_ranges = get_yearly_date_ranges(
                pd.to_datetime(start_date), pd.to_datetime(end_date)
            )

            all_data = []

            # 2. 各年ごとに記事を取得
            for year, (y_start, y_end) in year_ranges.items():
                st.write(f"📅 {year}年: {y_start.date()} 〜 {y_end.date()} を処理中...")
                df_year = scrape_articles(year, y_start, y_end)
                all_data.append(df_year)

            # 3. データ統合と表示
            if all_data:
                df_all = pd.concat(all_data, ignore_index=True)
                df_all["日付_dt"] = pd.to_datetime(df_all["日付"], format="%Y.%m.%d", errors="coerce")
                df_all = df_all.sort_values("日付_dt", ascending=False).drop(columns=["日付_dt"])

                st.success(f"✅ {len(df_all)}件の記事を抽出しました！")
                st.dataframe(df_all)

                st.download_button(
                    label="📄 CSVダウンロード",
                    data=df_all.to_csv(index=False),
                    file_name="jtekt_news_selected_period.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ 記事が見つかりませんでした。")
else:
    st.error("⚠️ 終了日は開始日より過去の日付を選んでください。")
