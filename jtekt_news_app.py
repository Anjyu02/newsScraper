import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re

# --- 段落整形用関数 ---
def extract_clean_text(content_div):
    paragraphs = []
    for p in content_div.find_all(['p', 'h1', 'h2', 'h3']):
        for br in p.find_all("br"):
            br.replace_with("\n")
        text = p.get_text().strip()
        if text:
            paragraphs.append(text)
    result = "\n".join(paragraphs)
    result = re.sub(r'[ 　]+', ' ', result)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()

# --- ニュース収集関数 ---
def fetch_news(start_date, end_date):
    url = 'https://www.jtekt.co.jp/news/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    news_list = []

    for item in soup.select('li.article'):
        try:
            date_str = item.select_one('time.article-op-data')['datetime']
            date = pd.to_datetime(date_str)
            if not (start_date <= date <= end_date):
                continue

            title = item.select_one('p.article-txt').text.strip()
            category = item.select_one('p.article-op-cate').text.strip()
            link = item.select_one('a')['href']
            full_link = link if link.startswith('http') else 'https://www.jtekt.co.jp' + link

            # 詳細ページ本文取得
            detail_response = requests.get(full_link)
            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
            content_div = detail_soup.select_one('div.detail-content')
            if content_div:
                body_text = extract_clean_text(content_div)
            else:
                body_text = "本文なし"

            news_list.append(['JTEKT', date.strftime('%Y-%m-%d'), category, title, full_link, body_text])
            time.sleep(0.5)

        except Exception as e:
            print(f"記事取得失敗: {e}")
            continue

    return pd.DataFrame(news_list, columns=['企業名','日付','カテゴリ','タイトル','URL','本文'])


# --- Streamlit アプリ本体 ---

st.title("JTEKT ニュース自動収集ツール (クラウド版)")

st.write("""
指定した期間のJTEKT公式ニュースリリースを自動収集し、段落整形済みCSVを生成します。
Streamlit Cloud対応版です。
""")

# 期間選択UI
start_date = st.date_input("抽出開始日", pd.to_datetime('2023-01-01'))
end_date = st.date_input("抽出終了日", pd.to_datetime('2025-06-15'))
