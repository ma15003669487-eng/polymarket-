"""Configuration helpers for the Polymarket arbitrage bot."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Runtime configuration loaded from environment variables.

    Attributes:
        telegram_token: Bot token obtained from @BotFather.
        telegram_chat_id: Chat ID to notify. If omitted, the bot will reply only to active chats.
        polygon_rpc: RPC URL for submitting on-chain trades.
        private_key: Private key for signing transactions.
        price_threshold: Max allowed sum of yes+no prices to trigger arbitrage (e.g. 0.99).
        trade_amount: Amount of collateral (USDC) to commit per leg.
        poll_interval: Seconds between price refreshes.
        auto_trade: Whether to automatically execute without manual confirmation.
    """

    telegram_token: str
    telegram_chat_id: Optional[int]
    polygon_rpc: Optional[str]
    private_key: Optional[str]
    price_threshold: float = 0.99
    trade_amount: float = 10.0
    poll_interval: int = 30
    auto_trade: bool = False

    @classmethod
    def load(cls) -> "Config":
        def getenv_float(name: str, default: float) -> float:
            val = os.getenv(name)
            return float(val) if val is not None else default

        def getenv_int(name: str, default: int) -> int:
            val = os.getenv(name)
            return int(val) if val is not None else default

        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        return cls(
            telegram_token=os.environ["TELEGRAM_TOKEN"],
            telegram_chat_id=int(telegram_chat_id) if telegram_chat_id else None,
            polygon_rpc=os.getenv("POLYGON_RPC"),
            private_key=os.getenv("PRIVATE_KEY"),
            price_threshold=getenv_float("PRICE_THRESHOLD", 0.99),
            trade_amount=getenv_float("TRADE_AMOUNT", 10.0),
            poll_interval=getenv_int("POLL_INTERVAL", 30),
            auto_trade=os.getenv("AUTO_TRADE", "false").lower() in {"1", "true", "yes"},
        )


__all__ = ["Config"]
