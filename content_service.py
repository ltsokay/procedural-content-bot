"""
ContentService — координатор генерации.

По типу контента из сессии пользователя выбирает нужный генератор
(MapGenerator / LootGenerator / NameGenerator), вызывает его и
возвращает результат. Сами генераторы ничего не знают друг о друге —
это и есть модульность, о которой написано в курсовой.
"""

from generators.map_generator import MapGenerator
from generators.loot_generator import LootGenerator
from generators.name_generator import NameGenerator
from session import UserSession


class ContentService:
    def __init__(self):
        self.map_generator = MapGenerator()
        self.loot_generator = LootGenerator()
        self.name_generator = NameGenerator()

    def generate(self, session: UserSession) -> dict:
        if session.content_type == "map":
            return self.map_generator.generate(
                size=session.size,
                theme=session.theme,
                difficulty=session.difficulty,
            )
        elif session.content_type == "loot":
            return self.loot_generator.generate(
                theme=session.theme,
                difficulty=session.difficulty,
            )
        elif session.content_type == "name":
            return self.name_generator.generate(theme=session.theme)
        else:
            raise ValueError(f"Неизвестный тип контента: {session.content_type}")

    def preview(self, result: dict) -> str:
        """Текстовое превью результата для отправки в чат."""
        if result.get("type") == "map":
            return self.map_generator.preview(result)
        elif result.get("type") == "loot":
            return self.loot_generator.preview(result)
        elif result.get("type") == "name":
            return self.name_generator.preview(result)
        return "Нет данных для предпросмотра."
