import json
import random
from datetime import datetime, timedelta
import streamlit as st

RARITY_WEIGHTS = {"N": 45, "R": 30, "SR": 15, "SSR": 10}

MODES = {
    "自己肯定感を高めたい日": ["回復", "生活", "行動"],
    "勉強したい日": ["勉強", "回復", "生活"],
    "体を鍛えたい日": ["運動", "回復", "生活"],
    "生活を整える日": ["生活", "回復", "行動"],
    "お金・投資の日": ["お金", "勉強", "生活"],
    "行動力を上げたい日": ["行動", "運動", "回復"],
    "バランスよく過ごす日": ["勉強", "運動", "生活", "回復", "行動", "お金", "趣味"],
    "趣味を楽しむ日": ["趣味", "回復", "行動"],
}

MOODS = {
    "元気": ["easy", "medium", "hard"],
    "普通": ["easy", "medium"],
    "疲れている": ["easy"],
}

BREAK_CARD = {
    "name": "休憩",
    "minutes": 15,
    "rarity": "N",
    "place": "any",
    "cost": "free",
    "difficulty": "easy",
    "category": "休憩",
}

COMBOS = {
    "筋トレ": [
        {"name": "プロテイン補給", "minutes": 10, "rarity": "R", "place": "home", "cost": "low", "difficulty": "easy", "category": "運動"},
        {"name": "風呂でリカバリー", "minutes": 30, "rarity": "R", "place": "home", "cost": "free", "difficulty": "easy", "category": "回復"},
    ],
    "ランニング": [
        {"name": "ストレッチでクールダウン", "minutes": 15, "rarity": "R", "place": "home", "cost": "free", "difficulty": "easy", "category": "運動"},
    ],
    "Python基礎学習": [
        {"name": "学んだことを3行メモ", "minutes": 15, "rarity": "R", "place": "home", "cost": "free", "difficulty": "easy", "category": "勉強"},
    ],
}

def load_cards():
    with open("cards.json", "r", encoding="utf-8") as f:
        return json.load(f)

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

def filter_cards(cards, categories, difficulties, place_filter, cost_filter):
    filtered = [
        c for c in cards
        if c["category"] in categories
        and c["difficulty"] in difficulties
    ]

    if place_filter == "家だけ":
        filtered = [c for c in filtered if c["place"] == "home"]

    if cost_filter == "無料だけ":
        filtered = [c for c in filtered if c["cost"] == "free"]

    return filtered

def make_schedule(start, end, cards, enable_combo=True):
    current = start
    schedule = []
    minutes_since_break = 0
    ssr_used = False
    last_card = None

    while current < end:
        if minutes_since_break >= 90 and (not last_card or last_card["name"] != "休憩"):
            card = BREAK_CARD
        else:
            card = get_random_card(cards, ssr_used, last_card)

        finish = current + timedelta(minutes=card["minutes"])

        if finish > end:
            break

        schedule.append((current, finish, card))
        current = finish

        if card["name"] == "休憩":
            minutes_since_break = 0
        else:
            minutes_since_break += card["minutes"]

        if card["rarity"] == "SSR":
            ssr_used = True

        last_card = card

        if enable_combo and card["name"] in COMBOS:
            for combo_card in COMBOS[card["name"]]:
                combo_finish = current + timedelta(minutes=combo_card["minutes"])
                if combo_finish <= end:
                    schedule.append((current, combo_finish, combo_card))
                    current = combo_finish
                    last_card = combo_card

    return schedule

def schedule_to_text(schedule):
    lines = []
    for s, e, card in schedule:
        lines.append(
            f"{s.strftime('%H:%M')}-{e.strftime('%H:%M')} "
            f"{card['name']} [{card['rarity']}] "
            f"(場所:{card['place']} / 金額:{card['cost']} / 難易度:{card['difficulty']} / 種類:{card['category']})"
        )
    return "\n".join(lines)

def create_ai_prompt(schedule, start_time, end_time, mode, mood):
    return f"""
私はこれから以下のスケジュールで行動します。
各予定について、具体的に何をすればいいかを実行レベルまで落とし込んでください。

【今日のモード】
{mode}

【今の気分】
{mood}

【使える時間】
{start_time}〜{end_time}

【スケジュール】
{schedule_to_text(schedule)}

【お願いしたいこと】
・おすすめの場所
・使うべきサイトやツール
・具体的な手順
・注意点やコツ
・少し楽しくなる工夫
・無理のない現実的なプラン

なるべくお金を使わず、今日の満足度が上がる形で提案してください。
"""

st.set_page_config(page_title="生活ガチャ", page_icon="🎲")

st.title("🎲 生活ガチャ・スケジューラー")
st.write("気分と時間を選ぶと、今日の行動カードを自動で組みます。")

cards = load_cards()

start_time = st.time_input("開始時間", value=datetime.strptime("10:00", "%H:%M").time())
end_time = st.time_input("終了時間", value=datetime.strptime("18:00", "%H:%M").time())

mode = st.selectbox("今日のモード", list(MODES.keys()))
mood = st.selectbox("今の気分", list(MOODS.keys()))

place_filter = st.selectbox("場所フィルター", ["指定なし", "家だけ"])
cost_filter = st.selectbox("金額フィルター", ["指定なし", "無料だけ"])

enable_combo = st.checkbox("コンボを有効にする", value=True)

if st.button("ガチャを回す"):
    start = datetime.combine(datetime.today(), start_time)
    end = datetime.combine(datetime.today(), end_time)

    filtered_cards = filter_cards(
        cards,
        MODES[mode],
        MOODS[mood],
        place_filter,
        cost_filter
    )

    if not filtered_cards:
        st.error("条件に合うカードがありません。cards.jsonにカードを追加してください。")
    else:
        schedule = make_schedule(start, end, filtered_cards, enable_combo)

        st.subheader("今日のスケジュール")

        for s, e, card in schedule:
            rarity = card["rarity"]

            if rarity == "SSR":
                st.success(f"✨ {s.strftime('%H:%M')}-{e.strftime('%H:%M')} {card['name']} [{rarity}]")
            elif rarity == "SR":
                st.info(f"🔥 {s.strftime('%H:%M')}-{e.strftime('%H:%M')} {card['name']} [{rarity}]")
            else:
                st.write(f"{s.strftime('%H:%M')}-{e.strftime('%H:%M')} {card['name']} [{rarity}]")

            st.caption(
                f"場所:{card['place']} / 金額:{card['cost']} / 難易度:{card['difficulty']} / 種類:{card['category']}"
            )

        st.subheader("AIにコピペするプロンプト")
        st.text_area(
            "この文章をChatGPTに貼る",
            create_ai_prompt(schedule, start_time.strftime("%H:%M"), end_time.strftime("%H:%M"), mode, mood),
            height=300
        )