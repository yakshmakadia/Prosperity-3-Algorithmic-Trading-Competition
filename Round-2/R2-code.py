from typing import Dict, List, Optional
import statistics

# ========== MOCK CLASSES FOR LOCAL TESTING ==========
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
# ========== END MOCK CLASSES ==========

class Trader:
    def __init__(self):
        self.products = ["RAINFOREST_RESIN", "KELP", "SQUID_INK"]
        self.position_limits = {p: 50 for p in self.products}
        self.price_history = {p: [] for p in self.products}
        self.spread_history = {p: [] for p in self.products}
        self.volume_history = {p: [] for p in self.products}

        self.strategy_params = {
            "RAINFOREST_RESIN": {
                "base_spread": 1.5,
                "volatility_window": 20,
                "momentum_window": 10,
                "inventory_skew": 0.3
            },
            "KELP": {
                "base_spread": 2.5,
                "volatility_window": 15,
                "momentum_window": 8,
                "inventory_skew": 0.4
            },
            "SQUID_INK": {
                "base_spread": 3.0,
                "volatility_window": 10,
                "momentum_window": 5,
                "inventory_skew": 0.5
            }
        }

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        result = {}

        for product in self.products:
            if product not in state.order_depths:
                continue

            order_depth = state.order_depths[product]
            position = state.position.get(product, 0)
            params = self.strategy_params[product]

            self.update_market_history(product, order_depth, state.timestamp)
            fair_price = self.calculate_fair_price(product, order_depth)
            spread = self.calculate_dynamic_spread(product, position)
            momentum = self.calculate_momentum(product)
            imbalance = self.calculate_order_imbalance(order_depth)

            orders = self.generate_orders(
                product=product,
                order_depth=order_depth,
                position=position,
                fair_price=fair_price,
                spread=spread,
                momentum=momentum,
                imbalance=imbalance,
                params=params,
                timestamp=state.timestamp
            )

            result[product] = orders

        return result, 0, "AURONIS_BURST"

    def update_market_history(self, product: str, order_depth: OrderDepth, timestamp: int):
        if order_depth.buy_orders and order_depth.sell_orders:
            best_bid = max(order_depth.buy_orders.keys())
            best_ask = min(order_depth.sell_orders.keys())
            mid_price = (best_bid + best_ask) / 2
            spread = best_ask - best_bid
            total_volume = sum(abs(v) for v in order_depth.sell_orders.values()) + sum(order_depth.buy_orders.values())

            self.price_history[product].append(mid_price)
            self.spread_history[product].append(spread)
            self.volume_history[product].append(total_volume)

            if len(self.price_history[product]) > 100:
                self.price_history[product].pop(0)
                self.spread_history[product].pop(0)
                self.volume_history[product].pop(0)

    def calculate_fair_price(self, product: str, order_depth: OrderDepth) -> float:
        if not self.price_history[product]:
            return {"RAINFOREST_RESIN": 10000, "KELP": 2025, "SQUID_INK": 1970}.get(product, 1000)

        sma = sum(self.price_history[product][-20:]) / min(20, len(self.price_history[product]))
        ema_weights = [0.9**i for i in range(len(self.price_history[product]))]
        ema = sum(p * w for p, w in zip(reversed(self.price_history[product]), reversed(ema_weights))) / sum(ema_weights)

        current_bid = max(order_depth.buy_orders.keys())
        current_ask = min(order_depth.sell_orders.keys())
        bid_vol = sum(order_depth.buy_orders.values())
        ask_vol = sum(abs(v) for v in order_depth.sell_orders.values())
        microprice = (current_bid * ask_vol + current_ask * bid_vol) / (bid_vol + ask_vol)

        return 0.4 * microprice + 0.3 * ema + 0.3 * sma

    def calculate_dynamic_spread(self, product: str, position: int) -> float:
        params = self.strategy_params[product]
        if len(self.spread_history[product]) < 2:
            return params["base_spread"]

        spreads = self.spread_history[product][-params["volatility_window"]:]
        volatility = statistics.stdev(spreads) if len(spreads) >= 2 else 0
        position_ratio = abs(position) / self.position_limits[product]

        spread = params["base_spread"] * (1 + volatility) * (1 - params["inventory_skew"] * position_ratio)
        return max(1, min(spread, 20))

    def calculate_momentum(self, product: str) -> float:
        if len(self.price_history[product]) < 6:
            return 0
        prices = self.price_history[product][-6:]
        returns = [(prices[i+1] - prices[i])/prices[i] for i in range(len(prices)-1)]
        avg_return = statistics.mean(returns)

        threshold = 0.001 if product == "RAINFOREST_RESIN" else 0.003
        return (1 if avg_return > threshold else -1 if avg_return < -threshold else 0)

    def calculate_order_imbalance(self, order_depth: OrderDepth) -> float:
        bid_vol = sum(order_depth.buy_orders.values())
        ask_vol = sum(abs(v) for v in order_depth.sell_orders.values())
        if bid_vol + ask_vol == 0:
            return 0
        return (bid_vol - ask_vol) / (bid_vol + ask_vol)

    def generate_orders(self, product: str, order_depth: OrderDepth, position: int,
                      fair_price: float, spread: float, momentum: float, imbalance: float, params: dict, timestamp: int) -> List[Order]:
        orders = []
        position_limit = self.position_limits[product]

        adjustment = momentum * 0.5 + imbalance * 0.5
        buy_price = round(fair_price - spread * (1 - adjustment))
        sell_price = round(fair_price + spread * (1 + adjustment))

        # Time-aware size logic
        phase_boost = 1.5 if timestamp < 70000 else 1.0
        base_quantity = int((8 + 4 * abs(imbalance)) * phase_boost)
        buy_quantity = min(base_quantity, position_limit - position)
        sell_quantity = min(base_quantity, position_limit + position)

        # Endgame inventory flush
        if timestamp > 95000:
            if position > 0:
                orders.append(Order(product, max(order_depth.buy_orders.keys()), -position))
            elif position < 0:
                orders.append(Order(product, min(order_depth.sell_orders.keys()), -position))
            return orders

        if position < position_limit:
            orders.append(Order(product, buy_price, buy_quantity))
        if position > -position_limit:
            orders.append(Order(product, sell_price, -sell_quantity))

        best_bid = max(order_depth.buy_orders.keys())
        best_ask = min(order_depth.sell_orders.keys())

        if best_ask < fair_price * 0.995 and momentum >= 0:
            vol = min(-order_depth.sell_orders[best_ask], position_limit - position)
            if vol > 0:
                orders.append(Order(product, best_ask, vol))

        if best_bid > fair_price * 1.005 and momentum <= 0:
            vol = min(order_depth.buy_orders[best_bid], position_limit + position)
            if vol > 0:
                orders.append(Order(product, best_bid, -vol))

        return orders
