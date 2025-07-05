import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromiumService
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

# 🔧 ヘルパー関数定義
def get_page_url(year, page_num):
    if page_num == 1:
        return f"https://www.jtekt.co.jp/news/news{year}.html"
    else:
        return f"https://www.jtekt.co.jp/news/news{year}_{page_num}.html"

def get_max_page(driver, year):
    url = get_page_url(year, 1)
    driver.get(url)
    hide_cookie_popup(driver) 
    time.sleep(1)
    page_links = driver.find_elements(By.XPATH, '//ul[@class="pager-box"]/li/a')
    page_numbers = set()
    for a in page_links:
        href = a.get_attribute("href")
        if href and f"news{year}" in href:
            if f"news{year}.html" in href:
                page_numbers.add(1)
            elif f"news{year}_" in href:
                try:
                    num = int(href.split(f"news{year}_")[1].split(".html")[0])
                    page_numbers.add(num)
                except:
                    pass
    return max(page_numbers) if page_numbers else 1

# Cookieポップアップを非表示にする関数
def hide_cookie_popup(driver):
    try:
        driver.execute_script("""
            let banner = document.querySelector('#onetrust-banner-sdk');
            if (banner) banner.style.display = 'none';

            let overlay = document.querySelector('.onetrust-pc-dark-filter');
            if (overlay) overlay.style.display = 'none';
        """)
        print("✅ Cookieポップアップを非表示にしました")
    except Exception as e:
        print(f"⚠️ 非表示処理に失敗しました: {e}")



WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, '//div//p[@class="article-txt"]'))
)
time.sleep(3)

hide_cookie_popup(driver)

# ニュース記事一覧から抽出
data = []
articles = driver.find_elements(By.XPATH, '//li[@class="article"]')

for article in articles:
    try:
        # 🔗 先にリンク・タイトル・日付を取得
        link = article.find_element(By.XPATH, './/a').get_attribute('href')
        title = article.find_element(By.XPATH, './/p[@class="article-txt"]').text
        date = article.find_element(By.XPATH, './/time').text

        print("✅ 処理中リンク:", link)

        # 🚫 本文抽出対象外ページ（以下に該当するリンクは本文スキップ）
        # ① IRページ（例：/ir/ を含む）
        if "/ir/" in link:
            print(f"📄 IRページのため本文抽出スキップ → {link}")
            data.append({
                "日付": date,
                "見出し": title,
                "本文": "IRページのため本文抽出スキップ",
                "リンク": link
            })
            continue

        # ② エンジニアリングジャーナルページ（例：/engineering-journal/ を含む）
        elif "/engineering-journal/" in link:
            print(f"📄 Engineering Journalページのため本文抽出スキップ → {link}")
            data.append({
                "日付": date,
                "見出し": title,
                "本文": "Engineering Journalページのため本文抽出スキップ",
                "リンク": link
            })
            continue

        # ③ 外部動画サイト（例：irmovie.jp）
        elif "irmovie.jp" in link:
            print(f"📄 外部動画ページのため本文抽出スキップ → {link}")
            data.append({
                "日付": date,
                "見出し": title,
                "本文": "外部動画ページのため本文抽出スキップ",
                "リンク": link
            })
            continue

        # 個別ページへアクセス
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(link)

        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        hide_cookie_popup(driver)

        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, '//div[@class="detail-content"]'))
        )

        # BeautifulSoupで本文抽出
        soup = BeautifulSoup(driver.page_source, "html.parser")
        content_div = soup.select_one("div.detail-content")

        body_text = ""
        for tag in content_div.find_all(["h2", "p"]):
            body_text += tag.get_text(strip=True) + "\n"

        data.append({
            "日付": date,
            "見出し": title,
            "本文": body_text.strip(),
            "リンク": link
        })

        # タブを閉じて元に戻る
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(1)

    except Exception as e:
        print("⚠️ エラー発生:")
        traceback.print_exc()
        try:
            driver.switch_to.window(driver.window_handles[0])
        except:
            pass
        continue

# DataFrame化
df = pd.DataFrame(data)

# 表示
st.success(f"{len(df)} 件の記事を抽出しました")
st.dataframe(df)

# ダウンロードボタンimport streamlit as st
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
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@class="detail-content"]')))

            soup = BeautifulSoup(driver.page_source, "html.parser")
            content_div = soup.select_one("div.detail-content")
            body_text = "\n".join(tag.get_text(strip=True) for tag in content_div.find_all(["h2", "p"]))

            data.append({"日付": date, "見出し": title, "本文": body_text.strip(), "リンク": link})

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

# Streamlit UI
st.title("JTEKTニュース抽出アプリ")
if st.button("実行する"):
    df = scrape_articles()
    st.success(f"{len(df)}件を抽出しました")
    st.dataframe(df)
    st.download_button("CSVダウンロード", df.to_csv(index=False), "jtekt_news.csv", "text/csv")

st.download_button(
    label="📄 CSVダウンロード",
    data=df.to_csv(index=False),
    file_name="jtekt_news.csv",
    mime="text/csv"
)
