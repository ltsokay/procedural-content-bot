"""
Модульные тесты ядра бота (генераторы, сервисы, состояние, экспорт).

Запуск:
    python -m unittest discover -s tests        # без зависимостей (stdlib)
или, если установлен pytest / coverage:
    coverage run -m pytest && coverage report

Тесты не затрагивают сетевой слой Telegram — проверяется бизнес-логика
генерации, маршрутизации и сериализации.
"""

import json
import unittest
import xml.etree.ElementTree as ET

from session import UserSession
from content_service import ContentService
from export_service import ExportService
from generators.map_generator import MapGenerator, TILE_THEMES
from generators.loot_generator import LootGenerator, RARITY_TABLE, BASE_POWER
from generators.name_generator import NameGenerator
from generators.perlin import pnoise2, BACKEND


class TestUserSession(unittest.TestCase):
    def test_defaults(self):
        s = UserSession()
        self.assertEqual(s.content_type, "map")
        self.assertEqual(s.theme, "fantasy")
        self.assertEqual(s.difficulty, "easy")
        self.assertEqual(s.size, 10)
        self.assertEqual(s.last_result, {})

    def test_last_result_is_independent(self):
        a, b = UserSession(), UserSession()
        a.last_result["x"] = 1
        self.assertEqual(b.last_result, {})  # у каждого свой словарь


class TestPerlin(unittest.TestCase):
    def test_returns_float_in_range(self):
        v = pnoise2(1.5, 2.5)
        self.assertIsInstance(v, float)
        self.assertGreaterEqual(v, -1.5)
        self.assertLessEqual(v, 1.5)

    def test_backend_reported(self):
        self.assertIsInstance(BACKEND, str)
        self.assertTrue(len(BACKEND) > 0)


class TestMapGenerator(unittest.TestCase):
    def setUp(self):
        self.g = MapGenerator()

    def test_dimensions(self):
        r = self.g.generate(size=8, theme="fantasy", difficulty="easy")
        self.assertEqual(r["type"], "map")
        self.assertEqual(len(r["map"]), 8)
        self.assertTrue(all(len(row) == 8 for row in r["map"]))
        self.assertEqual(len(r["enemies"]), 8)

    def test_tiles_belong_to_theme(self):
        r = self.g.generate(size=10, theme="sci-fi", difficulty="hard")
        allowed = set(TILE_THEMES["sci-fi"].values())
        for row in r["map"]:
            for tile in row:
                self.assertIn(tile, allowed)

    def test_no_enemy_on_water(self):
        names = TILE_THEMES["fantasy"]
        r = self.g.generate(size=12, theme="fantasy", difficulty="hard")
        for y, row in enumerate(r["map"]):
            for x, tile in enumerate(row):
                if tile == names["water"]:
                    self.assertEqual(r["enemies"][y][x], 0)

    def test_unknown_theme_falls_back(self):
        r = self.g.generate(size=5, theme="unknown", difficulty="easy")
        allowed = set(TILE_THEMES["fantasy"].values())
        self.assertTrue(all(t in allowed for row in r["map"] for t in row))

    def test_preview_lines(self):
        r = self.g.generate(size=6, theme="fantasy", difficulty="easy")
        preview = self.g.preview(r)
        self.assertEqual(len(preview.splitlines()), 6)


class TestLootGenerator(unittest.TestCase):
    def setUp(self):
        self.g = LootGenerator()

    def test_rarity_and_power(self):
        for _ in range(50):
            r = self.g.generate(theme="fantasy", difficulty="hard")
            item = r["item"]
            self.assertIn(item["rarity"], BASE_POWER)
            self.assertGreaterEqual(item["power"], BASE_POWER[item["rarity"]])
            self.assertLessEqual(item["power"], BASE_POWER[item["rarity"]] + 10)
            self.assertEqual(len(item["name"].split()), 2)  # префикс + предмет

    def test_easy_has_no_legendary(self):
        rarities = {self.g.generate("fantasy", "easy")["item"]["rarity"] for _ in range(200)}
        self.assertNotIn("legendary", rarities)

    def test_unknown_theme_falls_back(self):
        r = self.g.generate(theme="unknown", difficulty="easy")
        self.assertEqual(r["type"], "loot")

    def test_preview(self):
        r = self.g.generate("sci-fi", "easy")
        self.assertIn(r["item"]["name"], self.g.preview(r))


class TestNameGenerator(unittest.TestCase):
    def setUp(self):
        self.g = NameGenerator()

    def test_returns_capitalized_name(self):
        for theme in ("fantasy", "sci-fi", "post-apocalyptic"):
            r = self.g.generate(theme)
            self.assertEqual(r["type"], "name")
            self.assertTrue(r["value"][0].isupper())
            self.assertLessEqual(len(r["value"]), 12)

    def test_model_is_cached(self):
        self.g.generate("fantasy")
        self.assertIn("fantasy", self.g._models)

    def test_unknown_theme_falls_back(self):
        r = self.g.generate("unknown")
        self.assertTrue(len(r["value"]) > 0)

    def test_preview(self):
        r = self.g.generate("fantasy")
        self.assertIn(r["value"], self.g.preview(r))


class TestContentService(unittest.TestCase):
    def setUp(self):
        self.cs = ContentService()

    def test_routes_each_type(self):
        for ctype in ("map", "loot", "name"):
            s = UserSession(content_type=ctype)
            self.assertEqual(self.cs.generate(s)["type"], ctype)

    def test_unknown_type_raises(self):
        s = UserSession(content_type="bogus")
        with self.assertRaises(ValueError):
            self.cs.generate(s)

    def test_preview_routes(self):
        for ctype in ("map", "loot", "name"):
            s = UserSession(content_type=ctype)
            self.assertIsInstance(self.cs.preview(self.cs.generate(s)), str)

    def test_preview_unknown_fallback(self):
        self.assertIsInstance(self.cs.preview({"type": "???"}), str)


class TestExportService(unittest.TestCase):
    def setUp(self):
        self.ex = ExportService()
        self.cs = ContentService()

    def test_json_roundtrip(self):
        r = self.cs.generate(UserSession(content_type="loot"))
        parsed = json.loads(self.ex.to_json(r))
        self.assertEqual(parsed["type"], "loot")

    def test_xml_is_valid(self):
        r = self.cs.generate(UserSession(content_type="name"))
        root = ET.fromstring(self.ex.to_xml(r))
        self.assertEqual(root.tag, "result")

    def test_xml_handles_nested_map(self):
        r = self.cs.generate(UserSession(content_type="map", size=5))
        root = ET.fromstring(self.ex.to_xml(r))  # вложенные списки не должны падать
        self.assertIsNotNone(root.find("map"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
