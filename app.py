import streamlit as st
import os
from datetime import date
from dotenv import load_dotenv
import anthropic
from supabase import create_client, Client

# .envの読み込み
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Supabaseクライアント
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# 顧客データの読み込み
def load_customers():
    res = supabase.table("customers").select("*").execute()
    return res.data

# 顧客データの保存
def save_customer(customer):
    supabase.table("customers").insert(customer).execute()

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
- 各パターンは「【パターン1】」「【パターン2】」「【パターン3】」と見出しをつける
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

menu = st.sidebar.selectbox("メニュー", ["顧客一覧", "顧客追加", "AI返信生成"])

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
        save_customer(new_customer)
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
            st.markdown(reply)