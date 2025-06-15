import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

st.title("JTEKT ニュースリリース抽出アプリ Ver1.5.1完全安定版")

start_date = st.date_input("開始日を選択", value=datetime(2024, 1, 1))
end_date = st.date_input("終了日を選択", value=datetime(2025, 12, 31))

if start_date > end_date:
    st.error("開始日は終了日以前の日付を選択してください。")
    st.stop()

@st.cache_data
def fetch_news(start_date, end_date):
    base_url = "https://www.jtekt.co.jp/news/index.html"
    news_data = []
    page = 1
    max_pages = 30  # 最大ページ数制限（JTEKTは多くても20前後）

    while page <= max_pages:
        url = base_url if page == 1 else f"{base_url}?page={page}"
        response = requests.get(url)
        if response.status_code != 200:
            break

        soup = BeautifulSoup(response.content, "html.parser")
        news_list = soup.select(".newsList li")

        if not news_list:
            break

        stop_flag = False  # 新たに追加

        for news in news_list:
            date_text = news.select_one(".date").text.strip()
            title = news.select_one(".title").text.strip()
            link = news.find("a").get("href")
            full_link = f"https://www.jtekt.co.jp{link}"

            date_obj = datetime.strptime(date_text, "%Y年%m月%d日").date()

            if start_date <= date_obj <= end_date:
                news_data.append({
                    "日付": date_obj,
                    "タイトル": title,
                    "リンク": full_link
                })
            elif date_obj < start_date:
                stop_flag = True
                break  # forループ抜ける
        st.write(f"{page}ページまで巡回しました")
        if stop_flag:
            break

        page += 1

    return pd.DataFrame(news_data)

if st.button("抽出開始"):
    result_df = fetch_news(start_date, end_date)
    if result_df.empty:
        st.write("該当期間のニュースはありませんでした。")
    else:
        st.write(f"{len(result_df)}件のニュースを抽出しました。")
        st.dataframe(result_df)

        csv = result_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("CSVダウンロード", csv, file_name="jtekt_news.csv", mime="text/csv")
