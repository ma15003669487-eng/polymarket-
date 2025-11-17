# Polymarket 套利机器人

功能概览：
- 扫描全部 Polymarket 市场，发现 `Yes+No < 阀值` 的机会。
- Telegram 推送套利机会，底部固定按钮可一键执行/跳过。
- 支持手动确认或自动交易模式，可自定义阀值和下单金额。
- 可选创建钱包/交易：提供私钥与 Polygon RPC 即可从脚本内执行；缺省时自动进入 dry-run。
- `start.sh` 一键启动（读取 `.env`）。

## 快速开始
1. 安装依赖
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. 配置环境变量（`.env` 示例）
   ```bash
   TELEGRAM_TOKEN=123456:ABCDEF
   TELEGRAM_CHAT_ID=123456789  # 目标群/私聊 ID
   POLYGON_RPC=https://polygon-mainnet.infura.io/v3/<api-key>
   PRIVATE_KEY=0xabc...        # 用于下单的私钥
   PRICE_THRESHOLD=0.99        # 触发套利的阀值
   TRADE_AMOUNT=10             # 每条腿下单金额（USDC）
   POLL_INTERVAL=30            # 轮询秒数
   AUTO_TRADE=false            # true 切到自动交易
   ```
3. 运行
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

启动后在 Telegram 发送 `/start`，会收到固定按钮：✅ 执行、⛔ 跳过、🤖 自动交易、🙅‍♂️ 手动确认。

## 代码结构
- `bot/config.py`：加载所有可调参数。
- `bot/polymarket.py`：调用 CLOB API 获取市场与订单簿，筛选 `yes+no<阀值` 套利。
- `bot/telegram_client.py`：Telegram 推送与按钮回调。
- `bot/trader.py`：交易执行（默认 dry-run，预留真实链上调用接口）。
- `bot/main.py`：主循环与手动/自动模式控制。

## 风险提示
- 真实交易前请先在测试环境/dry-run 验证，确保 RPC、私钥、Gas 与滑点设置正确。
- Polymarket API/订单簿结构可能调整，必要时更新 `bot/polymarket.py` 的解析逻辑。
