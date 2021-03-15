# -*- coding: utf-8 -*-

from aioquant import quant
from aioquant.platform.binance import BinanceRestAPI
from aioquant.tasks import SingleTask, LoopRunTask
from aioquant.utils import logger
from aioquant.configure import config


class BinanceStrategy:

    def __init__(self) -> None:
        host = "https://api.binance.com"
        access_key = "access_key"
        secret_key = "secret_key"
        self._rest_api = BinanceRestAPI(host=host, access_key=access_key, secret_key=secret_key)

        # 初始化的时候查询一下账户的资产信息
        # SingleTask.run(self.get_assert_info)  # 本质是一个协程;

        # 下单
        # SingleTask.run(self.create_new_order)

        # 撤单
        # SingleTask.run(self.revoke_order)

        """
        '吃盘口毛刺'的简化策略: 根据实时盘口变化取卖6和卖8的价格,并根据他们的平均价格来挂卖单
        即, average_price = (ask6_price + ask8_price) / 2 取指定位数的数据, EOS是4位;

        在策略启动的时候判断是否有挂单, 如果有挂单, 判断价格是否已经超过 ask6_price 和 ask8_price 的区间,
        如果超过那么撤单后再重新挂单.

        拆解:
        1.挂单;
        2.撤单;
        3.获取盘口信息(计算平均值);
        """
        self._symbol = "EOSUSDT"
        self._action = "SELL"
        self._quantity = "2.5"
        self._order_id = ""
        self._price = 0.0

        self._is_ok = True

        # SingleTask.run(self.get_latest_orders)
        # SingleTask.run(self.get_current_open_order)

        LoopRunTask.register(self.dynamic_trade, interval=5)

    async def get_assert_info(self):
        """获取资产信息"""
        success, error = await self._rest_api.get_user_account()
        logger.info("success: ", success, caller=self)
        # logger.info("error: ", error, caller=self)

    async def create_new_order(self, price: str):
        """下单"""
        symbol = self._symbol
        action = self._action
        quantity = self._quantity  # min 2.5
        success, error = await self._rest_api.create_order(action, symbol, price, quantity)
        if error:
            self._is_ok = False
            logger.warn("error: ", error, caller=self)
            return
        self._order_id = str(success["orderId"])
        self._price = price
        logger.info("order_id", self._order_id, "price", price, caller=self)

    async def revoke_order(self, order_id: str):
        """撤销订单"""
        success, error = await self._rest_api.revoke_order(self._symbol, order_id)
        if error:
            self._is_ok = False
            logger.warn("error: ", error, caller=self)
            return
        logger.info("order_id: ", order_id, caller=self)

    async def get_latest_orders(self):
        """获取最新盘口价格(订单薄)"""
        success, _ = await self._rest_api.get_orderbook(self._symbol, 10)
        logger.info("success: ", success, caller=self)

        ask6_price = success["asks"][5][0]
        ask8_price = success["asks"][7][0]
        average_price = round((float(ask6_price) + float(ask8_price)) / 2, 4)

        logger.info("ask6_price", ask6_price, "ask8_price", ask8_price, caller=self)
        logger.info("The average price is: ", average_price)

    async def get_current_open_order(self):
        """查询当前用户是否有挂单"""
        success, error = await self._rest_api.get_open_orders(self._symbol)
        logger.info("success: ", success, caller=self)
        logger.info("error: ", error, caller=self)

    async def dynamic_trade(self, *args, **kwargs):
        """简化版的吃盘口毛刺策略"""
        if not self._is_ok:
            logger.warn("something error", caller=self)
            quant.stop()
            return
        success, error = await self._rest_api.get_orderbook(self._symbol, 10)
        logger.info("success: ", success, caller=self)
        # logger.info("error: ", error, caller=self)
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


        if self._order_id and self._price:
            if self._price >= ask6_price and self._price <= ask8_price:
                return

        if self._order_id:
            await self.revoke_order(self._order_id)

        await self.create_new_order(average_price)

