import streamlit as st
st.title("✅ ページは読み込めています")

if st.button("テスト表示"):
    st.write("これは仮の表示です")

# import streamlit as st
# import pandas as pd
# from datetime import datetime
# from utils.mazda_scraper import scrape_articles_mazda

# st.title("🚗 マツダニュース抽出アプリ")

# # ✅ 入力：日付（新しい → 古い）
# start_date = st.date_input("開始日（新しい日）", datetime.today())
# end_date = st.date_input("終了日（古い日）", datetime.today())

# st.caption("※ マツダ公式ニュースは年別に分かれており、ページネーションは存在しません。")

# if start_date < end_date:
#     st.error("⚠️ 終了日は開始日より過去の日付を選んでください。")
# else:
#     if st.button("✅ ニュースを抽出する"):
#         with st.spinner("記事を抽出中です..."):

#             years = list(range(end_date.year, start_date.year + 1))
#             all_data = []

#             for year in years:
#                 st.write(f"📅 {year}年を処理中...")
#                 df = scrape_articles_mazda(year, pd.to_datetime(start_date), pd.to_datetime(end_date))
#                 if not df.empty:
#                     all_data.append(df)

#             if all_data:
#                 df_all = pd.concat(all_data, ignore_index=True)
#                 df_all["日付_dt"] = pd.to_datetime(df_all["日付"], errors="coerce")
#                 df_all = df_all.sort_values("日付_dt", ascending=False).drop(columns=["日付_dt"])

#                 st.success(f"✅ {len(df_all)}件の記事を抽出しました！")
#                 st.dataframe(df_all)

#                 st.download_button(
#                     label="📄 CSVダウンロード",
#                     data=df_all.to_csv(index=False),
#                     file_name="mazda_news.csv",
#                     mime="text/csv"
#                 )
#             else:
#                 st.warning("⚠️ 指定期間に該当する記事は見つかりませんでした。")
