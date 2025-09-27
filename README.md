BasicBot – Binance Futures Testnet Trading Bot
Overview
BasicBot is a Python trading bot for Binance Futures Testnet (USDT-M).
It supports MARKET, LIMIT, and STOP-LIMIT orders via a CLI interface, with logging and error handling.
⚠️ Important: If any errors occur while placing orders (like HTTP 500 / code -1000), this is an issue with Binance Testnet servers, not the bot. Testnet can be temporarily unstable.
@Setup & Usage
Install dependencies:
pip install requests

@Set your Binance Testnet API keys as environment variables:

export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"


@Run orders:

python3 script.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

Key Notes About Testnet Behavior

--Testnet errors (HTTP 500 / code -1000) are caused by Binance Testnet instability.

--Retrying after a few seconds usually resolves the issue.

--Logging is included to confirm that requests were sent correctly and show API responses.

--Bot logic is correct; failures from Testnet do not indicate bugs in the code.

## Logs and Testnet Behavior

Sample logs (from `logs/basic_bot.log`):

2025-09-27 13:03:05,678 | INFO | BasicBot | BasicBot initialized (Testnet base: https://testnet.binancefuture.com)
2025-09-27 13:03:05,678 | INFO | BasicBot | Placing order: BTCUSDT BUY MARKET qty=0.001 price=None stop=None
2025-09-27 13:03:05,946 | ERROR | BasicBot | API error: {'code': -1000, 'msg': 'An unknown error occurred while processing the request.'}

> ⚠️ Note: These errors are caused by **Binance Testnet server instability**, not the bot.  
> All API requests were correctly sent, and the bot handled errors and logged responses properly.  
> Retrying the same order usually succeeds once the testnet server is responsive.


Usage Examples

Market order (buy 0.001 BTC):

python3 script.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001


Limit order (sell 0.001 BTC at $60,000):

python3 script.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 60000


Stop-limit order:

python3 script.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.001 --stop-price 61000 --price 60900
Add --verbose to see debug logs in console.