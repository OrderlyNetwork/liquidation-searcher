import asyncio
from decimal import ROUND_DOWN, Decimal
from typing import Any, Dict, List, Tuple

from orderly_sdk.rest import AsyncClient

from liquidation_searcher.types import ActionType, Executor, LiquidationType
from liquidation_searcher.utils.log import logger


class OrderlyExecutor(Executor):
    symbol_info: Dict[str, Any]
    max_notional: float
    liquidation_symbols: List[str]

    def __init__(
        self,
        account_id,
        orderly_key,
        orderly_secret,
        endpoint,
        max_notional,
        liquidation_symbols,
    ):
        self.orderly_client = AsyncClient(
            account_id=account_id,
            orderly_key=orderly_key,
            orderly_secret=orderly_secret,
            endpoint=endpoint,
        )
        self.symbol_info = dict()
        self.max_notional = max_notional
        self.liquidation_symbols = liquidation_symbols

    async def sync_state(self):
        symbols = await self.orderly_client.get_available_symbols()
        for symbol in symbols["data"]["rows"]:
            self.symbol_info[symbol["symbol"]] = {
                "base_tick": str(symbol["base_tick"]),
                "base_min": str(symbol["base_min"]),
                "min_notional": str(symbol["min_notional"]),
            }
        balance = await self.orderly_client.get_current_holding()
        logger.info("orderly executor balance: {}", balance)
        info = await self.orderly_client.get_account_info()
        logger.info("orderly executor account info: {}", info)

    async def execute(self, action):
        if action["action_type"] == ActionType.ORDERLY_LIQUIDATION_ORDER:
            liquidation_id = action["liquidation_id"]
            if (
                action["type"] == LiquidationType.LIQUIDATED
                or action["type"] == LiquidationType.CLAIM
            ):
                total_notional = 0
                ratio = 0
                for position in action["positions_by_perp"]:
                    symbol = position["symbol"]
                    position_qty = position["position_qty"]
                    future_prices = (
                        await self.orderly_client.get_futures_for_one_market(symbol)
                    )
                    mark_price = future_prices["data"]["mark_price"]
                    total_notional += mark_price * position_qty
                if total_notional == 0:
                    logger.error(
                        "orderly executor claim_liquidated_positions total_notional is 0"
                    )
                    return
                if total_notional <= self.max_notional:
                    ratio = 1
                else:
                    ratio = self.format_ratio(self.max_notional / total_notional)
                json = dict(
                    liquidation_id=liquidation_id,
                    ratio_qty_request=ratio,
                )
                logger.info(
                    "orderly executor claim_liquidated_positions json: {}", json
                )
                res = await self.orderly_client.claim_liquidated_positions(json)
                logger.info("orderly executor claim_liquidated_positions res: {}", res)
            # elif action["type"] == LiquidationType.CLAIM:
            #     for position in action["positions_by_perp"]:
            #         symbol = position["symbol"]
            #         position_qty = position["position_qty"]
            #         if symbol not in self.liquidation_symbols:
            #             logger.error(
            #                 "orderly executor claim ignored symbol: {}, not configed in liquidation_symbols",
            #                 symbol,
            #             )
            #             continue
            #         future_prices = (
            #             await self.orderly_client.get_futures_for_one_market(symbol)
            #         )
            #         mark_price = future_prices["data"]["mark_price"]

            #         (qty, ratio) = self.calc_claim_qty(symbol, position_qty, mark_price)
            #         if qty == 0 or ratio == 0:
            #             logger.error(
            #                 "orderly executor calc_claim_qty failed symbol: {}, qty: {}",
            #                 symbol,
            #                 position_qty,
            #             )
            #             continue

            #         json = dict(
            #             liquidation_id=liquidation_id,
            #             symbol=symbol,
            #             qty_request=self.format_qty(symbol, qty),
            #         )
            #         logger.info("orderly executor claim_insurance_fund json: {}", json)
            #         res = await self.orderly_client.claim_insurance_fund(json)
            #         logger.info("orderly executor claim_insurance_fund res: {}", res)
            #         # We have only one liquidation_id, so we can only claim the first symbol for now
            #         break
            else:
                logger.error(f"Unknown liquidation type: {action['type']}")

            # wait for claim position transfer
            await asyncio.sleep(2)

            positions = await self.orderly_client.get_all_positions()
            logger.info("orderly executor positions: {}", positions)
            for position in positions["data"]["rows"]:
                symbol = position["symbol"]
                position_qty = position["position_qty"]
                side = ""
                if position_qty > 0:
                    side = "SELL"
                elif position_qty < 0:
                    side = "BUY"
                else:
                    logger.debug(
                        f"Unknown position symbol: {symbol}, qty: {position_qty}"
                    )
                    continue
                json = dict(
                    symbol=symbol,
                    order_type="MARKET",
                    side=side,
                    order_quantity=self.format_qty(symbol, abs(position_qty)),
                    reduce_only=True,
                )
                if json["order_quantity"] == 0:
                    logger.debug(
                        f"Empty position quantity symbol: {symbol}, qty: {position_qty}"
                    )
                    continue
                logger.info("orderly executor create_order json: {}", json)
                res = await self.orderly_client.create_order(json)
                logger.info("orderly executor create_order res: {}", res)
        else:
            logger.error(f"Unknown action type: {action['action_type']}")
            return

    def calc_claim_qty(self, symbol, position_qty, mark_price) -> Tuple[float, float]:
        if position_qty == 0 or mark_price == 0:
            return (0, 0)
        qty = abs(self.max_notional / mark_price)
        if qty < float(self.symbol_info[symbol]["base_min"]):
            return (0, 0)
        if qty * mark_price < float(self.symbol_info[symbol]["min_notional"]):
            return (0, 0)
        qty = min(qty, abs(position_qty))
        ratio = self.format_ratio(qty / position_qty)
        qty = qty if position_qty > 0 else -qty
        return (qty, ratio)

    def format_qty(self, symbol, qty):
        return format(
            Decimal(str(qty)).quantize(
                Decimal(self.symbol_info[symbol]["base_tick"]),
                rounding=ROUND_DOWN,
            ),
            "f",
        )

    def format_ratio(self, ratio):
        return abs(
            float(
                Decimal(str(ratio)).quantize(
                    Decimal("0.001"),
                    rounding=ROUND_DOWN,
                )
            )
        )
