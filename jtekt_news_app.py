import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

st.title("JTEKT ニュース抽出アプリ Ver1.5.3 完全安定版")

# ユーザー入力
start_date = st.date_input("開始日を選択", value=datetime(2024, 1, 1))
end_date = st.date_input("終了日を選択", value=datetime(2025, 12, 31))

if start_date > end_date:
    st.error("開始日は終了日以前の日付を選択してください。")
    st.stop()

@st.cache_data
def fetch_news(start_date, end_date):
    base_url = "https://www.jtekt.co.jp/news/"
    page = 1
    max_pages = 30
    news_data = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    while page <= max_pages:
        url = base_url if page == 1 else f"{base_url}index_{page}.html"
        response = requests.get(url)
        if response.status_code != 200:
            break

        soup = BeautifulSoup(response.content, "html.parser")
        news_list = soup.select("ul.news-box-article li.article")

        if not news_list:
            break

        stop_flag = False

        for article in news_list:
            time_tag = article.select_one("time.article-op-data")
            if not time_tag:
                continue

            # 日付をdatetime型に変換
            date_text = time_tag.get("datetime").strip()
            date_obj = datetime.strptime(date_text, "%Y-%m-%d").date()

            # タイトル
            title_tag = article.select_one("p.article-txt")
            title = title_tag.get_text(strip=True) if title_tag else ""

            # URL
            link_tag = article.find("a")
            if link_tag and link_tag.get("href"):
                link = link_tag.get("href")
                if not link.startswith("http"):
                    link = "https://www.jtekt.co.jp" + link
            else:
                link = ""

            if start_date <= date_obj <= end_date:
                news_data.append({
                    "日付": date_obj,
                    "タイトル": title,
                    "リンク": link
                })
            elif date_obj < start_date:
                stop_flag = True
                break

        progress = page / max_pages
        progress_bar.progress(progress)
        status_text.text(f"{page}ページまで巡回中…")

        if stop_flag:
            break

        page += 1

    progress_bar.empty()
    status_text.text("巡回完了")
    return pd.DataFrame(news_data)

# 実行ボタン
if st.button("抽出開始"):
    result_df = fetch_news(start_date, end_date)
    if result_df.empty:
        st.write("該当期間のニュースはありませんでした。")
    else:
        st.write(f"{len(result_df)}件のニュースを抽出しました。")
        st.dataframe(result_df)

        csv = result_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("CSVダウンロード", csv, file_name="jtekt_news.csv", mime="text/csv")
