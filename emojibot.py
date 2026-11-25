
import os
import re
import getpass
import logging
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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)

BOT_NAME = "RoXeT Emoji Extractor"
DOWNLOAD_DIR = Path("emoji_files")
DOWNLOAD_DIR.mkdir(exist_ok=True)

EMOJI_ID_PATTERN = re.compile(r"\d{5,}")

# -------------------- MENU --------------------

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton(
                "✨ استخراج با ایموجی",
                callback_data="extract",
            )
        ],
        [
            InlineKeyboardButton(
                "🔎 جستجو با ID",
                callback_data="search",
            )
        ],
        [
            InlineKeyboardButton(
                "📘 راهنما",
                callback_data="help",
            ),
            InlineKeyboardButton(
                "💎 درباره ربات",
                callback_data="about",
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔙 بازگشت به منو",
                callback_data="home",
            )
        ]
    ])


# -------------------- OWNER CHECK --------------------

def is_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_id = context.application.bot_data.get("owner_id")
    user = update.effective_user

    return bool(
        user
        and owner_id
        and user.id == owner_id
    )


async def reject_user(update: Update):
    message = update.effective_message

    if message:
        await message.reply_text(
            "⛔ این ربات خصوصی است و فقط مالک می‌تواند از آن استفاده کند."
        )


# -------------------- START --------------------

async def start_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_owner(update, context):
        await reject_user(update)
        return

    context.user_data["mode"] = None

    await update.message.reply_text(
        "💎 به RoXeT Emoji Extractor خوش آمدی!\n\n"
        "✨ استخراج ایموجی‌های سفارشی تلگرام\n"
        "📦 دریافت فایل‌های قابل پشتیبانی\n\n"
        "یکی از گزینه‌های زیر را انتخاب کن:",
        reply_markup=main_menu(),
    )


# -------------------- BUTTONS --------------------

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    if not is_owner(update, context):
        await query.edit_message_text(
            "⛔ دسترسی غیرمجاز است."
        )
        return

    data = query.data

    if data == "home":
        context.user_data["mode"] = None

        await query.edit_message_text(
            "💎 منوی اصلی RoXeT\n\n"
            "یک گزینه انتخاب کن:",
            reply_markup=main_menu(),
        )

    elif data == "extract":
        context.user_data["mode"] = "extract"

        await query.edit_message_text(
            "✨ استخراج با ایموجی\n\n"
            "یک پیام حاوی ایموجی سفارشی تلگرام "
            "برای ربات ارسال کن.\n\n"
            "ربات شناسه ایموجی را بررسی می‌کند.",
            reply_markup=back_menu(),
        )

    elif data == "search":
        context.user_data["mode"] = "search"

        await query.edit_message_text(
            "🔎 جستجو با ID\n\n"
            "شناسه عددی ایموجی سفارشی را ارسال کن:",
            reply_markup=back_menu(),
        )

    elif data == "help":
        await query.edit_message_text(
            "📘 راهنمای استفاده\n\n"
            "1️⃣ برای استخراج، گزینه استخراج با ایموجی را بزن.\n"
            "2️⃣ یک پیام دارای ایموجی سفارشی بفرست.\n"
            "3️⃣ برای جستجو با شناسه، گزینه جستجو با ID را بزن.\n"
            "4️⃣ فایل در صورت پشتیبانی تلگرام ارسال می‌شود.\n\n"
            "⚠️ فقط ایموجی‌های سفارشی قابل شناسایی هستند.",
            reply_markup=back_menu(),
        )

    elif data == "about":
        await query.edit_message_text(
            "💎 RoXeT Emoji Extractor\n\n"
            "نسخه: 1.0\n"
            "ساخته شده برای استخراج ایموجی سفارشی تلگرام\n\n"
            "Powered by RoXeT",
            reply_markup=back_menu(),
        )


# -------------------- DOWNLOAD --------------------

def get_file_extension(sticker):
    if sticker.is_video:
        return ".webm"

    if sticker.is_animated:
        return ".tgs"

    return ".webp"


async def extract_emoji(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    emoji_id: str,
):
    message = update.effective_message

    status = await message.reply_text(
        "⏳ در حال دریافت اطلاعات ایموجی..."
    )

    try:
        stickers = await context.bot.get_custom_emoji_stickers(
            custom_emoji_ids=[emoji_id]
        )

        if not stickers:
            await status.edit_text(
                "❌ ایموجی پیدا نشد یا از طریق Bot API قابل دریافت نیست."
            )
            return

        sticker = stickers[0]

        extension = get_file_extension(sticker)
        file_path = DOWNLOAD_DIR / f"{emoji_id}{extension}"

        telegram_file = await context.bot.get_file(sticker.file_id)

        await telegram_file.download_to_drive(
            custom_path=str(file_path)
        )

        await status.edit_text(
            "✅ ایموجی دریافت شد.\n"
            "📤 در حال ارسال فایل..."
        )

        if sticker.is_video:
            await message.reply_video_sticker(
                sticker=str(file_path)
            )
        elif sticker.is_animated:
            await message.reply_animation(
                animation=str(file_path)
            )
        else:
            await message.reply_sticker(
                sticker=str(file_path)
            )

        with open(file_path, "rb") as file:
            await message.reply_document(
                document=file,
                filename=file_path.name,
                caption=(
                    "💎 RoXeT Emoji Extractor\n"
                    f"🆔 ID: {emoji_id}\n"
                    f"📁 Format: {extension}"
                ),
            )

        await status.edit_text(
            "✅ عملیات با موفقیت انجام شد."
        )

    except Exception as error:
        logging.exception("Emoji extraction failed")

        await status.edit_text(
            "❌ دریافت ایموجی ناموفق بود.\n\n"
            f"جزئیات: {str(error)[:700]}"
        )

    finally:
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass


# -------------------- MESSAGE HANDLER --------------------

async def emoji_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_owner(update, context):
        await reject_user(update)
        return

    message = update.effective_message
    mode = context.user_data.get("mode")

    emoji_ids = []

    # Detect custom emoji in message entities
    if message.entities:
        for entity in message.entities:
            if entity.type == "custom_emoji":
                if entity.custom_emoji_id:
                    emoji_ids.append(
                        str(entity.custom_emoji_id)
                    )

    if message.caption_entities:
        for entity in message.caption_entities:
            if entity.type == "custom_emoji":
                if entity.custom_emoji_id:
                    emoji_ids.append(
                        str(entity.custom_emoji_id)
                    )

    # Search by numeric ID
    if mode == "search":
        match = EMOJI_ID_PATTERN.search(message.text or "")

        if not match:
            await message.reply_text(
                "❌ شناسه معتبر ارسال کن."
            )
            return

        emoji_ids = [match.group(0)]

    elif mode == "extract":
        if not emoji_ids:
            await message.reply_text(
                "❌ ایموجی سفارشی پیدا نشد.\n"
                "یک پیام دارای Custom Emoji ارسال کن."
            )
            return

    else:
        await message.reply_text(
            "برای شروع از منوی /start استفاده کن."
        )
        return

    # Remove duplicate IDs
    emoji_ids = list(dict.fromkeys(emoji_ids))

    if not emoji_ids:
        await message.reply_text(
            "❌ شناسه ایموجی پیدا نشد."
        )
        return

    for emoji_id in emoji_ids[:10]:
        await extract_emoji(
            update,
            context,
            emoji_id,
        )


# -------------------- MAIN --------------------

def main():
    print()
    print("=" * 38)
    print("       RoXeT Emoji Extractor")
    print("=" * 38)
    print()

    bot_token = getpass.getpass(
        "Bot Token (hidden): "
    ).strip()

    owner_text = input(
        "Owner Telegram ID: "
    ).strip()

    if not bot_token:
        raise SystemExit("Bot Token is required.")

    try:
        owner_id = int(owner_text)
    except ValueError:
        raise SystemExit("Owner ID must be numeric.")

    application = (
        Application.builder()
        .token(bot_token)
        .build()
    )

    application.bot_data["owner_id"] = owner_id

    application.add_handler(
        CommandHandler("start", start_cmd)
    )

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            emoji_handler,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.TEXT,
            emoji_handler,
        )
    )

    print()
    print("RoXeT is running...")
    print("Press CTRL+C to stop.")
    print()

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
