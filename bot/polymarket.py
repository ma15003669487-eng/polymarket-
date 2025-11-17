"""Helpers for fetching Polymarket markets and spotting arbitrage."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class Outcome:
    market_id: str
    question: str
    outcome: str
    yes_price: float
    no_price: float
    volume: float

    @property
    def combined(self) -> float:
        """Return yes_price + no_price."""
        return self.yes_price + self.no_price


@dataclass
class ArbitrageOpportunity:
    market_id: str
    question: str
    yes_price: float
    no_price: float

    @property
    def combined(self) -> float:
        return self.yes_price + self.no_price

    def describe(self) -> str:
        edge = 1 - self.combined
        return (
            f"{self.question}\n"
            f"Yes: {self.yes_price:.4f} | No: {self.no_price:.4f} | Edge: {edge:.4%}\n"
            f"Sum (yes+no): {self.combined:.4f}"
        )


class PolymarketClient:
    """Lightweight client for Polymarket public markets."""

    BASE_URL = "https://clob.polymarket.com"

    def __init__(self, session: Optional[requests.Session] = None):
        self._session = session or requests.Session()

    def _get(self, path: str, **params) -> dict:
        url = f"{self.BASE_URL}{path}"
        logger.debug("GET %s params=%s", url, params)
        response = self._session.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def fetch_outcomes(self) -> List[Outcome]:
        """Fetch all markets and extract best yes/no prices.

        The CLOB API exposes `markets` with an orderbook summary. We pick the best
        ask for buying Yes and No as our cost basis.
        """

        payload = self._get("/markets", limit=500)
        markets: Iterable[dict] = payload.get("markets", []) if isinstance(payload, dict) else []

        outcomes: List[Outcome] = []
        for market in markets:
            if market.get("closed") or market.get("takerMarketMakerFee") is None:
                continue

            question = market.get("question", "")
            market_id = market.get("id") or market.get("slug") or question
            book = market.get("orderbook", {})
            yes_price = self._best_price(book, "yes")
            no_price = self._best_price(book, "no")
            if yes_price is None or no_price is None:
                continue

            outcomes.append(
                Outcome(
                    market_id=market_id,
                    question=question,
                    outcome=market.get("outcomeType", ""),
                    yes_price=yes_price,
                    no_price=no_price,
                    volume=float(market.get("volume", 0.0)),
                )
            )

        logger.info("Fetched %d outcomes", len(outcomes))
        return outcomes

    @staticmethod
    def _best_price(orderbook: dict, side: str) -> Optional[float]:
        # Orderbook may contain aggregated levels under bids/asks keyed by side
        # We assume asks represent our buy price.
        try:
            book_side = orderbook.get("asks" if side == "yes" else "bids", [])
            if not book_side:
                return None
            return float(book_side[0]["price"])
        except Exception:  # noqa: BLE001
            logger.exception("Failed to parse orderbook side %s", side)
            return None

    def find_arbitrage(self, threshold: float) -> List[ArbitrageOpportunity]:
        """Return markets where yes+no is below the provided threshold."""
        opportunities: List[ArbitrageOpportunity] = []
        for outcome in self.fetch_outcomes():
            if outcome.combined < threshold:
                opportunities.append(
                    ArbitrageOpportunity(
                        market_id=outcome.market_id,
                        question=outcome.question,
                        yes_price=outcome.yes_price,
                        no_price=outcome.no_price,
                    )
                )
        opportunities.sort(key=lambda opp: opp.combined)
        return opportunities
