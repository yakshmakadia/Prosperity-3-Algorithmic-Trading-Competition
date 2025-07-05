from typing import Dict, List, Optional
import statistics
import sys

class Order:
    def __init__(self, symbol: str, price: int, quantity: int):
        self.symbol = symbol
        self.price = price
        self.quantity = quantity

    def __repr__(self):
        return f"Order({self.symbol}, {self.price}, {self.quantity})"

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
        self.products = ["RAINFOREST_RESIN", "KELP", "SQUID_INK"]
        self.position_limits = {p: 50 for p in self.products}
        self.price_history = {p: [] for p in self.products}
        self.strategy_params = {
            "RAINFOREST_RESIN": {"base_spread": 0.8, "momentum_window": 5},
            "KELP": {"base_spread": 1.0, "momentum_window": 4},
            "SQUID_INK": {"base_spread": 1.3, "momentum_window": 3}
        }

    def run(self, state: TradingState):
        result = {}

        for product in self.products:
            if product not in state.order_depths:
                continue

            order_depth = state.order_depths[product]
            position = state.position.get(product, 0)
            params = self.strategy_params[product]

            self.update_price_history(product, order_depth)
            fair = self.compute_fair_price(product, order_depth)
            momentum = self.compute_momentum(product, params["momentum_window"])
            spread = self.compute_adaptive_spread(product)

            orders = self.generate_aggressive_orders(product, fair, order_depth, position, momentum, spread, state.timestamp)
            result[product] = orders

            print(f"[TICK {state.timestamp}] {product} pos={position} fair={fair:.2f} mom={momentum:.4f} spread={spread:.2f}", file=sys.stderr)
            for o in orders:
                print(f"  -> {o}", file=sys.stderr)

        return result, 0, "CG-Z1-OPT"

    def update_price_history(self, product: str, order_depth: OrderDepth):
        if order_depth.buy_orders and order_depth.sell_orders:
            bid = max(order_depth.buy_orders)
            ask = min(order_depth.sell_orders)
            mid = (bid + ask) / 2
            self.price_history[product].append(mid)
            if len(self.price_history[product]) > 100:
                self.price_history[product].pop(0)

    def compute_fair_price(self, product: str, order_depth: OrderDepth) -> float:
        history = self.price_history[product]
        if not history:
            return (max(order_depth.buy_orders) + min(order_depth.sell_orders)) / 2

        sma = sum(history[-10:]) / min(10, len(history))
        ema_weights = [0.9 ** i for i in range(len(history))]
        ema = sum(p * w for p, w in zip(reversed(history), reversed(ema_weights))) / sum(ema_weights)

        bid = max(order_depth.buy_orders)
        ask = min(order_depth.sell_orders)
        bid_vol = sum(order_depth.buy_orders.values())
        ask_vol = sum(abs(v) for v in order_depth.sell_orders.values())
        micro = (bid * ask_vol + ask * bid_vol) / (bid_vol + ask_vol)

        return 0.5 * micro + 0.35 * ema + 0.15 * sma

    def compute_momentum(self, product: str, window: int) -> float:
        if len(self.price_history[product]) < window:
            return 0
        p = self.price_history[product][-window:]
        diffs = [(p[i+1] - p[i])/p[i] for i in range(len(p)-1)]
        return statistics.mean(diffs)

    def compute_adaptive_spread(self, product: str) -> float:
        history = self.price_history[product]
        if len(history) < 10:
            return self.strategy_params[product]["base_spread"]
        stdev = statistics.stdev(history[-10:])
        return max(0.6, min(2, stdev * 1.5))

    def generate_aggressive_orders(self, product: str, fair: float, depth: OrderDepth, pos: int,
                                 momentum: float, spread: float, timestamp: int) -> List[Order]:
        orders = []
        limit = self.position_limits[product]
        vol_boost = 2 if abs(momentum) > 0.01 else 1
        early_game = timestamp < 1500

        buy_price = round(fair - spread - momentum * spread * 3)
        sell_price = round(fair + spread - momentum * spread * 3)

        max_qty = int(12 * vol_boost * (1.2 if early_game else 1))
        buy_qty = min(max_qty, limit - pos)
        sell_qty = min(max_qty, limit + pos)

        if buy_qty > 0:
            orders.append(Order(product, buy_price, buy_qty))
        if sell_qty > 0:
            orders.append(Order(product, sell_price, -sell_qty))

        best_ask = min(depth.sell_orders)
        best_bid = max(depth.buy_orders)

        if best_ask < fair * 0.997:
            take_qty = min(-depth.sell_orders[best_ask], limit - pos)
            if take_qty > 0:
                orders.append(Order(product, best_ask, take_qty))

        if best_bid > fair * 1.003:
            take_qty = min(depth.buy_orders[best_bid], limit + pos)
            if take_qty > 0:
                orders.append(Order(product, best_bid, -take_qty))

        if abs(pos) > 40:
            flatten = round(fair + 5) if pos > 0 else round(fair - 5)
            orders.append(Order(product, flatten, -pos))

        return orders
