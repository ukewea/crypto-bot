import asyncio
from binance import AsyncClient, BinanceSocketManager
from config import *
from crypto import *


async def main():
    config = Config()
    crypto = Crypto(config)
    cash_currency = config.position_manage['cash_currency']
    exclude_currencies = config.position_manage['exclude_currencies']

    watching_symbols = crypto.get_tradable_symbols(cash_currency, exclude_currencies)
    print(watching_symbols)
    client = await AsyncClient.create()
    bm = BinanceSocketManager(client)
    # start any sockets here, i.e a trade socket
    streams = [f"{s.symbol.lower()}@kline_15m" for s in watching_symbols]
    ms = bm.multiplex_socket(streams)

    price_cache = dict()
    # then start receiving messages
    async with ms as tscm:
        while True:
            res = await tscm.recv()
            # trade_symbol = res['data']['s']
            # latest_price = res['data']['c']
            if res['data']['k']['x']:
                print(res)
            # print(f"{trade_symbol} price = {latest_price} {cash_currency}")
            # price_cache[trade_symbol] = latest_price

    await client.close_connection()

if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
