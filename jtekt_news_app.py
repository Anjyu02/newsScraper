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

def get_page_url(year, page_num):
    if page_num == 1:
        return f"https://www.jtekt.co.jp/news/news{year}.html"
    else:
        return f"https://www.jtekt.co.jp/news/news{year}_{page_num}.html"

# ✅ ニュース抽出本体
def scrape_articles(year, start_date, end_date):
    driver = generate_driver()
    data = []
    page_num = 1
    status = st.empty()  # ✅ 上書き用表示エリア

    while True:
        url = get_page_url(year, page_num)
        driver.get(url)

        try:
            hide_cookie_popup(driver)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//li[@class="article"]'))
            )
            time.sleep(1)
        except:
            print(f"✅ ページ{page_num}が存在しないため終了")
            break

        articles = driver.find_elements(By.XPATH, '//li[@class="article"]')
        for article in articles:
            try:
                link = article.find_element(By.XPATH, './/a').get_attribute('href')
                title = article.find_element(By.XPATH, './/p[@class="article-txt"]').text
                date = article.find_element(By.XPATH, './/time').text
                date_obj = pd.to_datetime(date, format="%Y.%m.%d", errors="coerce")

                # ✅ ステータス更新
                status.write(f"📄 ページ{page_num} | 📅 処理中の日付: {date}")

                # ✅ フィルタ：終了日より過去 → 終了
                if date_obj < pd.to_datetime(start_date):
                    print(f"🛑 {date} は開始日 {start_date} より前 → 抽出終了")
                    driver.quit()
                    return pd.DataFrame(data)

                # ✅ フィルタ：スキップ対象URL
                if any(skip in link for skip in ["/ir/", "/engineering-journal/", "irmovie.jp"]):
                    data.append({"日付": date, "見出し": title, "本文": "スキップ対象", "リンク": link})
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

        page_num += 1

    driver.quit()
    return pd.DataFrame(data)

# ===============================
# ✅ Streamlit アプリ本体
# ===============================
st.title("JTEKTニュース抽出アプリ")

today = datetime.date.today()
start_of_year = datetime.date(today.year, 1, 1)

start_date = st.date_input("開始日", start_of_year)
end_date = st.date_input("終了日", today)

if start_date > end_date:
    st.error("⚠️ 終了日は開始日以降の日付を選択してください。")
else:
    if st.button("✅ ニュースを抽出する"):
        with st.spinner("記事を抽出中です..."):
            df = scrape_articles(start_date.year, start_date, end_date)
            if df.empty:
                st.warning("記事が見つかりませんでした。")
            else:
                df["日付_dt"] = pd.to_datetime(df["日付"], format="%Y.%m.%d", errors="coerce")
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
