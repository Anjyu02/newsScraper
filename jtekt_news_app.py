import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re

# 段落整形関数
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

# ニュース収集関数（Ver1.5 ページネーション＋期間打ち切り型）
def fetch_news(start_date, end_date):
    base_url = 'https://www.jtekt.co.jp/news/?page='
    page = 1
    news_list = []
    
    while True:
        response = requests.get(base_url + str(page))
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.select('li.article')
        
        if not articles:
            break  # 記事がない場合は終了
        
        for item in articles:
            date_str = item.select_one('time.article-op-data')['datetime']
            date = pd.to_datetime(date_str)
            
            if date < start_date:
                return pd.DataFrame(news_list, columns=['企業名','日付','カテゴリ','タイトル','URL','本文'])
            
            if start_date <= date <= end_date:
                title = item.select_one('p.article-txt').text.strip()
                category = item.select_one('p.article-op-cate').text.strip()
                link = item.select_one('a')['href']
                full_link = link if link.startswith('http') else 'https://www.jtekt.co.jp' + link

                try:
                    detail_response = requests.get(full_link)
                    detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                    content_div = detail_soup.select_one('div.detail-content')
                    body_text = extract_clean_text(content_div) if content_div else "本文なし"
                except Exception as e:
                    body_text = f"本文取得失敗: {e}"

                news_list.append(['JTEKT', date.strftime('%Y-%m-%d'), category, title, full_link, body_text])
                time.sleep(0.5)
        
        page += 1

    return pd.DataFrame(news_list, columns=['企業名','日付','カテゴリ','タイトル','URL','本文'])


# Streamlit アプリ本体

st.title("JTEKT ニュース自動収集ツール Ver1.5")

st.write("""
期間指定に基づいてJTEKT公式ニュースリリースを全ページ自動巡回して収集します。
期間外に入った時点で自動停止する高効率版です。
""")

# 期間選択UI
start_date_input = st.date_input("抽出開始日", pd.to_datetime('2023-01-01'))
end_date_input = st.date_input("抽出終了日", pd.to_datetime('2025-06-16'))

# pandas型に変換（重要！！）
start_date = pd.to_datetime(start_date_input)
end_date = pd.to_datetime(end_date_input)

# 実行ボタン
if st.button("ニュース収集実行"):
    with st.spinner("ニュースを収集中…（少々お待ちください）"):
        result_df = fetch_news(start_date, end_date)
        st.success(f"✅ ニュース抽出完了：{len(result_df)}件")

        st.dataframe(result_df)

        csv = result_df.to_csv(index=False).encode('utf-8')
        st.download_button("CSVダウンロード", csv, f"jtekt_news_{start_date}_{end_date}.csv", "text/csv")

st.caption("対象: https://www.jtekt.co.jp/news/")
