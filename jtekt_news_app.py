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

# ✅ 固定期間：2024年5月のみ
def scrape_articles(year):
    print("🚀 scrape_articles 開始")
    driver = generate_driver()
    data = []
    page_num = 1

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
