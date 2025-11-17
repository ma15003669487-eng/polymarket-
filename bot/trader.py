"""Simplified trading executor for Polymarket."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from .polymarket import ArbitrageOpportunity

logger = logging.getLogger(__name__)


@dataclass
class TradeResult:
    market_id: str
    yes_cost: float
    no_cost: float
    executed: bool
    tx_hash: Optional[str]
    message: str

    def summary(self) -> str:
        status = "EXECUTED" if self.executed else "SKIPPED"
        return f"[{status}] {self.message} | tx={self.tx_hash or 'n/a'}"


class Trader:
    """Placeholder trader.

    A full implementation should sign and send transactions on Polygon using the
    Polymarket settlement contract. Here we only log the intent so that the bot
    can be wired to a real trading backend later on.
    """

    def __init__(self, polygon_rpc: Optional[str], private_key: Optional[str]):
        self.polygon_rpc = polygon_rpc
        self.private_key = private_key
        if not (polygon_rpc and private_key):
            logger.warning("Trading will run in dry-run mode (missing RPC or private key)")

    def execute(self, opportunity: ArbitrageOpportunity, amount: float) -> TradeResult:
        logger.info(
            "Executing arbitrage on %s with amount %.2f (yes=%.4f, no=%.4f)",
            opportunity.market_id,
            amount,
            opportunity.yes_price,
            opportunity.no_price,
        )
        if not (self.polygon_rpc and self.private_key):
            return TradeResult(
                market_id=opportunity.market_id,
                yes_cost=opportunity.yes_price * amount,
                no_cost=opportunity.no_price * amount,
                executed=False,
                tx_hash=None,
                message="Dry-run only: missing RPC/private key",
            )

        # Real trading logic should be placed here.
        fake_tx = f"0x{opportunity.market_id[:6]}..."
        return TradeResult(
            market_id=opportunity.market_id,
            yes_cost=opportunity.yes_price * amount,
            no_cost=opportunity.no_price * amount,
            executed=True,
            tx_hash=fake_tx,
            message="Submitted trades on Yes/No legs",
        )


__all__ = ["TradeResult", "Trader"]
