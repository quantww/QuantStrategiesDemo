# -*- coding: utf-8 -*-

from aioquant import quant
from aioquant.const import BINANCE, HUOBI, OKEX
from aioquant.configure import config
from aioquant.error import Error
from aioquant.order import Order, ORDER_STATUS_FILLED, ORDER_STATUS_PARTIAL_FILLED, ORDER_STATUS_FAILED
from aioquant.tasks import LoopRunTask
from aioquant.trade import Trade
from aioquant.utils import logger


class BinanceStrategy:

    def __init__(self) -> None:
        """
        '吃盘口毛刺'的简化策略: 根据实时盘口变化取卖6和卖8的价格,并根据他们的平均价格来挂卖单
        即, average_price = (ask6_price + ask8_price) / 2 取指定位数的数据, EOS是4位;

        在策略启动的时候判断是否有挂单, 如果有挂单, 判断价格是否已经超过 ask6_price 和 ask8_price 的区间,
        如果超过那么撤单后再重新挂单.
        """
        self._symbol = "EOSUSDT"
        self._action = "SELL"
        self._quantity = "2.5"
        self._order_id = ""
        self._price = 0.0

        self._is_ok = False

        params = dict(
            strategy=config.strategy_name,
            platform=config.platform,
            symbol=config.symbol,
            account=config.account,  # 分布式...多个
            access_key=config.access_key,
            secret_key=config.secret_key,
            passphrase=config.passphrase,
            order_update_callback=self.on_order_update_callback,
            init_callback=self.on_init_callback,
            error_callback=self.on_error_callback,
        )

        self._trade = Trade(**params)

        if config.platform == BINANCE:
            LoopRunTask.register(self.dynamic_trade_with_binance, interval=2)
        elif config.platform == HUOBI:
            LoopRunTask.register(self.dynamic_trade_with_huobi, interval=2)
        elif config.platform == OKEX:
            LoopRunTask.register(self.dynamic_trade_with_okex, interval=2)
        else:
            logger.error("platform error:", config.platform, caller=self)
            quant.stop()

    async def create_new_order(self, price: float):
        """下单"""
        action = self._action
        quantity = self._quantity  # min 2.5
        logger.info("Doing price: ", price, "quantity: ", self._quantity)
        order_id, error = await self._trade.create_order(action, price, quantity)
        if error:
            return
        self._order_id = order_id
        self._price = price
        logger.info("order_id", self._order_id, "price", price, caller=self)

    async def revoke_order(self, order_id: str):
        """撤销订单"""
        _, error = await self._trade.revoke_order(order_id)
        if error:
            return
        logger.info("order_id: ", order_id, caller=self)

    async def dynamic_trade_with_binance(self, *args, **kwargs):
        """简化版的吃盘口毛刺策略"""
        if not self._is_ok:
            return
        success, error = await self._trade.rest_api.get_orderbook(self._symbol, 10)
        if error:
            # 通过 钉钉、微信等发送通知...
            # 或 接入风控系统;
            self._is_ok = False
            logger.warn("error: ", error, caller=self)
            return

        ask6_price = float(success["asks"][5][0])
        ask8_price = float(success["asks"][7][0])
        average_price = round((ask6_price + ask8_price) / 2, 4)
        logger.info(f"the average price is {average_price}....", caller=self)

        await self.strategy_process(ask6_price, ask8_price, average_price)

    async def strategy_process(self, ask6_price: float, ask8_price: float, average_price: float):
        """handle strategy process"""
        if self._order_id and self._price:
            if self._price >= ask6_price and self._price <= ask8_price:
                return

        if self._order_id:
            await self.revoke_order(self._order_id)

        await self.create_new_order(average_price)

    async def dynamic_trade_with_huobi(self, *args, **kwargs):
        raise NotImplementedError()

    async def dynamic_trade_with_okex(self, *args, **kwargs):
        raise NotImplementedError()

    async def on_order_update_callback(self, order: Order):
        """不会主动被调用,当订单有变化的时候会被调用"""
        logger.info("order", order, caller=self)
        if order.status == ORDER_STATUS_FILLED:
            # 完全成交
            self._order_id = ""
            self._price = 0.0
            # TODO: 完全对冲
        elif order.status == ORDER_STATUS_PARTIAL_FILLED:
            # 部分成交
            # TODO: 部分对冲
            pass
        elif order.status == ORDER_STATUS_FAILED:
            # 报警, 触发风控
            pass
        else:
            return

    async def on_init_callback(self, success: bool, **kwargs):
        """用于标记: 初始化Trade()成功或失败"""
        logger.info("success", success, caller=self)
        if not success:
            return

        _, error = await self._trade.revoke_order()
        if error:
            return

        self._is_ok = True

    async def on_error_callback(self, error: Error, **kwargs):
        """执行过程中有任意的失败情况下都会报错"""
        self._is_ok = False
        logger.info("error", error, caller=self)
        quant.stop()
