import asyncio
import collections
import time
import traceback

from binance import AsyncClient, BinanceSocketManager

from config import *
from crypto import *


def test_api(crypto, watching_symbols, closed_klines):
    for s in watching_symbols:
        klines_api = crypto.get_klines(s.symbol, 500)
        if klines_api is None:
            continue

        dq = collections.deque(maxlen=500)
        closed_klines[s.symbol] = dq

        last_close_api = None
        for k in klines_api:
            if k.close_time - k.open_time != (15 * 60 * 1000 - 1):
                print(
                    f"Bad K line interval: {k.close_time} - {k.open_time} = {k.close_time - k.open_time}")

            if last_close_api is not None:
                if k.close_time - last_close_api != (15 * 60 * 1000):
                    print(
                        f"Bad inter K line interval: {k.close_time} - {last_close_api} = {k.close_time - last_close_api}")
            last_close_api = k.close_time

            # put k into closed_klines[s.symbol]
            dq.append(k)

    # print(time.time_ns())
    # print(last_close_api)
    b = time.time_ns() - (klines_api[-1].open_time*1000000)
    print(f"Last K line closed diff from now = {b} ({b / 1000000000}s)")
    if b >= (30 * 60 * 1000000000):
        print("Oops, missed a K line")


async def main_1m():
    config = Config()
    crypto = Crypto(config)
    cash_currency = config.position_manage['cash_currency']
    exclude_currencies = config.position_manage['exclude_currencies']

    watching_symbols = crypto.get_tradable_symbols(
        cash_currency, exclude_currencies)
    print(watching_symbols)

    closed_klines = dict()

    # test_api(crypto, watching_symbols, closed_klines)

    client = await AsyncClient.create()
    bm = BinanceSocketManager(client)
    # start any sockets here, i.e a trade socket
    streams = [f"{s.symbol.lower()}@kline_1m" for s in watching_symbols]
    ms_1m = bm.multiplex_socket(streams)

    price_cache = dict()
    last_time_get_closed_klines = dict()

    # then start receiving messages
    async with ms_1m as tscm:
        while True:
            try:
                res = await tscm.recv()
                # print(res)
            except Exception as err:
                print("ERRRRRRRRRRRRR awating data from WebSocket")
                traceback.print_tb(err.__traceback__)
                raise

            try:
                trade_symbol = res['data']['s']
                close_price = res['data']['k']['c']
                kline_start_time = res['data']['k']['t']
                kline_close_time = int(res['data']['k']['T'])

                if res['data']['k']['x']:
                    if trade_symbol in last_time_get_closed_klines:
                        # k = Kline([kline_start_time, kline_close_time])
                        last_time_close = last_time_get_closed_klines[trade_symbol]
                        print(
                            f"Close time diff = {kline_close_time - last_time_close}")

                    last_time_get_closed_klines[trade_symbol] = int(
                        kline_close_time)

                # print(f"{trade_symbol} {kline_start_time} ~ price = {close_price} {cash_currency}")
                price_cache[trade_symbol] = close_price
            except Exception as err:
                print("ERRRRRRRRRRRRR processing data")
                traceback.print_tb(err.__traceback__)
                raise

    await client.close_connection()

if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    cors = asyncio.wait([main_1m()])
    loop.run_until_complete(cors)
