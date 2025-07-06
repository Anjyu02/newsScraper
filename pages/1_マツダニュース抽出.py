def scrape_articles_mazda(year, start_date, end_date):
    print(f"🚗 scrape_articles_mazda 開始: {year}年（{start_date.date()}〜{end_date.date()}）")
    driver = generate_driver()
    data = []

    url = f"https://www.mazda.co.jp/news_list/{year}/"
    print(f"🌐 アクセスURL: {url}")
    driver.get(url)
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    box = soup.find("div", class_="Notification__list__box2")

    if not box:
        print("⚠️ ニュース一覧が見つかりません")
        return pd.DataFrame()

    dls = box.find_all("dl")
    for dl in dls:
        try:
            date = dl.find("dt").get_text(strip=True)
            date_obj = pd.to_datetime(date, format="%Y年%m月%d日", errors="coerce")
            if pd.isna(date_obj):
                continue

            # ✅ 範囲外スキップ処理（JTEKT同様、新しい順と仮定）
            if date_obj < end_date:
                print(f"🛑 {date} は範囲より古いため打ち切り")
                break
            elif date_obj > start_date:
                print(f"⏩ {date} は範囲より新しいためスキップ")
                continue

            link_tag = dl.find("dd").find("a")
            title = link_tag.get_text(strip=True)
            href = link_tag["href"]
            full_link = f"https://www.mazda.co.jp{href}"

            # ✅ 本文取得（新しいタブ）
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            driver.get(full_link)

            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "detail-content"))
            )
            detail_soup = BeautifulSoup(driver.page_source, "html.parser")
            content_div = detail_soup.select_one("div.detail-content")

            if content_div:
                body_text = extract_content_text(content_div)
            else:
                body_text = "本文抽出不可"

            data.append({
                "日付": date,
                "見出し": title,
                "本文": body_text.strip(),
                "リンク": full_link
            })

            print(f"✅ 抽出成功: {title}")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)

        except Exception as e:
            print(f"⚠️ エラー: {e}")
            traceback.print_exc()
            try:
                driver.switch_to.window(driver.window_handles[0])
            except:
                pass
            continue

    driver.quit()
    return pd.DataFrame(data)
