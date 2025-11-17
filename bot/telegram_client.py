"""Telegram bot utilities for notification and manual confirmations."""
from __future__ import annotations

import logging
from typing import Callable, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackContext, CallbackQueryHandler, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, token: str, chat_id: Optional[int] = None):
        self.chat_id = chat_id
        self.app = Application.builder().token(token).build()
        self._confirm_handler: Optional[Callable[[str], None]] = None

    async def start(self) -> None:
        await self.app.initialize()
        self.app.add_handler(CommandHandler("start", self._start))
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        await self.app.start()

    async def stop(self) -> None:
        await self.app.stop()

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.chat_id = self.chat_id or update.effective_chat.id
        await update.message.reply_text(
            "套利机器人已启动。使用固定按钮确认或取消交易。",
            reply_markup=self._reply_keyboard(),
        )

    def _reply_keyboard(self) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("✅ 执行", callback_data="confirm")],
            [InlineKeyboardButton("⛔ 跳过", callback_data="skip")],
            [InlineKeyboardButton("🤖 自动交易", callback_data="auto_on")],
            [InlineKeyboardButton("🙅‍♂️ 手动确认", callback_data="auto_off")],
        ]
        return InlineKeyboardMarkup(keyboard)

    async def notify_opportunity(self, text: str, callback: Callable[[bool], None]) -> None:
        if not self.chat_id:
            logger.warning("Missing chat_id; message not sent")
            return
        self._confirm_handler = lambda decision: callback(decision)
        await self.app.bot.send_message(
            chat_id=self.chat_id,
            text=text,
            reply_markup=self._reply_keyboard(),
        )

    async def send_text(self, text: str) -> None:
        if not self.chat_id:
            logger.warning("Missing chat_id; message not sent")
            return
        await self.app.bot.send_message(chat_id=self.chat_id, text=text)

    async def _handle_callback(self, update: Update, context: CallbackContext) -> None:
        if not self._confirm_handler:
            await update.callback_query.answer("没有待处理的套利请求")
            return
        data = update.callback_query.data
        await update.callback_query.answer()
        if data == "confirm":
            self._confirm_handler(True)
        elif data == "skip":
            self._confirm_handler(False)
        elif data == "auto_on":
            self._confirm_handler(True)
            await self.send_text("已切换为自动交易")
        elif data == "auto_off":
            self._confirm_handler(False)
            await self.send_text("已切换为手动确认")


__all__ = ["TelegramNotifier"]
