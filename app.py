import json
import random
from datetime import datetime, timedelta
import streamlit as st

st.set_page_config(
    page_title="生活ガチャ",
    page_icon="🎲",
    layout="wide"
)

# =========================
# CSS
# =========================

st.markdown("""
<style>
body {
    background-color: #0f1117;
}

.main {
    background: linear-gradient(180deg, #0f1117 0%, #151928 100%);
    color: white;
}

.big-title {
    font-size: 56px;
    font-weight: 800;
    background: linear-gradient(90deg,#00ffd5,#7a5cff,#ff4fd8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}

.sub-title {
    color: #9ea3b0;
    font-size: 18px;
    margin-top: -10px;
    margin-bottom: 30px;
}

.card {
    padding: 18px;
    border-radius: 18px;
    margin-bottom: 16px;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(12px);
}

.rarity-n {
    border-left: 6px solid #7f8c8d;
}

.rarity-r {
    border-left: 6px solid #3498db;
}

.rarity-sr {
    border-left: 6px solid #9b59b6;
    box-shadow: 0 0 18px rgba(155,89,182,0.35);
}

.rarity-ssr {
    border-left: 6px solid gold;
    background: linear-gradient(135deg,#2b2300,#1a1a1a);
    box-shadow: 0 0 25px rgba(255,215,0,0.5);
}

.time {
    font-size: 20px;
    font-weight: bold;
}

.name {
    font-size: 28px;
    font-weight: 700;
}

.meta {
    color: #b7bcc7;
    margin-top: 8px;
    font-size: 14px;
}

.ssr-banner {
    text-align: center;
    padding: 16px;
    border-radius: 18px;
    background: linear-gradient(90deg,#ffd700,#ff9800);
    color: black;
    font-size: 26px;
    font-weight: 800;
    margin-bottom: 20px;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% {transform: scale(1);}
    50% {transform: scale(1.02);}
    100% {transform: scale(1);}
}

.stButton>button {
    width: 100%;
    background: linear-gradient(90deg,#00ffd5,#7a5cff);
    color: white;
    border: none;
    border-radius: 14px;
    padding: 14px;
    font-size: 20px;
    font-weight: bold;
}

.stButton>button:hover {
    transform: scale(1.02);
    transition: 0.2s;
}
</style>
""", unsafe_allow_html=True)

# =========================
# CONFIG
# =========================

RARITY_WEIGHTS = {
    "N": 45,
    "R": 30,
    "SR": 15,
    "SSR": 10
}

MODES = {
    "自己肯定感を高めたい日": ["回復", "生活", "行動"],
    "勉強したい日": ["勉強", "回復", "生活"],
    "体を鍛えたい日": ["運動", "回復", "生活"],
    "生活を整える日": ["生活", "回復", "行動"],
    "お金・投資の日": ["お金", "勉強", "生活"],
    "行動力を上げたい日": ["行動", "運動", "回復"],
    "趣味を楽しむ日": ["趣味", "回復", "行動"],
    "バランスよく過ごす日": ["勉強", "運動", "生活", "回復", "行動", "お金", "趣味"]
}

MOODS = {
    "元気": ["easy", "medium", "hard"],
    "普通": ["easy", "medium"],
    "疲れている": ["easy"]
}

BREAK_CARD = {
    "name": "休憩",
    "minutes": 15,
    "rarity": "N",
    "place": "any",
    "cost": "free",
    "difficulty": "easy",
    "category": "休憩"
}

# =========================
# LOAD
# =========================

def load_cards():
    with open("cards.json", "r", encoding="utf-8") as f:
        return json.load(f)

cards = load_cards()

# =========================
# FUNCTIONS
# =========================

def filter_cards(cards, categories, difficulties, free_only):
    filtered = [
        c for c in cards
        if c["category"] in categories
        and c["difficulty"] in difficulties
    ]

    if free_only:
        filtered = [c for c in filtered if c["cost"] == "free"]

    return filtered

def get_random_card(cards, ssr_used, last_card):
    for _ in range(50):

        rarity = random.choices(
            list(RARITY_WEIGHTS.keys()),
            weights=list(RARITY_WEIGHTS.values()),
            k=1
        )[0]

        if rarity == "SSR" and ssr_used:
            continue

        candidates = [c for c in cards if c["rarity"] == rarity]

        if last_card:
            candidates = [
                c for c in candidates
                if c["name"] != last_card["name"]
                and c["category"] != last_card["category"]
            ]

        if candidates:
            return random.choice(candidates)

    return random.choice(cards)

def make_schedule(start, end, cards):
    current = start
    schedule = []
    ssr_used = False
    last_card = None
    minutes_since_break = 0

    while current < end:

        if minutes_since_break >= 90:
            card = BREAK_CARD
            minutes_since_break = 0
        else:
            card = get_random_card(cards, ssr_used, last_card)

        finish = current + timedelta(minutes=card["minutes"])

        if finish > end:
            break

        schedule.append((current, finish, card))

        if card["rarity"] == "SSR":
            ssr_used = True

        current = finish
        last_card = card

        if card["name"] != "休憩":
            minutes_since_break += card["minutes"]

    return schedule

# =========================
# UI
# =========================

st.markdown("<div class='big-title'>🎲 LIFE GACHA</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>今日をゲームみたいに生きる。</div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    start_time = st.time_input(
        "開始時間",
        value=datetime.strptime("10:00", "%H:%M").time()
    )

with col2:
    end_time = st.time_input(
        "終了時間",
        value=datetime.strptime("18:00", "%H:%M").time()
    )

mode = st.selectbox("今日のモード", list(MODES.keys()))
mood = st.selectbox("今の気分", list(MOODS.keys()))

free_only = st.checkbox("無料だけにする")

if st.button("🎰 ガチャを回す"):

    start = datetime.combine(datetime.today(), start_time)
    end = datetime.combine(datetime.today(), end_time)

    filtered_cards = filter_cards(
        cards,
        MODES[mode],
        MOODS[mood],
        free_only
    )

    schedule = make_schedule(start, end, filtered_cards)

    st.markdown("---")
    st.subheader("📅 今日のスケジュール")

    for s, e, card in schedule:

        rarity_class = {
            "N": "rarity-n",
            "R": "rarity-r",
            "SR": "rarity-sr",
            "SSR": "rarity-ssr"
        }[card["rarity"]]

        if card["rarity"] == "SSR":
            st.markdown(
                f"<div class='ssr-banner'>✨ SSR EVENT : {card['name']} ✨</div>",
                unsafe_allow_html=True
            )

        st.markdown(f"""
        <div class='card {rarity_class}'>
            <div class='time'>
                {s.strftime('%H:%M')} - {e.strftime('%H:%M')}
            </div>

            <div class='name'>
                {card['name']} [{card['rarity']}]
            </div>

            <div class='meta'>
                📍 {card['place']}　
                💰 {card['cost']}　
                ⚡ {card['difficulty']}　
                🧩 {card['category']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.success("🎉 スケジュール生成完了")