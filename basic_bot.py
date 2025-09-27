#!/usr/bin/env python3
"""
basic_bot.py

Simplified Binance Futures (USDT-M) Testnet trading bot.

- Uses direct REST signed calls against https://testnet.binancefuture.com
- Supports MARKET, LIMIT, and STOP_LIMIT (Stop-Limit) order types
- CLI interface with input validation
- Logging of requests, responses, and errors
"""

import os
import time
import hmac
import hashlib
import logging
from logging.handlers import RotatingFileHandler
import argparse
import requests
from urllib.parse import urlencode

# -------------------------
# Configuration / Constants
# -------------------------
TESTNET_BASE = "https://testnet.binancefuture.com"
ORDER_ENDPOINT = "/fapi/v1/order"
TIMEOUT = 10  # seconds for HTTP requests

# -------------------------
# Logging setup
# -------------------------
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger("BasicBot")
logger.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "basic_bot.log"),
    maxBytes=2 * 1024 * 1024,
    backupCount=5,
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(levelname)s: %(message)s")
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)


# -------------------------
# Helper: Signed Requests
# -------------------------
def _sign(params: dict, secret: str) -> str:
    """Create HMAC SHA256 signature of the query string."""
    encoded = urlencode(params)
    signature = hmac.new(secret.encode("utf-8"), encoded.encode("utf-8"), hashlib.sha256).hexdigest()
    return signature


def _post_signed(api_key: str, api_secret: str, path: str, params: dict):
    """
    Post a signed request to TESTNET_BASE + path.
    Returns response JSON (or raises for HTTP errors).
    """
    params = params.copy()
    params["timestamp"] = int(time.time() * 1000)
    query = urlencode(params)
    signature = hmac.new(api_secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()
    params["signature"] = signature

    url = TESTNET_BASE + path
    headers = {
        "X-MBX-APIKEY": api_key,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    logger.debug("POST %s ? %s", url, urlencode({k: v for k, v in params.items() if k != "signature"}))
    try:
        resp = requests.post(url, headers=headers, data=params, timeout=TIMEOUT)
        logger.debug("Response status: %s", resp.status_code)
        try:
            j = resp.json()
        except Exception:
            logger.exception("Failed to decode JSON from response")
            resp.raise_for_status()
        if not resp.ok:
            logger.error("API error: %s", j)
            # raise an informative exception
            raise Exception(f"API response error: HTTP {resp.status_code} - {j}")
        logger.info("API response: %s", j)
        return j
    except requests.RequestException as e:
        logger.exception("Network error when calling Binance API")
        raise


# -------------------------
# BasicBot class
# -------------------------
class BasicBot:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        logger.info("BasicBot initialized (Testnet base: %s)", TESTNET_BASE)

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None,
                    stop_price: float = None, time_in_force: str = "GTC", reduce_only: bool = False,
                    close_position: bool = False):
        """
        Place an order on Binance Futures Testnet.
        - symbol: e.g., 'BTCUSDT'
        - side: 'BUY' or 'SELL'
        - order_type: 'MARKET', 'LIMIT', or 'STOP_LIMIT'
            - MARKET: requires quantity
            - LIMIT: requires price and quantity
            - STOP_LIMIT: requires stop_price, price and quantity
        - time_in_force: e.g., 'GTC'
        - reduce_only: True/False (for futures)
        - close_position: True/False (for futures)
        """
        # Basic validation
        symbol = symbol.upper()
        side = side.upper()
        order_type = order_type.upper()

        if not symbol.isalnum():
            raise ValueError("Symbol must be alphanumeric, e.g., BTCUSDT")

        if side not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")

        if order_type not in ("MARKET", "LIMIT", "STOP_LIMIT"):
            raise ValueError("order_type must be MARKET, LIMIT, or STOP_LIMIT")

        if quantity is None or quantity <= 0:
            raise ValueError("quantity must be a positive number")

        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET" if order_type == "MARKET" else ("LIMIT" if order_type == "LIMIT" else "STOP"),
            "quantity": str(quantity),
            "recvWindow": 5000,
        }

        # Additional fields for LIMIT
        if order_type == "LIMIT":
            if price is None:
                raise ValueError("LIMIT orders require price")
            params["price"] = str(price)
            params["timeInForce"] = time_in_force

        # For STOP_LIMIT we send type=STOP and set stopPrice and price & timeInForce
        if order_type == "STOP_LIMIT":
            if stop_price is None or price is None:
                raise ValueError("STOP_LIMIT requires both stop_price and price")
            # On Binance Futures, the `type=STOP` or `type=STOP_MARKET` is used; to create a stop-limit you supply stopPrice + price.
            # We'll use type=STOP (which requires price) to emulate stop-limit.
            params["stopPrice"] = str(stop_price)
            params["price"] = str(price)
            params["timeInForce"] = time_in_force

        if reduce_only:
            params["reduceOnly"] = "true"
        if close_position:
            params["closePosition"] = "true"

        # Send the signed request
        logger.info("Placing order: %s %s %s qty=%s price=%s stop=%s", symbol, side, order_type, quantity, price, stop_price)
        response = _post_signed(self.api_key, self.api_secret, ORDER_ENDPOINT, params)
        return response


# -------------------------
# CLI
# -------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Basic Binance Futures Testnet Trading Bot (USDT-M)")

    parser.add_argument("--api-key", help="Binance API Key (or set BINANCE_API_KEY env var)")
    parser.add_argument("--api-secret", help="Binance API Secret (or set BINANCE_API_SECRET env var)")

    parser.add_argument("--symbol", required=True, help="Trading symbol, e.g., BTCUSDT")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL"], help="BUY or SELL")
    parser.add_argument("--type", dest="order_type", required=True, choices=["MARKET", "LIMIT", "STOP_LIMIT"],
                        help="Order type: MARKET, LIMIT, STOP_LIMIT")
    parser.add_argument("--quantity", required=True, type=float, help="Order quantity (in base asset)")
    parser.add_argument("--price", type=float, help="Price for LIMIT or STOP_LIMIT")
    parser.add_argument("--stop-price", dest="stop_price", type=float, help="Stop price for STOP_LIMIT")
    parser.add_argument("--time-in-force", dest="tif", default="GTC", help="Time in force for LIMIT/STOP_LIMIT (default GTC)")
    parser.add_argument("--reduce-only", action="store_true", help="Set reduceOnly=true for the order")
    parser.add_argument("--close-position", action="store_true", help="Set closePosition=true for the order (futures)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging to console")

    return parser.parse_args()


def main():
    args = parse_args()

    api_key = args.api_key or os.environ.get("BINANCE_API_KEY")
    api_secret = args.api_secret or os.environ.get("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        logger.error("API key and secret must be provided either via --api-key/--api-secret or environment variables BINANCE_API_KEY & BINANCE_API_SECRET")
        return

    if args.verbose:
        console_handler.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    bot = BasicBot(api_key, api_secret)

    try:
        result = bot.place_order(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
            time_in_force=args.tif,
            reduce_only=args.reduce_only,
            close_position=args.close_position
        )
        logger.info("Order placed successfully. Order response:\n%s", result)
        print("\n=== ORDER RESPONSE ===")
        for k, v in result.items():
            print(f"{k}: {v}")
        print("======================\n")
    except Exception as e:
        logger.exception("Failed to place order: %s", e)
        print("ERROR:", e)


if __name__ == "__main__":
    main()
