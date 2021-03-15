# -*- coding: utf-8 -*-

from aioquant import quant


def binance_strategy():
    from strategies.binance_strategy import BinanceStrategy
    BinanceStrategy()
    # from strategies.market_info import CustomMarket
    # CustomMarket()


if __name__ == '__main__':
    # config_file = None
    config_file = "config.json"
    quant.start(config_file, entrance_func=binance_strategy)