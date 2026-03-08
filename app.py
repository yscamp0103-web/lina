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

# カスタムCSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400&family=Noto+Sans+JP:wght@400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans JP', sans-serif;
}

.stApp {
    background: #0a0a0a;
}

section[data-testid="stSidebar"] {
    background: #111111;
    border-right: 1px solid #333333;
}

section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

.logo-container {
    text-align: center;
    padding: 40px 0 30px 0;
}

.logo-title {
    font-family: 'Cormorant Garamond', serif;
    font-weight: 300;
    font-size: 4rem;
    color: #e8d5b0;
    letter-spacing: 0.05em;
    line-height: 1;
    margin: 0;
}

.logo-line {
    width: 200px;
    height: 1px;
    background: #e8d5b0;
    margin: 12px auto;
    opacity: 0.6;
}

.logo-sub {
    font-family: 'Cormorant Garamond', serif;
    font-weight: 300;
    font-size: 0.85rem;
    color: #888888;
    letter-spacing: 0.25em;
    text-transform: uppercase;
}

.customer-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 12px;
}

.customer-name {
    font-size: 1.1rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 8px;
}
.customer-info {
    color: rgba(255,255,255,0.85);
    font-size: 0.9rem;
    margin-top: 8px;
    line-height: 1.8;
}


.stButton > button {
    background: #e8d5b0 !important;
    color: #0a0a0a !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 25px !important;
    padding: 0.5rem 2rem !important;
    width: 100%;
}

.stButton > button:hover {
    opacity: 0.85 !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background: #1a1a1a !important;
    border: 1px solid #333333 !important;
    color: white !important;
    border-radius: 10px !important;
}

.stMarkdown p, label, .stSelectbox label {
    color: rgba(255,255,255,0.85) !important;
}

.section-title {
    color: #ffffff;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    border-bottom: 1px solid #2a2a2a;
    padding-bottom: 10px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

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
st.markdown("""
<div class="logo-container">
    <div class="logo-title">Lina</div>
    <div class="logo-line"></div>
    <div class="logo-sub">AI Messaging Assistant</div>
</div>
""", unsafe_allow_html=True)

menu = st.sidebar.selectbox("メニュー", ["顧客一覧", "顧客追加", "AI返信生成"])

customers = load_customers()

# 顧客追加
if menu == "顧客追加":
    st.markdown('<div class="section-title">✨ 顧客追加</div>', unsafe_allow_html=True)
    name = st.text_input("名前")
    age = st.number_input("年齢", min_value=0, max_value=100, value=30)
    job = st.text_input("職業")
    rank = st.selectbox("ランク", ["1軍", "2軍", "3軍"])
    last_visit = st.date_input("最終来店日", value=date.today())
    memo = st.text_area("前回の会話メモ")
    topics = st.text_input("好きな話題")
    ng = st.text_input("苦手なこと")
    appearance = st.text_area("見た目・特徴メモ")

    if st.button("保存する"):
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
        st.success(f"✅ {name}さんを追加しました")

# 顧客一覧
if menu == "顧客一覧":
    st.markdown('<div class="section-title">👑 顧客一覧</div>', unsafe_allow_html=True)
    if not customers:
        st.info("顧客がまだいません。顧客追加から登録してください。")
    else:
        for c in customers:
            st.markdown(f"""
            <div class="customer-card">
                <div class="customer-name">
                    {c['name']}
                    <span class="customer-rank">{c['rank']}</span>
                </div>
                <div class="customer-info">
                    🎂 {c['age']}歳　💼 {c['job']}<br>
                    📅 最終来店：{c['last_visit']}<br>
                    💬 好きな話題：{c.get('topics', 'ー')}<br>
                    ✨ 特徴：{c.get('appearance', 'ー')}
                </div>
            </div>
            """, unsafe_allow_html=True)

# AI返信生成
if menu == "AI返信生成":
    st.markdown('<div class="section-title">🤖 AI返信生成</div>', unsafe_allow_html=True)
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

        if st.button("返信を生成する ✨"):
            with st.spinner("生成中..."):
                reply = generate_reply(selected_customer, situation)

            patterns = reply.split("【パターン")
            for i, pattern in enumerate(patterns[1:], 1):
                text = pattern.split("】", 1)[-1].strip()
                st.markdown(f"**【パターン{i}】**")
                st.code(text, language=None)