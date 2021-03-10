# -*- coding: utf-8 -*-

from aioquant.platform.binance import BinanceRestAPI
from aioquant.tasks import SingleTask
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
        SingleTask.run(self.revoke_order)


    async def get_assert_info(self):
        """获取资产信息"""
        success, error = await self._rest_api.get_user_account()
        logger.info("success: ", success, caller=self)
        # logger.info("error: ", error, caller=self)

    async def create_new_order(self):
        """下单"""
        symbol = "EOSUSDT"
        action = "SELL"
        price = "4.200"
        quantity = "2.5"  # min 2.5
        success, error = await self._rest_api.create_order(action, symbol, price, quantity)
        logger.info("success: ", success, caller=self)
        logger.info("error: ", error, caller=self)

    async def revoke_order(self):
        """撤销订单"""

        symbol = "EOSUSDT"
        order_id = "1594147489"

        success, error = await self._rest_api.revoke_order(symbol, order_id)
        logger.info("success: ", success, caller=self)
        logger.warn("error: ", error, caller=self)
