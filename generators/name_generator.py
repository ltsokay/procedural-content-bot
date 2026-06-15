"""
NameGenerator — генератор имён персонажей на марковских цепях.

Метод - марковская модель:
1. Из тематического корпуса имён строим модель переходов: по двум подряд
   идущим символам (контексту) запоминаем, какие символы встречались следующими
2. При генерации идём по цепочке: имея последние два символа, случайно
   выбираем следующий по собранной статистике — пока не дойдём до конца
Получаются новые имена, похожие по стилю на исходные, но не совпадающие с ними
"""

import random

#Тематические корпусы имён — на их основе обучается марковская модель
NAME_CORPUS = {
    "fantasy": [
        "eldorin", "aragorn", "galadriel", "thalion", "morwen", "elrohir",
        "celeborn", "finduilas", "isildur", "lothlorien", "gandalf", "arwen",
    ],
    "sci-fi": [
        "zarknel", "vextor", "cyrion", "nexus", "orbion", "quarrik",
        "syntara", "drelvon", "kaelix", "tronix", "veyra", "xenor",
    ],
    "post-apocalyptic": [
        "raider", "scrapper", "ashen", "duster", "cinder", "wraith",
        "ratter", "vulture", "grimm", "hollow", "rustok", "drifter",
    ],
}

#Спецсимволы начала/конца имени для марковской модели
START = "^"
END = "$"
ORDER = 2  #Длина контекста (марковская цепь порядка 2 по символам)


class NameGenerator:
    """Строит новое имя на основе марковской модели по тематическому корпусу."""

    def __init__(self):
        #Кэшируем обученные модели по темам, чтобы не строить заново каждый раз
        self._models = {}

    def _build_model(self, theme: str) -> dict:
        corpus = NAME_CORPUS.get(theme, NAME_CORPUS["fantasy"])
        model = {}
        for word in corpus:
            padded = START * ORDER + word + END
            for i in range(len(padded) - ORDER):
                context = padded[i:i + ORDER]
                next_char = padded[i + ORDER]
                model.setdefault(context, []).append(next_char)
        return model

    def generate(self, theme: str) -> dict:
        if theme not in self._models:
            self._models[theme] = self._build_model(theme)
        model = self._models[theme]

        #Генерируем, пока не получим имя приемлемой длины
        for _ in range(20):
            context = START * ORDER
            result = ""
            for _ in range(20):  #Ограничение длины
                choices = model.get(context)
                if not choices:
                    break
                next_char = random.choice(choices)
                if next_char == END:
                    break
                result += next_char
                context = (context + next_char)[-ORDER:]
            if 3 <= len(result) <= 12:
                break

        name = result.capitalize() if result else "Unnamed"
        return {
            "type": "name",
            "theme": theme,
            "value": name,
        }

    def preview(self, result: dict) -> str:
        return f"🧙 Имя персонажа: {result['value']}"
