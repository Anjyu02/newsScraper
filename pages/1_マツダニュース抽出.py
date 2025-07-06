import streamlit as st
import pandas as pd
from datetime import datetime
from utils.mazda_scraper import scrape_mazda_news

st.title("🚗 マツダニュース抽出アプリ")

start_date = st.date_input("開始日（新しい日）", datetime.today())
end_date = st.date_input("終了日（古い日）", datetime.today())

st.caption("※ マツダ公式ニュースは年別に分かれており、ページネーションは存在しません。")

if start_date < end_date:
    st.error("⚠️ 終了日は開始日より過去の日付を選んでください。")
else:
    if st.button("✅ ニュースを抽出する"):
        with st.spinner("記事を抽出中です..."):

            years = list(range(end_date.year, start_date.year + 1))
            all_data = []

            for year in years:
                st.write(f"📅 {year}年を処理中...")
                data = scrape_mazda_news(year)  # ✅ 正しい関数名に修正
                df = pd.DataFrame(data)
                if not df.empty:
                    all_data.append(df)

            if all_data:
                df_all = pd.concat(all_data, ignore_index=True)
                df_all["日付_dt"] = pd.to_datetime(df_all["日付"], errors="coerce")

                # ✅ ここで期間フィルター
                df_filtered = df_all[
                    (df_all["日付_dt"] >= pd.to_datetime(end_date)) &
                    (df_all["日付_dt"] <= pd.to_datetime(start_date))
                ].sort_values("日付_dt", ascending=False).drop(columns=["日付_dt"])

                if df_filtered.empty:
                    st.warning("⚠️ 指定期間に該当する記事は見つかりませんでした。")
                else:
                    st.success(f"✅ {len(df_filtered)}件の記事を抽出しました！")
                    st.dataframe(df_filtered)

                    st.download_button(
                        label="📄 CSVダウンロード",
                        data=df_filtered.to_csv(index=False),
                        file_name="mazda_news.csv",
                        mime="text/csv"
                    )
            else:
                st.warning("⚠️ 記事が取得できませんでした。")
