import file_based_asset_positions
import position
import crypto
import copy
from binance.enums import *
from decimal import Decimal
import logging.config


log = logging.getLogger(__name__)


class OrderResult:
    def __init__(self):
        self.ok = False
        self.transactions = list()
        self.raw_response = None

    def Failure():
        r = OrderResult()
        r.ok = False
        return r


def open_position_with_max_fund(
    api_client: crypto.Crypto,
    base_asset: str,
    trade_symbol: str,
    cash_asset: str,
    max_fund: Decimal,
    asset_position: position.Position,
    symbol_info: crypto.WatchingSymbol
) -> OrderResult:
    """
    開倉：限制最多買入金額，買入指定交易對
    api_client: API client
    base_asset: 資產名稱
    trade_symbol: 資產交易時的交易對
    cash_asset: 現金的資產名稱
    max_fund: 最大投入資金
    asset_position: 資產目前倉位結構
    symbol_info: 交易對在交易所內的交易情況、交易限制等資訊
    """

    log.debug(f"[{trade_symbol}] Entering buy process")

    open_quantity = asset_position.open_quantity
    if open_quantity > 0:
        log.debug(f"[{trade_symbol}] Already holds {base_asset} ({open_quantity.normalize():f}), skip the buy")
        return OrderResult.Failure()

    symbol_filters = symbol_info.info['filters']
    filters_dict = dict()
    for f in symbol_filters:
        filters_dict[f['filterType']] = f

    # 先檢查資金是否滿足最小成交額需求
    min_notional_dict = filters_dict['MIN_NOTIONAL']
    # print(f"MIN_NOTIONAL dict: {min_notional_dict}")
    min_notional = Decimal(min_notional_dict['minNotional'])
    if (max_fund < min_notional):
        log.warning(f"[{trade_symbol}] No enough cash to send a BUY order"
        f" (minNotional = {min_notional}, our budget = {max_fund}")
        return OrderResult.Failure()

    # 建立 Decimal 如果能傳字串就盡量傳字串，傳數字進來會有精度問題
    latest_price_api_call = api_client.get_latest_price(trade_symbol)
    latest_price = Decimal(latest_price_api_call['price'])
    # print(f'Latest price of {trade_symbol} = {latest_price}')

    # 計算買入的數量，用 order_quote_qty(..) 會買到小數點後面太多位，到時無法全部平倉
    lot_filter = filters_dict['LOT_SIZE']
    max_buyable_quantity = max_fund / latest_price
    min_qty = Decimal(lot_filter['minQty'])
    max_qty = Decimal(lot_filter['maxQty'])
    step_size = Decimal(lot_filter['stepSize'])

    if max_buyable_quantity < min_qty:
        log.warning(f"[{trade_symbol}] Cannot purchase enough quantity of {base_asset} to meet minQty"
            f" (min qty = {min_qty}, our max qty = {max_buyable_quantity}")
        return OrderResult.Failure()

    # 移除 stepSize 無法整除的部份，賣出時才能全部平倉
    rounded_quantity = max_buyable_quantity - (max_buyable_quantity % step_size)

    if rounded_quantity > max_qty:
        log.debug(f"[{trade_symbol}] Desired BUY qty '{rounded_quantity}' exceeds limit, buy '{max_qty}' instead")
        rounded_quantity = max_qty

    log.debug(f"[{trade_symbol}] BUY qty = {rounded_quantity.normalize():f}"
        f", estimated cost = (qty * latest_quote) = {(rounded_quantity * latest_price).normalize():f}")

    log.debug(f"[{trade_symbol}] Sending BUY order to exchange")
    order_ok, order = api_client.order_qty(SIDE_BUY, f'{rounded_quantity.normalize():f}', trade_symbol)

    if order_ok:
        ret = OrderResult()
        ret.ok = True
        ret.raw_response = order
        log.debug(f"[{trade_symbol}] BUY order sent successfully, adding transaction to database")
        add_transactions_to_position(ret, api_client, base_asset, trade_symbol, cash_asset, asset_position, order)
        return ret
    else:
        log.error(f"[{trade_symbol}] Error while sending BUY order ({str(order)})")
        return OrderResult.Failure()


def close_all_position(
    api_client: crypto.Crypto,
    base_asset: str,
    trade_symbol: str,
    cash_asset: str,
    asset_position: position.Position,
    symbol_info: dict
) -> OrderResult:
    """全部平倉某資產"""

    log.debug(f"[{trade_symbol}] Entering sell process")

    open_quantity = asset_position.open_quantity
    if open_quantity <= 0:
        log.debug(f"[{trade_symbol}] No {base_asset} can sell")
        return OrderResult.Failure()

    # 只平倉有紀錄的資產，避免平倉到不是自動開倉的部位
    log.debug(f"[{trade_symbol}] Sending SELL order to exchange, qty = {open_quantity.normalize():f}")
    order_ok, order = api_client.order_qty(SIDE_SELL, open_quantity, trade_symbol)
    if order_ok:
        # order filled:
        # {'symbol': 'BNBUSDT', 'orderId': 854270, 'orderListId': -1, 'clientOrderId': 'FH0FsNLBSgFFwQVnb0xU6r', 'transactTime': 1620188399140, 'price': '0.00000000', 'origQty': '0.03000000', 'executedQty': '0.03000000', 'cummulativeQuoteQty': '13.90200000', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'MARKET', 'side': 'SELL', 'fills': [{'price': '463.40000000', 'qty': '0.03000000', 'commission': '0.00000000', 'commissionAsset': 'USDT', 'tradeId': 365249}]}

        # order not filled:
        # {'symbol': 'XRPUSDT', 'orderId': 1292, 'orderListId': -1, 'clientOrderId': 'Fc1OgHu9AUrytFTQUJOT16', 'transactTime': 1620188400305, 'price': '0.00000000', 'origQty': '16.30000000', 'executedQty': '0.00000000', 'cummulativeQuoteQty': '0.00000000', 'status': 'EXPIRED', 'timeInForce': 'GTC', 'type': 'MARKET', 'side': 'SELL', 'fills': []}
        ret = OrderResult()
        ret.ok = True
        ret.raw_response = order
        log.debug(f"[{trade_symbol}] SELL order sent successfully, adding transaction to database")
        add_transactions_to_position(ret, api_client, base_asset, trade_symbol, cash_asset, asset_position, order)
        return ret
    else:
        log.error(f"[{trade_symbol}] Error while sending SELL order ({str(order)})")
        return OrderResult.Failure()

def add_transactions_to_position(
    order_result: OrderResult,
    api_client: crypto.Crypto,
    base_asset: str,
    trade_symbol: str,
    cash_asset: str,
    asset_position: position.Position,
    order: dict
):
    # {'symbol': 'DOGEUSDT', 'orderId': 786775885, 'orderListId': -1, 'clientOrderId': 'gQp1YKqpjVBMwlkUIcCgWV', 'transactTime': , 'price': '0.00000000', 'origQty': '36.60000000', 'executedQty': '36.60000000', 'cummulativeQuoteQty': '13.96546200', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'MARKET', 'side': 'BUY', 'fills': [{'price': '0.38157000', 'qty': '36.60000000', 'commission': '0.00001676', 'commissionAsset': 'BNB', 'tradeId': 142837993}]}
    order_symbol = order['symbol']
    order_side = order['side']
    order_type = order['type']
    order_id = order['orderId']
    fills = order['fills']
    commision_to_cash_prices = dict()

    for fill in fills:
        fill_qty = fill['qty']
        fill_price = fill['price']
        fill_commission = Decimal(fill['commission'])
        fill_commission_asset = fill['commissionAsset']

        # 若手續費不是以 USDT 計價，轉換為 USDT
        if fill_commission_asset != cash_asset:
            commision_to_cash_price = commision_to_cash_prices.get(fill_commission_asset, None)
            if commision_to_cash_price is None:
                trade_symbol_commission = f"{fill_commission_asset}{cash_asset}"
                latest_commision_to_cash_price_api_call = api_client.get_latest_price(trade_symbol_commission)
                commision_to_cash_price = Decimal(latest_commision_to_cash_price_api_call['price'])
                commision_to_cash_prices[fill_commission_asset] = commision_to_cash_price

            fill_commission_as_cash = fill_commission * commision_to_cash_price
        else:
            fill_commission_as_cash = fill_commission

        transaction = position.Transaction(
            time=int(order['transactTime']),
            activity=order_side,
            symbol=base_asset,
            trade_symbol=order_symbol,
            quantity=Decimal(fill_qty),
            price=Decimal(fill_price),
            commission=Decimal(fill_commission),
            commission_asset=fill_commission_asset,
            commission_as_usdt=fill_commission_as_cash,
            order_id=order_id,
            trade_id=fill['tradeId'],
            closed_trade_ids=[])
        asset_position.add_transaction(transaction)
        order_result.transactions.append(copy.deepcopy(transaction))
