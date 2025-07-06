from typing import Dict, List
import json


class Order:
    def __init__(self, symbol: str, price: int, quantity: int):
        self.symbol = symbol
        self.price = price
        self.quantity = quantity


class OrderDepth:
    def __init__(self):
        self.buy_orders: Dict[int, int] = {}
        self.sell_orders: Dict[int, int] = {}


class TradingState:
    def __init__(self):
        self.timestamp: int = 0
        self.order_depths: Dict[str, OrderDepth] = {}
        self.position: Dict[str, int] = {}
        self.traderData: str = ""


class Trader:
    def __init__(self):
        self.position_limit = 75
        self.short_window = 3
        self.long_window = 7

    def run(self, state: TradingState):
        product = "MAGNIFICENT_MACARONS"
        orders: List[Order] = []

        depth = state.order_depths.get(product)
        position = state.position.get(product, 0)

        # Load historical prices from traderData
        if state.traderData:
            memory = json.loads(state.traderData)
            price_history = memory.get("price_history", [])
        else:
            price_history = []

        # Get current mid price
        if depth and depth.buy_orders and depth.sell_orders:
            best_bid = max(depth.buy_orders)
            best_ask = min(depth.sell_orders)
            mid_price = (best_bid + best_ask) / 2
        else:
            mid_price = 10000  # default fallback

        price_history.append(mid_price)
        if len(price_history) > self.long_window:
            price_history = price_history[-self.long_window:]

        # Calculate moving averages
        short_ma = sum(price_history[-self.short_window:]) / min(len(price_history), self.short_window)
        long_ma = sum(price_history) / len(price_history)

        # Trading decision
        if short_ma > long_ma * 1.002 and best_ask < mid_price * 1.01 and position < self.position_limit:
            volume = min(depth.sell_orders[best_ask], self.position_limit - position)
            orders.append(Order(product, best_ask, volume))

        elif short_ma < long_ma * 0.998 and best_bid > mid_price * 0.99 and position > -self.position_limit:
            volume = min(depth.buy_orders[best_bid], position + self.position_limit)
            orders.append(Order(product, best_bid, -volume))

        # Save memory
        traderData = json.dumps({"price_history": price_history})

        return {product: orders}, 0, traderData
