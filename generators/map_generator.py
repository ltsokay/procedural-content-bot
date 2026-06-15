"""
MapGenerator — генератор карт.

Идея (как и описано в курсовой): для каждой клетки карты считаем значение
шума Перлина, а затем по пороговым значениям превращаем число в тип
поверхности (вода / равнина / лес / горы). Названия поверхностей зависят
от выбранной темы (fantasy, sci-fi, post-apocalyptic).
"""

import random

from generators.perlin import pnoise2

# Базовые "категории" рельефа -> как они называются в каждой теме.
TILE_THEMES = {
    "fantasy": {
        "water": "water",
        "plain": "plain",
        "forest": "forest",
        "mountain": "mountain",
    },
    "sci-fi": {
        "water": "coolant",
        "plain": "platform",
        "forest": "biozone",
        "mountain": "reactor",
    },
    "post-apocalyptic": {
        "water": "toxic_pool",
        "plain": "wasteland",
        "forest": "ruins",
        "mountain": "rubble",
    },
}

# Плотность опасных зон (врагов) в зависимости от сложности.
ENEMY_DENSITY = {
    "easy": 0.05,
    "hard": 0.15,
}


class MapGenerator:
    """Строит двумерную карту тайлов и матрицу опасных зон."""

    def generate(self, size: int, theme: str, difficulty: str, scale: float = 10.0) -> dict:
        names = TILE_THEMES.get(theme, TILE_THEMES["fantasy"])
        density = ENEMY_DENSITY.get(difficulty, 0.05)

        # Случайный сдвиг, чтобы каждая генерация давала новую карту.
        offset_x = random.uniform(0, 1000)
        offset_y = random.uniform(0, 1000)

        tiles = []
        enemies = []
        for y in range(size):
            row = []
            enemy_row = []
            for x in range(size):
                value = pnoise2((x + offset_x) / scale, (y + offset_y) / scale)
                if value < -0.1:
                    row.append(names["water"])
                elif value < 0.2:
                    row.append(names["plain"])
                elif value < 0.5:
                    row.append(names["forest"])
                else:
                    row.append(names["mountain"])
                # Враг может появиться только не на воде.
                is_enemy = row[-1] != names["water"] and random.random() < density
                enemy_row.append(1 if is_enemy else 0)
            tiles.append(row)
            enemies.append(enemy_row)

        return {
            "type": "map",
            "theme": theme,
            "difficulty": difficulty,
            "size": size,
            "map": tiles,
            "enemies": enemies,
        }

    def preview(self, result: dict) -> str:
        """Короткое текстовое превью карты символами (для отправки в чат)."""
        symbols = {
            "water": "~", "coolant": "~", "toxic_pool": "~",
            "plain": ".", "platform": ".", "wasteland": ".",
            "forest": "#", "biozone": "#", "ruins": "#",
            "mountain": "^", "reactor": "^", "rubble": "^",
        }
        lines = []
        for row in result["map"]:
            lines.append("".join(symbols.get(tile, "?") for tile in row))
        return "\n".join(lines)
