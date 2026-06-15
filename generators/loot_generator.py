"""
LootGenerator — генератор предметов (лута)

Метод (параметрическая генерация):
1. По уровню сложности выбираем редкость из таблицы вероятностей
   (на лёгком чаще common, на сложном чаще rare/epic/legendary)
2. По теме берём префикс и название предмета из тематических словарей
3. Считаем числовую "силу" предмета: базовое значение по редкости + случайная добавка
"""

import random

#Таблицы редкости: список с повторениями = распределение вероятностей
RARITY_TABLE = {
    "easy": ["common"] * 70 + ["rare"] * 25 + ["epic"] * 5,
    "hard": ["common"] * 30 + ["rare"] * 40 + ["epic"] * 22 + ["legendary"] * 8,
}

#Базовая сила по редкости
BASE_POWER = {
    "common": 10,
    "rare": 30,
    "epic": 60,
    "legendary": 90,
}

#Тематические словари: префиксы и базовые названия предметов
LOOT_THEMES = {
    "fantasy": {
        "prefixes": ["Ancient", "Cursed", "Holy", "Dragon", "Elven"],
        "items": ["Sword", "Shield", "Amulet", "Staff", "Ring"],
    },
    "sci-fi": {
        "prefixes": ["Plasma", "Quantum", "Cyber", "Nano", "Ion"],
        "items": ["Blaster", "Armor", "Module", "Drone", "Implant"],
    },
    "post-apocalyptic": {
        "prefixes": ["Rusty", "Scrap", "Makeshift", "Irradiated", "Salvaged"],
        "items": ["Pipe", "Vest", "Canteen", "Rifle", "Mask"],
    },
}


class LootGenerator:
    """Создаёт случайный предмет с именем, редкостью и силой"""

    def generate(self, theme: str, difficulty: str) -> dict:
        table = RARITY_TABLE.get(difficulty, RARITY_TABLE["easy"])
        rarity = random.choice(table)

        words = LOOT_THEMES.get(theme, LOOT_THEMES["fantasy"])
        name = f"{random.choice(words['prefixes'])} {random.choice(words['items'])}"

        # Сила = базовое значение по редкости + случайная добавка 0..10.
        power = BASE_POWER[rarity] + random.randint(0, 10)

        return {
            "type": "loot",
            "theme": theme,
            "difficulty": difficulty,
            "item": {
                "name": name,
                "rarity": rarity,
                "power": power,
            },
        }

    def preview(self, result: dict) -> str:
        item = result["item"]
        return (
            f"🎁 {item['name']}\n"
            f"Редкость: {item['rarity']}\n"
            f"Сила: {item['power']}"
        )
