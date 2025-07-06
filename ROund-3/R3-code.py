from typing import Dict, List
import random


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
        self.position_limits = {
            "VOLCANIC_ROCK": 400,
            "VOLCANIC_ROCK_VOUCHER_9500": 200,
            "VOLCANIC_ROCK_VOUCHER_9750": 200,
            "VOLCANIC_ROCK_VOUCHER_10000": 200,
            "VOLCANIC_ROCK_VOUCHER_10250": 200,
            "VOLCANIC_ROCK_VOUCHER_10500": 200,
        }

        self.vouchers = {
            "VOLCANIC_ROCK_VOUCHER_9500": 9500,
            "VOLCANIC_ROCK_VOUCHER_9750": 9750,
            "VOLCANIC_ROCK_VOUCHER_10000": 10000,
            "VOLCANIC_ROCK_VOUCHER_10250": 10250,
            "VOLCANIC_ROCK_VOUCHER_10500": 10500,
        }

    def run(self, state: TradingState):
        result = {symbol: [] for symbol in self.position_limits}
        depths = state.order_depths
        positions = state.position

        # 1. Detect Market Regime
        market_regime = self.detect_market_regime(depths)

        # 2. Get mid price for rock
        rock_mid_price = self.get_mid_price(depths.get("VOLCANIC_ROCK", OrderDepth()))

        # 3. Apply appropriate strategy
        if market_regime == "Trending":
            result.update(self.run_trending_strategy(state, rock_mid_price))
        elif market_regime == "Volatile":
            result.update(self.run_volatile_strategy(state, rock_mid_price))
        else:
            result.update(self.run_stable_strategy(state, rock_mid_price))

        return result, 0, "SMART_ADAPTIVE_R4"

    def detect_market_regime(self, depths: Dict[str, OrderDepth]) -> str:
        rock_depth = depths.get("VOLCANIC_ROCK", None)
        if not rock_depth:
            return "Stable"

        spread = self.calculate_spread(rock_depth)
        volatility = random.uniform(0, 0.1)  # Placeholder
        rock_mid_price = self.get_mid_price(rock_depth)
        trend_strength = rock_mid_price - 10000  # Placeholder for real trend logic

        if volatility > 0.05 and spread > 200:
            return "Volatile"
        elif abs(trend_strength) > 50:
            return "Trending"
        else:
            return "Stable"

    def calculate_spread(self, depth: OrderDepth) -> float:
        if depth.buy_orders and depth.sell_orders:
            return max(depth.buy_orders) - min(depth.sell_orders)
        return 0

    def get_mid_price(self, depth: OrderDepth) -> float:
        if depth.buy_orders and depth.sell_orders:
            return (max(depth.buy_orders) + min(depth.sell_orders)) / 2
        elif depth.buy_orders:
            return max(depth.buy_orders)
        elif depth.sell_orders:
            return min(depth.sell_orders)
        return 10000

    def fair_value(self, rock_price: float, strike: int) -> float:
        return max(rock_price - strike, 0)

    def trade_vouchers(self, state: TradingState, rock_mid: float) -> Dict[str, List[Order]]:
        orders = {}
        for voucher, strike in self.vouchers.items():
            if voucher not in state.order_depths:
                continue
            depth = state.order_depths[voucher]
            fair = self.fair_value(rock_mid, strike)
            pos = state.position.get(voucher, 0)
            limit = self.position_limits[voucher]
            orders[voucher] = []

            # Buy undervalued
            if depth.sell_orders:
                ask = min(depth.sell_orders)
                if ask < fair * 0.95:
                    qty = min(depth.sell_orders[ask], limit - pos)
                    orders[voucher].append(Order(voucher, ask, qty))

            # Sell overvalued
            if depth.buy_orders:
                bid = max(depth.buy_orders)
                if bid > fair * 1.05:
                    qty = min(depth.buy_orders[bid], limit + pos)
                    orders[voucher].append(Order(voucher, bid, -qty))
        return orders

    def trade_rock_mean_reversion(self, state: TradingState, rock_mid: float) -> List[Order]:
        result = []
        depth = state.order_depths["VOLCANIC_ROCK"]
        pos = state.position.get("VOLCANIC_ROCK", 0)
        limit = self.position_limits["VOLCANIC_ROCK"]

        if depth.sell_orders:
            ask = min(depth.sell_orders)
            if ask < rock_mid * 0.98:
                qty = min(depth.sell_orders[ask], limit - pos)
                result.append(Order("VOLCANIC_ROCK", ask, qty))

        if depth.buy_orders:
            bid = max(depth.buy_orders)
            if bid > rock_mid * 1.02:
                qty = min(depth.buy_orders[bid], limit + pos)
                result.append(Order("VOLCANIC_ROCK", bid, -qty))

        return result

    def run_trending_strategy(self, state: TradingState, rock_mid: float) -> Dict[str, List[Order]]:
        result = self.trade_vouchers(state, rock_mid)
        result["VOLCANIC_ROCK"] = self.trade_rock_mean_reversion(state, rock_mid)
        return result

    def run_volatile_strategy(self, state: TradingState, rock_mid: float) -> Dict[str, List[Order]]:
        # Looser margins for volatile
        result = self.trade_vouchers(state, rock_mid)
        result["VOLCANIC_ROCK"] = self.trade_rock_mean_reversion(state, rock_mid)
        return result

    def run_stable_strategy(self, state: TradingState, rock_mid: float) -> Dict[str, List[Order]]:
        # Normal conservative logic
        result = self.trade_vouchers(state, rock_mid)
        result["VOLCANIC_ROCK"] = self.trade_rock_mean_reversion(state, rock_mid)
        return result
