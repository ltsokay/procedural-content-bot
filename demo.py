"""
demo.py — быстрая проверка работоспособности БЕЗ Telegram и без токена.

Запуск:  python demo.py

Скрипт прогоняет все три генератора и экспорт, чтобы убедиться,
что логика проекта работает на вашей машине.
"""

from generators.perlin import BACKEND
from content_service import ContentService
from export_service import ExportService
from session import UserSession

cs = ContentService()
ex = ExportService()

print("Шум Перлина:", BACKEND)
print("=" * 40)

# 1) Карта
print("\n[1] КАРТА (fantasy, hard, 12x12):")
s = UserSession(content_type="map", theme="fantasy", difficulty="hard", size=12)
result = cs.generate(s)
print(cs.preview(result))
print("Условные знаки: ~ вода, . равнина, # лес, ^ горы")

# 2) Лут
print("\n[2] ЛУТ (sci-fi, hard):")
s = UserSession(content_type="loot", theme="sci-fi", difficulty="hard")
result = cs.generate(s)
print(cs.preview(result))

# 3) Имена (марковская цепь)
print("\n[3] ИМЕНА (fantasy) — 5 штук:")
s = UserSession(content_type="name", theme="fantasy")
for _ in range(5):
    print("  -", cs.generate(s)["value"])

# 4) Экспорт последнего результата
print("\n[4] ЭКСПОРТ последнего имени в JSON:")
print(ex.to_json(result))
print("\n[4] ЭКСПОРТ последнего имени в XML:")
print(ex.to_xml(result))

print("\n" + "=" * 40)
print("Если вы видите карту, предмет, имена, JSON и XML — всё работает!")
