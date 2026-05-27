import json
import random
from datetime import datetime, timedelta

MODES = {
    "1": {"name": "自己肯定感を高めたい日", "categories": ["回復", "生活", "行動"]},
    "2": {"name": "勉強したい日", "categories": ["勉強", "回復", "生活"]},
    "3": {"name": "体を鍛えたい日", "categories": ["運動", "回復", "生活"]},
    "4": {"name": "生活を整える日", "categories": ["生活", "回復", "行動"]},
    "5": {"name": "お金・投資の日", "categories": ["お金", "勉強", "生活"]},
    "6": {"name": "行動力を上げたい日", "categories": ["行動", "運動", "回復"]},
    "7": {"name": "バランスよく過ごす日", "categories": ["勉強", "運動", "生活", "回復", "行動"]},
}

MOODS = {
    "1": {"name": "元気", "difficulty": ["easy", "medium", "hard"]},
    "2": {"name": "普通", "difficulty": ["easy", "medium"]},
    "3": {"name": "疲れている", "difficulty": ["easy"]},
}

RARITY_WEIGHTS = {
    "N": 45,
    "R": 30,
    "SR": 15,
    "SSR": 10
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

def load_cards():
    with open("cards.json", "r", encoding="utf-8") as f:
        return json.load(f)

def to_time(text):
    return datetime.strptime(text, "%H:%M")

def filter_cards(cards, mode, mood):
    categories = mode["categories"]
    difficulties = mood["difficulty"]

    filtered = [
        card for card in cards
        if card["category"] in categories
        and card["difficulty"] in difficulties
    ]

    return filtered

def get_random_card(cards, ssr_used, last_card):
    rarities = list(RARITY_WEIGHTS.keys())
    weights = list(RARITY_WEIGHTS.values())

    for _ in range(50):
        selected_rarity = random.choices(rarities, weights=weights, k=1)[0]

        if selected_rarity == "SSR" and ssr_used:
            continue

        candidates = [c for c in cards if c["rarity"] == selected_rarity]

        if last_card:
            candidates = [
                c for c in candidates
                if c["name"] != last_card["name"]
            ]

        if candidates:
            return random.choice(candidates)

    return random.choice(cards)

def make_schedule(start, end, cards):
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

        if finish <= end:
            schedule.append((current, finish, card))
            current = finish

            if card["name"] == "休憩":
                minutes_since_break = 0
            else:
                minutes_since_break += card["minutes"]

            if card["rarity"] == "SSR":
                ssr_used = True

            last_card = card
        else:
            break

    return schedule

def schedule_to_text(schedule):
    lines = []

    for start, end, card in schedule:
        lines.append(
            f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')} "
            f"{card['name']} [{card['rarity']}] "
            f"(場所:{card['place']} / 金額:{card['cost']} / 難易度:{card['difficulty']} / 種類:{card['category']})"
        )

    return "\n".join(lines)

def create_ics(schedule):
    today = datetime.today().strftime("%Y%m%d")

    ics = "BEGIN:VCALENDAR\n"
    ics += "VERSION:2.0\n"
    ics += "PRODID:-//Life Gacha Schedule//JP\n"

    for start, end, card in schedule:
        ics += "BEGIN:VEVENT\n"
        ics += f"SUMMARY:{card['name']} [{card['rarity']}]\n"
        ics += f"DTSTART:{today}T{start.strftime('%H%M%S')}\n"
        ics += f"DTEND:{today}T{end.strftime('%H%M%S')}\n"
        ics += "END:VEVENT\n"

    ics += "END:VCALENDAR\n"

    with open("schedule.ics", "w", encoding="utf-8") as f:
        f.write(ics)

def create_ai_prompt(schedule, start_time, end_time, mode, mood):
    return f"""
私はこれから以下のスケジュールで行動します。
各予定について、具体的に何をすればいいかを実行レベルまで落とし込んでください。

【今日のモード】
{mode["name"]}

【今の気分】
{mood["name"]}

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

def main():
    cards = load_cards()

    start_time_str = input("開始時間（例 10:00）: ")
    end_time_str = input("終了時間（例 18:00）: ")

    start = to_time(start_time_str)
    end = to_time(end_time_str)

    print("\n今日のモードを選んでください")
    for key, value in MODES.items():
        print(f"{key}. {value['name']}")

    mode = MODES[input("番号: ")]

    print("\n今の気分を選んでください")
    for key, value in MOODS.items():
        print(f"{key}. {value['name']}")

    mood = MOODS[input("番号: ")]

    filtered_cards = filter_cards(cards, mode, mood)

    if not filtered_cards:
        print("条件に合うカードがありません。cards.jsonにカードを追加してください。")
        return

    while True:
        schedule = make_schedule(start, end, filtered_cards)

        print("\n--- 生活ガチャ・スケジュール ---")
        print(schedule_to_text(schedule))

        answer = input("\nこのスケジュールでOKですか？ y=OK / n=作り直し: ")

        if answer.lower() == "y":
            break

    print("\n--- AIにコピペするプロンプト ---")
    print(create_ai_prompt(schedule, start_time_str, end_time_str, mode, mood))

    create_ics(schedule)

    print("Googleカレンダー用の schedule.ics を作成しました。")

if __name__ == "__main__":
    main()
