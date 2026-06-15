"""
ExportService — экспорт результата в JSON и XML.

Генераторы возвращают обычные словари Python, поэтому:
- JSON получается одной стандартной функцией json.dumps;
- XML строится через дерево xml.etree.ElementTree.
Генераторы не знают, в каком формате их результат будет выгружен — за это
отвечает только этот модуль.
"""

import json
import xml.etree.ElementTree as ET


class ExportService:
    def to_json(self, data: dict) -> str:
        return json.dumps(data, ensure_ascii=False, indent=2)

    def to_xml(self, data: dict) -> str:
        root = ET.Element("result")
        self._build(root, data)
        # ET.indent делает XML с отступами (Python 3.9+).
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode")

    def _build(self, parent: ET.Element, value):
        """Рекурсивно превращает словарь/список/значение в XML-узлы."""
        if isinstance(value, dict):
            for key, sub in value.items():
                child = ET.SubElement(parent, str(key))
                self._build(child, sub)
        elif isinstance(value, list):
            for item in value:
                child = ET.SubElement(parent, "item")
                self._build(child, item)
        else:
            parent.text = str(value)
