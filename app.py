import streamlit as st
import json
import os
from datetime import date, datetime
from dotenv import load_dotenv
import anthropic

# .envの読み込み
load_dotenv(override=True)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# データファイルのパス
DATA_FILE = "customers.json"

# 顧客データの読み込み
def load_customers():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

# 顧客データの保存
def save_customers(customers):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(customers, f, ensure_ascii=False, indent=2)

# AI返信生成
def generate_reply(customer, situation):
    situation_map = {
        "A. 来店翌日お礼": "昨日来店してくれたお客様への翌日のお礼メッセージ",
        "B. 久しぶりの再アプローチ": "しばらく来店がないお客様への再アプローチメッセージ",
        "C. 誕生日メッセージ": "お客様の誕生日を祝うメッセージ",
        "D. 来店を促す営業": "お客様に来店を促す営業メッセージ",
        "E. 受信メッセージへの返信": "お客様から届いたメッセージへの返信",
    }

    prompt = f"""あなたはキャバ嬢のLINE営業をサポートするAIです。
以下の顧客情報をもとに、自然で親しみやすいLINEメッセージを3パターン生成してください。

【シチュエーション】
{situation_map[situation]}

【顧客情報】
名前：{customer['name']}
年齢：{customer['age']}歳
職業：{customer['job']}
ランク：{customer['rank']}
最終来店日：{customer['last_visit']}
好きな話題：{customer['topics']}
苦手なこと：{customer['ng']}
前回の会話メモ：{customer['memo']}

【注意事項】
- タメ口と敬語を混ぜたキャバ嬢らしい自然な文体
- 絵文字を適度に使う
- 営業感を出しすぎない
- 必ず「【パターン1】」「【パターン2】」「【パターン3】」の3つだけ生成する
- 見出しや説明文は一切不要。各パターンの冒頭は必ずメッセージ本文から始める
"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

# メイン
st.title("Lina")
st.caption("キャバ嬢向けLINE営業AI支援ツール")

menu = st.sidebar.selectbox("メニュー", ["顧客一覧", "顧客追加", "AI返信生成", "売上管理", "設定"])

customers = load_customers()

# 顧客追加
if menu == "顧客追加":
    st.header("顧客追加")
    name = st.text_input("名前")
    age = st.number_input("年齢", min_value=0, max_value=100, value=30)
    job = st.text_input("職業")
    rank = st.selectbox("ランク", ["1軍", "2軍", "3軍"])
    last_visit = st.date_input("最終来店日", value=date.today())
    memo = st.text_area("前回の会話メモ")
    topics = st.text_input("好きな話題")
    ng = st.text_input("苦手なこと")
    appearance = st.text_area("見た目・特徴メモ")

    if st.button("保存"):
        new_customer = {
            "name": name,
            "age": age,
            "job": job,
            "rank": rank,
            "last_visit": str(last_visit),
            "memo": memo,
            "topics": topics,
            "ng": ng,
            "appearance": appearance,
            "visits": []
        }
        customers.append(new_customer)
        save_customers(customers)
        st.success(f"{name}さんを追加しました")

# 顧客一覧
if menu == "顧客一覧":
    st.header("顧客一覧")
    if not customers:
        st.info("顧客がまだいません。顧客追加から登録してください。")
    else:
        for i, c in enumerate(customers):
            st.subheader(f"{c['name']} ({c['rank']})")
            st.write(f"年齢：{c['age']}　職業：{c['job']}")
            st.write(f"最終来店日：{c['last_visit']}")
            st.write(f"好きな話題：{c['topics']}")
            st.write(f"特徴：{c['appearance']}")
            st.divider()

# AI返信生成
if menu == "AI返信生成":
    st.header("AI返信生成")
    if not customers:
        st.info("まず顧客を追加してください。")
    else:
        customer_names = [c["name"] for c in customers]
        selected_name = st.selectbox("顧客を選択", customer_names)
        selected_customer = next(c for c in customers if c["name"] == selected_name)

        situation = st.selectbox("シチュエーション", [
            "A. 来店翌日お礼",
            "B. 久しぶりの再アプローチ",
            "C. 誕生日メッセージ",
            "D. 来店を促す営業",
            "E. 受信メッセージへの返信",
        ])

        if situation == "E. 受信メッセージへの返信":
            received_message = st.text_area("受信したメッセージを入力")

        if st.button("返信を生成する"):
            with st.spinner("生成中..."):
                reply = generate_reply(selected_customer, situation)

            import re
            patterns = re.split(r'【パターン\d+】', reply)
            patterns = [p.strip() for p in patterns if p.strip()]

            for i, pattern in enumerate(patterns, 1):
                st.markdown(f"**パターン{i}**")
                st.code(pattern, language=None)

# 売上管理
if menu == "売上管理":
    st.header("売上管理")

    tab1, tab2 = st.tabs(["来店記録", "集計"])

    with tab1:
        st.subheader("来店記録を追加")
        if not customers:
            st.info("まず顧客を追加してください。")
        else:
            customer_names = [c["name"] for c in customers]
            selected_name = st.selectbox("顧客を選択", customer_names)
            visit_date = st.date_input("来店日", value=date.today())
            amount = st.number_input("使用金額（円）", min_value=0, step=1000, value=0)
            dohan = st.selectbox("同伴・アフター", ["なし", "同伴あり", "アフターあり", "同伴・アフター両方"])
            visit_memo = st.text_area("メモ")

            if st.button("来店記録を保存"):
                for c in customers:
                    if c["name"] == selected_name:
                        if "visits" not in c:
                            c["visits"] = []
                        c["visits"].append({
                            "date": str(visit_date),
                            "amount": amount,
                            "dohan": dohan,
                            "memo": visit_memo
                        })
                        c["last_visit"] = str(visit_date)
                        break
                save_customers(customers)
                st.success(f"{selected_name}さんの来店記録を保存しました")

    with tab2:
        st.subheader("集計")

        # 月次売上
        st.markdown("**月次売上合計**")
        month = st.selectbox("月を選択", [f"2026-{str(m).zfill(2)}" for m in range(1, 13)])
        monthly_total = 0
        for c in customers:
            for v in c.get("visits", []):
                if v["date"].startswith(month):
                    monthly_total += v["amount"]
        st.metric("合計", f"¥{monthly_total:,}")

        st.divider()

        # 顧客ごとの累計・ランキング
        ranking_data = []
        for c in customers:
            total = sum(v["amount"] for v in c.get("visits", []))
            count = len(c.get("visits", []))
            ranking_data.append({"name": c["name"], "rank": c["rank"], "total": total, "count": count})

        st.markdown("**金額ランキング**")
        sorted_by_amount = sorted(ranking_data, key=lambda x: x["total"], reverse=True)
        for i, d in enumerate(sorted_by_amount, 1):
            st.write(f"{i}位　{d['name']}（{d['rank']}）　¥{d['total']:,}")

        st.divider()

        st.markdown("**来店回数ランキング**")
        sorted_by_count = sorted(ranking_data, key=lambda x: x["count"], reverse=True)
        for i, d in enumerate(sorted_by_count, 1):
            st.write(f"{i}位　{d['name']}（{d['rank']}）　{d['count']}回")
 # 設定
if menu == "設定":
    st.header("設定")
    st.subheader("サブスクリプション")
    st.write("Linaをご利用いただくには月額サブスクリプションが必要です。")
    st.link_button("今すぐ登録する（¥1,980/月）", "https://buy.stripe.com/test_6oUeVcdD92kG5zh1o300000")
    st.divider()
    st.subheader("プレミアムプラン（近日公開）")
    st.info("誕生日アラート・ランク昇格提案・月次レポートなど追加機能を含むプレミアムプラン（¥4,980/月）を準備中です。")           