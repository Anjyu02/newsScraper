import streamlit as st

st.set_page_config(
    page_title="ニュース抽出アプリ",
    page_icon="📰",
    layout="wide"
)

st.title("🚗 自動車ニュース抽出アプリ")

st.markdown("""
このアプリでは、各自動車メーカーのニュースを自動で収集し、一覧表示します。  
左側のメニューから企業名を選んでください。
""")

st.markdown("### 📂 対応ページ一覧")
st.markdown("- 📘 [マツダ ニュース抽出](./pages/1_マツダニュース抽出.py)")
st.markdown("- 📗 [JTEKT ニュース抽出](./pages/2_JTEKTニュース抽出.py)")
