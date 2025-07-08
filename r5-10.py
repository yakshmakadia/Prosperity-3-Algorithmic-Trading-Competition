from typing import Dict, List
import json

class Order:
    def __init__(self, symbol: str, price: int, quantity: int):
        self.symbol = symbol
        self.price = price
        self.quantity = quantity

class OwnTrade:
    def __init__(self, symbol: str, price: int, quantity: int, buyer: str, seller: str, timestamp: int):
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
        self.buyer = buyer
        self.seller = seller
        self.timestamp = timestamp

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
        self.own_trades: Dict[str, List[OwnTrade]] = {}

class Trader:
    def __init__(self):
        self.macaron_limit = 75
        self.short_window = 3
        self.long_window = 7
        self.voucher_strikes = {
            "VOLCANIC_ROCK_VOUCHER_9500": 9500,
            "VOLCANIC_ROCK_VOUCHER_9750": 9750,
            "VOLCANIC_ROCK_VOUCHER_10000": 10000,
            "VOLCANIC_ROCK_VOUCHER_10250": 10250,
            "VOLCANIC_ROCK_VOUCHER_10500": 10500
        }

    def get_mid_price(self, depth):
        if depth and depth.buy_orders and depth.sell_orders:
            return (max(depth.buy_orders) + min(depth.sell_orders)) / 2
        return 10000

    def run(self, state: TradingState):
        orders = {}
        conversions = 0
        memory = json.loads(state.traderData) if state.traderData else {}

        # 1. MACARONS MOVING AVERAGE STRATEGY
        macaron_orders = self.macaron_strategy(state, memory)
        if macaron_orders:
            orders["MAGNIFICENT_MACARONS"] = macaron_orders

        # 2. MEAN REVERSION ON SQUID_INK, KELP
        for asset in ["SQUID_INK", "KELP"]:
            orders.update(self.mean_reversion(state, asset))

        # 3. VOUCHER BASKET ARBITRAGE STRATEGY
        voucher_orders = self.voucher_basket_arbitrage(state)
        for order in voucher_orders:
            orders.setdefault(order.symbol, []).append(order)

        return orders, conversions, json.dumps(memory)

    def macaron_strategy(self, state, memory):
        product = "MAGNIFICENT_MACARONS"
        orders = []
        if product not in state.order_depths:
            return orders

        depth = state.order_depths[product]
        position = state.position.get(product, 0)
        price_history = memory.get("macaron_prices", [])

        best_bid = max(depth.buy_orders) if depth.buy_orders else 0
        best_ask = min(depth.sell_orders) if depth.sell_orders else 20000
        mid_price = (best_bid + best_ask) / 2
        price_history.append(mid_price)

        if len(price_history) > self.long_window:
            price_history = price_history[-self.long_window:]

        short_ma = sum(price_history[-self.short_window:]) / min(len(price_history), self.short_window)
        long_ma = sum(price_history) / len(price_history)

        if short_ma > long_ma * 1.002 and best_ask < mid_price * 1.01 and position < self.macaron_limit:
            buy_volume = min(depth.sell_orders[best_ask], self.macaron_limit - position)
            orders.append(Order(product, best_ask, buy_volume))
        elif short_ma < long_ma * 0.998 and best_bid > mid_price * 0.99 and position > -self.macaron_limit:
            sell_volume = min(depth.buy_orders[best_bid], position + self.macaron_limit)
            orders.append(Order(product, best_bid, -sell_volume))

        memory["macaron_prices"] = price_history
        return orders

    def mean_reversion(self, state, asset, limit=50):
        orders = {}
        if asset in state.order_depths:
            depth = state.order_depths[asset]
            position = state.position.get(asset, 0)
            best_bid = max(depth.buy_orders) if depth.buy_orders else 0
            best_ask = min(depth.sell_orders) if depth.sell_orders else 20000
            mid_price = (best_bid + best_ask) / 2

            asset_orders = []
            if best_ask < mid_price * 0.98 and position < limit:
                asset_orders.append(Order(asset, best_ask, min(depth.sell_orders[best_ask], limit - position)))
            if best_bid > mid_price * 1.02 and position > -limit:
                asset_orders.append(Order(asset, best_bid, -min(depth.buy_orders[best_bid], position + limit)))

            if asset_orders:
                orders[asset] = asset_orders
        return orders

    def voucher_basket_arbitrage(self, state):
        orders = []
        rock_mid_price = self.get_mid_price(state.order_depths.get("VOLCANIC_ROCK"))

        for voucher, strike in self.voucher_strikes.items():
            if voucher not in state.order_depths:
                continue

            fv = max(0, rock_mid_price - strike)
            adjusted_fv = fv * (2 / 7)
            depth = state.order_depths[voucher]
            position = state.position.get(voucher, 0)
            limit = 200  # Increased position limit for better arbitrage coverage

            best_bid = max(depth.buy_orders) if depth.buy_orders else 0
            best_ask = min(depth.sell_orders) if depth.sell_orders else 99999

            if best_ask < adjusted_fv * 0.97 and position < limit:
                orders.append(Order(voucher, best_ask, min(depth.sell_orders[best_ask], limit - position)))
            if best_bid > adjusted_fv * 1.03 and position > -limit:
                orders.append(Order(voucher, best_bid, -min(depth.buy_orders[best_bid], position + limit)))

        return orders