
# RoXeT Emoji Extractor 💎

Private Telegram Custom Emoji Extractor.

## Features

- Persian interface
- Colored Inline Buttons
- Blue, Green and Red button styles
- Custom Emoji ID detection
- Search by Custom Emoji ID
- Telethon MTProto integration
- Original document download
- TGS, WEBM and WEBP support
- Sticker preview when supported
- Private owner-only access

## Requirements

- Ubuntu 22.04 / 24.04
- Python 3.10+
- Telegram Bot Token
- Telegram API ID and API HASH
- Owner Telegram ID
- Telegram phone number

## Installation

```bash
sudo apt update
sudo apt install -y python3-venv

python3 -m venv .venv

.venv/bin/pip install --upgrade pip

.venv/bin/pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python emojibot.py
```

Enter your credentials when prompted.

## Usage

1. Open your bot.
2. Send /start.
3. Select Extract Emoji or Search by ID.
4. Send a custom emoji or numeric ID.
5. Receive the original document when accessible.

## Security

Never upload your Telegram session file,
Bot Token or API HASH to GitHub.

Keep your Telegram session private.
