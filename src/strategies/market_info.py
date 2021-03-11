# -*- coding: utf-8 -*-

from aioquant.platform.binance import BinanceRestAPI
from aioquant.tasks import SingleTask
from aioquant.utils import logger


class CustomMarket:

    def __init__(self) -> None:
        host = "https://api.binance.com"
        access_key = "access_key"
        secret_key = "secret_key"

        self._rest_api = BinanceRestAPI(host, access_key, secret_key)

        self.symbol = "EOSUSDT"

        SingleTask.run(self.get_orderbook)

        # SingleTask.run(self.get_k_line)

        # SingleTask.run(self.get_trade)


    async def get_orderbook(self):
        """获取盘口订单薄数据"""
        symbol = self.symbol
        success, error = await self._rest_api.get_orderbook(symbol, 10)
        logger.info("success", success, caller=self)
        # logger.info("error", error, caller=self)

    async def get_k_line(self):
        """获取K线数据"""
        symbol = self.symbol
        success, error = await self._rest_api.get_klines(symbol, interval="1m", limit=10)
        logger.info("success", success, caller=self)
        logger.info("error", error, caller=self)

    async def get_trade(self):
        """获取最新的逐笔成交数据"""
        symbol = self.symbol
        success, error = await self._rest_api.get_latest_trade(symbol, 10)
        logger.info("success", success, caller=self)
        logger.info("error", error, caller=self)

