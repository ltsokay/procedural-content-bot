"""
UserSession — состояние одного пользователя.

Хранит текущие параметры генерации и последний полученный результат.
Благодаря этому пользователь может менять настройки по одной и в любой
момент сгенерировать контент или экспортировать последний результат.
"""

from dataclasses import dataclass, field


@dataclass
class UserSession:
    content_type: str = "map"        # что генерируем: map / loot / name
    theme: str = "fantasy"           # тема: fantasy / sci-fi / post-apocalyptic
    difficulty: str = "easy"         # сложность: easy / hard
    size: int = 10                   # размер карты (для типа map)
    last_result: dict = field(default_factory=dict)  # последний результат генерации
