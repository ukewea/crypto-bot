import file_based_asset_positions
import position
from crypto import *
from binance.enums import *
from decimal import Decimal

def open_position_with_max_fund(
    api_client: crypto.Crypto,
    base_asset: str,
    trade_symbol: str,
    cash_asset: str,
    max_fund: Decimal,
    asset_position: position.Position,
    symbol_info: dict
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
    open_quantity = asset_position.open_quantity
    if open_quantity > 0:
        print(f"Already HODLING {base_asset} ({open_quantity}), skip the buy")
        return OrderResult.Failure()

    # 計算買入的數量，用 order_quote_qty(..) 會買到小數點後面太多位，到時無法全部平倉
    symbol_filters = symbol_info['filters']
    filters_dict = dict()
    for f in symbol_filters:
        filters_dict[f['filterType']] = f

    # 先檢查資金是否滿足最小成交額需求
    min_notional = Decimal(filters_dict['MIN_NOTIONAL']['minNotional'])
    if (max_fund < min_notional):
        print(f"No enough cash to buy {base_asset} "
        f"(minNotional = {min_notional}, our budget = {max_fund}")
        return OrderResult.Failure()

    # 建立 Decimal 如果能傳字串就盡量傳字串，傳數字進來會有精度問題
    latest_price_api_call = api_client.get_latest_price(trade_symbol)
    latest_price = Decimal(latest_price_api_call['price'])

    lot_filter = filters_dict['LOT_SIZE']
    max_buyable_quantity = max_fund / latest_price
    min_qty = Decimal(lot_filter['minQty'])
    max_qty = Decimal(lot_filter['maxQty'])
    step_size = Decimal(lot_filter['stepSize'])

    if max_buyable_quantity < min_qty:
        print(f"Cannot purchase enough quantity of {base_asset} to meet minQty "
        f"(minQty = {min_notional}, our max_buyable_quantity = {max_buyable_quantity}")
        return OrderResult.Failure()

    # 移除 stepSize 無法整除的部份，賣出時才能全部平倉
    rounded_quantity = max_buyable_quantity - (max_buyable_quantity % step_size)

    if rounded_quantity > max_qty:
        print(f"rounded_quantity exceeds maxQty {max_qty}, buy {max_qty} of {base_asset} instead")
        rounded_quantity = max_qty

    order_ok, order = api_client.order_quote_qty(SIDE_BUY, rounded_quantity, symbol)
    if order_ok:
        ret = OrderResult()
        ret.ok = True
        ret.raw_response = order
        add_transactions_to_position(ret, api_client, base_asset, trade_symbol, cash_asset, asset_position, order)
        return ret
    else:
        print(f"Error while try buying {base_asset}: {str(order)}")
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
    open_quantity = asset_position.open_quantity
    if open_quantity <= 0:
        print(f"No {base_asset} to sell")
        return OrderResult.Failure()

    # 只平倉有紀錄的資產，避免平倉到不是自動開倉的部位
    order_ok, order = crypto.order_qty(SIDE_SELL, open_quantity, trade_symbol)
    if order_ok:
       ret = OrderResult()
       ret.ok = True
       ret.raw_response = order
       add_transactions_to_position(ret, api_client, base_asset, trade_symbol, cash_asset, asset_position, order)
       return ret
    else:
        print(f"Error while try buying {base_asset}: {str(order)}")
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
            if value is None:
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

        if order_side == SIDE_BUY:
            print(f"BOT +{fill_qty} {fill_order_symbol} @{fill_price} {order_type}")
        elif order_side == SIDE_SELL:
            print(f"SELL -{fill_qty} {fill_order_symbol} @{fill_price} {order_type}")
        else:
            print(f"{order_side} ?{fill_qty} {fill_order_symbol} @{fill_price} {order_type}")

class OrderResult:
    def __init__(self):
        self.ok = False
        self.transactions = list()
        self.raw_response = None

    def Failure() -> OrderResult:
        r = OrderResult()
        r.ok = False
        return r
