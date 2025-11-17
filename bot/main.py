"""Entrypoint for the Polymarket yes/no arbitrage bot."""
from __future__ import annotations

import asyncio
import logging
from typing import Callable, Optional

from .config import Config
from .polymarket import PolymarketClient
from .telegram_client import TelegramNotifier
from .trader import Trader

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class ArbitrageBot:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.client = PolymarketClient()
        self.trader = Trader(cfg.polygon_rpc, cfg.private_key)
        self.notifier = TelegramNotifier(cfg.telegram_token, cfg.telegram_chat_id)
        self.auto_trade = cfg.auto_trade
        self._loop_running = True

    async def start(self) -> None:
        await self.notifier.start()
        await self.notifier.send_text("Polymarket 套利监控已上线。")
        await self._loop()

    async def shutdown(self) -> None:
        self._loop_running = False
        await self.notifier.stop()

    async def _loop(self) -> None:
        while self._loop_running:
            try:
                opportunities = self.client.find_arbitrage(self.cfg.price_threshold)
                for opp in opportunities:
                    await self._handle_opportunity(opp)
            except Exception:  # noqa: BLE001
                logger.exception("Error scanning for opportunities")
            await asyncio.sleep(self.cfg.poll_interval)

    async def _handle_opportunity(self, opportunity) -> None:
        text = f"发现套利: yes+no={opportunity.combined:.4f} < {self.cfg.price_threshold}\n" + opportunity.describe()
        logger.info(text)

        if self.auto_trade:
            await self._execute_trade(opportunity)
            return

        loop = asyncio.get_running_loop()
        decision_event = asyncio.Event()
        decision: dict[str, bool] = {"ok": False}

        def callback(ok: bool) -> None:
            decision["ok"] = ok
            loop.call_soon_threadsafe(decision_event.set)

        await self.notifier.notify_opportunity(text, callback)
        await decision_event.wait()
        if decision["ok"]:
            await self._execute_trade(opportunity)
        else:
            await self.notifier.send_text("用户拒绝或退出此次套利。")

    async def _execute_trade(self, opportunity) -> None:
        result = self.trader.execute(opportunity, self.cfg.trade_amount)
        await self.notifier.send_text(f"执行结果: {result.summary()}")


async def main() -> None:
    cfg = Config.load()
    bot = ArbitrageBot(cfg)
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("收到中断，正在退出……")
    finally:
        await bot.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
