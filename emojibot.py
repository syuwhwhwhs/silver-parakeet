
#!/usr/bin/env python3
# RoXeT Emoji Extractor - Bot API Edition

import asyncio
import io
import logging
import re
from pathlib import Path

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
LOG = logging.getLogger("roxet-emoji")

SAVE_DIR = Path("emoji_files")
SAVE_DIR.mkdir(exist_ok=True)


def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("✨ استخراج با ایموجی", callback_data="extract"),
            InlineKeyboardButton("🔎 جستجو با ID", callback_data="search_id"),
        ],
        [
            InlineKeyboardButton("📘 راهنما", callback_data="help"),
            InlineKeyboardButton("💎 درباره RoXeT", callback_data="about"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="home")]
    ])


def safe_filename(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name or "emoji")
    return name[:100] or "emoji"


def sticker_filename(sticker, index=0):
    if getattr(sticker, "is_animated", False):
        ext = ".tgs"
    elif getattr(sticker, "is_video", False):
        ext = ".webm"
    else:
        ext = ".webp"

    return safe_filename(f"roxet_emoji_{index}{ext}")


async def is_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_id = context.application.bot_data.get("owner_id")
    user = update.effective_user
    return bool(user and owner_id and user.id == owner_id)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_owner(update, context):
        await update.effective_message.reply_text(
            "⛔ این ربات خصوصی است و فقط صاحب ربات اجازه استفاده دارد."
        )
        return

    await update.effective_message.reply_text(
        "💎 به RoXeT Emoji Extractor خوش آمدی!\n\n"
        "ایموجی سفارشی را بفرست یا از منوی زیر استفاده کن.",
        reply_markup=main_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await is_owner(update, context):
        await query.edit_message_text("⛔ دسترسی غیرمجاز است.")
        return

    action = query.data

    if action == "home":
        context.user_data.pop("waiting_for_id", None)
        await query.edit_message_text(
            "💎 منوی اصلی RoXeT",
            reply_markup=main_menu()
        )

    elif action == "extract":
        context.user_data.pop("waiting_for_id", None)
        await query.edit_message_text(
            "✨ یک ایموجی سفارشی را در پیام بعدی ارسال کن.",
            reply_markup=back_menu()
        )

    elif action == "search_id":
        context.user_data["waiting_for_id"] = True
        await query.edit_message_text(
            "🔎 شناسه عددی Custom Emoji را ارسال کن:",
            reply_markup=back_menu()
        )

    elif action == "help":
        await query.edit_message_text(
            "📘 راهنمای RoXeT\n\n"
            "۱. برای استخراج، یک ایموجی سفارشی بفرست.\n"
            "۲. برای جست‌وجو، گزینه جستجو با ID را بزن.\n"
            "۳. شناسه ایموجی باید عددی باشد.\n"
            "۴. در صورت پشتیبانی Bot API، فایل اصلی دریافت می‌شود.\n\n"
            "فرمت‌های قابل دریافت: TGS / WEBM / WEBP",
            reply_markup=back_menu()
        )

    elif action == "about":
        await query.edit_message_text(
            "💎 RoXeT Emoji Extractor\n\n"
            "استخراج ایموجی‌های سفارشی تلگرام\n"
            "ساخته شده با Python و Telegram Bot API",
            reply_markup=back_menu()
        )


async def extract_by_id(
    chat_id: int,
    emoji_id: int,
    context: ContextTypes.DEFAULT_TYPE
):
    try:
        stickers = await context.bot.get_custom_emoji_stickers(
            custom_emoji_ids=[emoji_id]
        )

        if not stickers:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ تلگرام برای این شناسه فایلی برنگرداند."
            )
            return

        for index, sticker in enumerate(stickers, start=1):
            filename = sticker_filename(sticker, index)

            telegram_file = await context.bot.get_file(sticker.file_id)
            file_bytes = await telegram_file.download_as_bytearray()

            if not file_bytes:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ دریافت فایل ناموفق بود."
                )
                continue

            # ارسال خود استیکر، در صورت پشتیبانی
            try:
                await context.bot.send_sticker(
                    chat_id=chat_id,
                    sticker=sticker.file_id
                )
            except Exception:
                LOG.warning("Sticker preview could not be sent")

            # ارسال فایل با پسوند اصلی
            file_object = io.BytesIO(bytes(file_bytes))
            file_object.name = filename

            await context.bot.send_document(
                chat_id=chat_id,
                document=file_object,
                filename=filename,
                caption=(
                    f"💎 RoXeT Emoji Extractor\n"
                    f"🆔 Custom Emoji ID: {emoji_id}\n"
                    f"📁 File: {filename}"
                )
            )

    except Exception as exc:
        LOG.exception("Extraction failed")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ خطا هنگام استخراج:\n{type(exc).__name__}: {exc}"
        )


async def emoji_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    msg = update.effective_message

    if not await is_owner(update, context):
        if msg:
            await msg.reply_text("⛔ فقط صاحب ربات اجازه استفاده دارد.")
        return

    if not msg or not msg.text:
        return

    # جست‌وجو با ID
    if context.user_data.get("waiting_for_id"):
        context.user_data["waiting_for_id"] = False

        match = re.fullmatch(r"\s*(\d+)\s*", msg.text)
        if not match:
            await msg.reply_text("❌ شناسه باید فقط شامل عدد باشد.")
            return

        emoji_id = int(match.group(1))
        await msg.reply_text(
            f"🔎 شناسه: {emoji_id}\n⏳ در حال دریافت فایل..."
        )
        await extract_by_id(msg.chat_id, emoji_id, context)
        return

    # استخراج ID از موجودیت ایموجی سفارشی
    entities = msg.entities or []
    custom_ids = [
        int(entity.custom_emoji_id)
        for entity in entities
        if getattr(entity, "type", None) == "custom_emoji"
        and getattr(entity, "custom_emoji_id", None)
    ]

    if not custom_ids:
        await msg.reply_text(
            "❌ ایموجی سفارشی پیدا نشد.\n"
            "یک Premium Custom Emoji را مستقیم در پیام ارسال کن."
        )
        return

    emoji_id = custom_ids[0]

    await msg.reply_text(
        f"🔎 شناسه پیدا شد: {emoji_id}\n"
        "⏳ در حال دریافت فایل..."
    )

    await extract_by_id(msg.chat_id, emoji_id, context)


async def post_init(application: Application):
    owner_id = application.bot_data["owner_id"]
    LOG.info("RoXeT bot started. Owner ID: %s", owner_id)


def main():
    print("=== RoXeT Emoji Extractor ===")

    bot_token = input("Bot Token: ").strip()
    owner_text = input("Owner Telegram ID: ").strip()

    if not bot_token:
        raise SystemExit("Bot Token is required.")

    try:
        owner_id = int(owner_text)
    except ValueError:
        raise SystemExit("Owner ID must be numeric.")

    app = (
        Application.builder()
        .token(bot_token)
        .post_init(post_init)
        .build()
    )

    app.bot_data["owner_id"] = owner_id

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, emoji_handler)
    )

    print("RoXeT is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
