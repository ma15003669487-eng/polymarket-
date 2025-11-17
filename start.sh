#!/usr/bin/env bash
set -euo pipefail

if [ ! -f .env ]; then
  echo "Missing .env file. Create one with TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, etc." >&2
  exit 1
fi

export $(grep -v '^#' .env | xargs)
python -m bot.main
