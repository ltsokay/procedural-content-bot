"""
ProceduralBot — Telegram-бот «Генератор процедурного контента».

Точка входа в программу. Отвечает за приём команд и нажатий inline-кнопок,
хранение состояния пользователей (UserSession) и отправку результатов.
Сама генерация делегируется ContentService, экспорт — ExportService.

Запуск:
    1. Получить токен у @BotFather в Telegram.
    2. Вписать его в переменную TOKEN ниже (или в переменную окружения BOT_TOKEN).
    3. pip install -r requirements.txt
    4. python procedural_content_bot.py
"""

import html
import io
import logging
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from session import UserSession
from content_service import ContentService
from export_service import ExportService

# Впишите сюда токен от @BotFather (или задайте переменную окружения BOT_TOKEN).
TOKEN = os.environ.get("BOT_TOKEN", "ВСТАВЬТЕ_СЮДА_ТОКЕН")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Хранилище состояний пользователей: ключ — id пользователя Telegram.
USER_STATE: dict[int, UserSession] = {}

content_service = ContentService()
export_service = ExportService()

# Доступные значения параметров (для inline-кнопок).
THEMES = ["fantasy", "sci-fi", "post-apocalyptic"]
DIFFICULTIES = ["easy", "hard"]
CONTENT_TYPES = ["map", "loot", "name"]
SIZES = [10, 20, 30]


def get_session(user_id: int) -> UserSession:
    """Возвращает сессию пользователя, создавая её при первом обращении."""
    if user_id not in USER_STATE:
        USER_STATE[user_id] = UserSession()
    return USER_STATE[user_id]


def main_keyboard(session: UserSession) -> InlineKeyboardMarkup:
    """Формирует основную клавиатуру с учётом текущих параметров (галочкой ✅)."""

    def row(prefix, current, options):
        return [
            InlineKeyboardButton(
                ("✅ " if str(opt) == str(current) else "") + str(opt),
                callback_data=f"{prefix}:{opt}",
            )
            for opt in options
        ]

    keyboard = [
        row("type", session.content_type, CONTENT_TYPES),
        row("theme", session.theme, THEMES),
        row("diff", session.difficulty, DIFFICULTIES),
    ]
    # Размер карты показываем только для типа "map".
    if session.content_type == "map":
        keyboard.append(row("size", session.size, SIZES))
    keyboard.append([InlineKeyboardButton("🎲 Сгенерировать", callback_data="generate")])
    keyboard.append([
        InlineKeyboardButton("⬇️ JSON", callback_data="export:json"),
        InlineKeyboardButton("⬇️ XML", callback_data="export:xml"),
    ])
    return InlineKeyboardMarkup(keyboard)


def settings_text(session: UserSession) -> str:
    text = (
        "Текущие параметры:\n"
        f"• Тип контента: {session.content_type}\n"
        f"• Тема: {session.theme}\n"
        f"• Сложность: {session.difficulty}\n"
    )
    if session.content_type == "map":
        text += f"• Размер карты: {session.size}×{session.size}\n"
    return text


# ---------------- Обработчики команд ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_user.id)
    text = (
        "👋 Генератор процедурного контента\n\n"
        "Я генерирую игровые карты, лут и имена персонажей.\n"
        "Выберите параметры на кнопках ниже и нажмите «Сгенерировать».\n\n"
        + settings_text(session)
    )
    await update.message.reply_text(text, reply_markup=main_keyboard(session))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n"
        "/start — меню и параметры\n"
        "/generate — сгенерировать с текущими параметрами\n"
        "/settings — показать выбранные параметры\n"
        "/export_json — последний результат в JSON\n"
        "/export_xml — последний результат в XML"
    )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_user.id)
    await update.message.reply_text(settings_text(session), reply_markup=main_keyboard(session))


async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_user.id)
    await _do_generate(session, update.message)


async def export_json_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_user.id)
    await _do_export(session, "json", update.message)


async def export_xml_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_user.id)
    await _do_export(session, "xml", update.message)


# ---------------- Обработчик нажатий на кнопки ----------------

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = get_session(query.from_user.id)
    data = query.data

    if data == "generate":
        await _do_generate(session, query.message)
        return
    if data.startswith("export:"):
        await _do_export(session, data.split(":")[1], query.message)
        return

    # Иначе это изменение параметра вида "ключ:значение".
    key, value = data.split(":")
    if key == "type":
        session.content_type = value
    elif key == "theme":
        session.theme = value
    elif key == "diff":
        session.difficulty = value
    elif key == "size":
        session.size = int(value)

    # Перерисовываем клавиатуру с обновлёнными галочками.
    await query.edit_message_text(
        "👋 Генератор процедурного контента\n\n" + settings_text(session),
        reply_markup=main_keyboard(session),
    )


# ---------------- Общие действия ----------------

async def _do_generate(session: UserSession, message):
    try:
        result = content_service.generate(session)
    except ValueError as e:
        await message.reply_text(f"Ошибка: {e}")
        return
    session.last_result = result
    preview = content_service.preview(result)
    # Карту оборачиваем в моноширинный блок, чтобы сетка не "ехала".
    # html.escape — чтобы спецсимволы не сломали HTML-разметку Telegram.
    if result.get("type") == "map":
        await message.reply_text(f"<pre>{html.escape(preview)}</pre>", parse_mode="HTML")
    else:
        await message.reply_text(preview)


async def _do_export(session: UserSession, fmt: str, message):
    if not session.last_result:
        # Обработка ошибки: экспорт до генерации.
        await message.reply_text("Сначала сгенерируйте контент, потом экспортируйте.")
        return
    if fmt == "json":
        text = export_service.to_json(session.last_result)
    else:
        text = export_service.to_xml(session.last_result)

    # Отправляем результат ФАЙЛОМ, а не текстом: карта в JSON/XML может быть
    # длиннее лимита Telegram (~4096 символов), и текстовое сообщение упало бы.
    # io.BytesIO — это файл в памяти, его не нужно сохранять на диск.
    content_type = session.last_result.get("type", "result")
    file_bytes = io.BytesIO(text.encode("utf-8"))
    file_bytes.name = f"{content_type}.{fmt}"
    await message.reply_document(document=file_bytes, filename=f"{content_type}.{fmt}")


def main():
    if TOKEN == "ВСТАВЬТЕ_СЮДА_ТОКЕН":
        raise SystemExit(
            "Не задан токен. Получите его у @BotFather и впишите в переменную TOKEN "
            "или в переменную окружения BOT_TOKEN."
        )

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("generate", generate_command))
    app.add_handler(CommandHandler("export_json", export_json_command))
    app.add_handler(CommandHandler("export_xml", export_xml_command))
    app.add_handler(CallbackQueryHandler(on_button))

    logging.info("Бот запущен. Нажмите Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()
