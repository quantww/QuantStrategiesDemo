# -*- coding: utf-8 -*-

from aioquant import quant


def binance_strategy():
    print("My first binance demo...")
    from strategies.binance_strategy import BinanceStrategy
    BinanceStrategy()


if __name__ == '__main__':
    config_file = "config.json"
    quant.start(config_file, entrance_func=binance_strategy)