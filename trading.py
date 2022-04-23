import requests
import json
import talib as ta
import pandas as pd
import datetime

from config import endpoints, auth, urls, initial_stocks


## data for the data frame for each position
dict_data = {}

## trading price fix for API - (e.g. 80€ would be 800000)
price_fix = 10000

def checkPositions():
    print("## checking positions...")
    position_response = requests.get(urls.trading_urL + endpoints.positions, headers=auth.createAuthParameter())
    json_data = json.loads(position_response.text)
    pending_orders = checkPendingOrders()
    predefined_stocks = initial_stocks.stock_collection()
    for order in pending_orders:
        if not predefined_stocks.__contains__(order["isin"]):
            predefined_stocks.append(order["isin"])

    #print(predefined_stocks)
    if json_data["total"] > 0:
        print("### found " + str(json_data["total"]) + " positions.")
        for res in json_data["results"]:
            pos = res["isin"]
            predefined_stocks.remove(pos)
            if shouldClose(pos):
                closePosition(pos, res["quantity"])
    else:
        print("### no positions....will check pre-defined ISINs for buying.")#
    # check if there is money left to buy
    print(predefined_stocks)
    checkStocksForBuying(predefined_stocks)

def checkPendingOrders():
    order_response = requests.get(urls.trading_urL + endpoints.order, headers=auth.createAuthParameter())
    json_data = json.loads(order_response.text)
    return json_data["results"]

def checkStocksForBuying(results):
    for pos in results:
        print("#### checking " + pos)
        if shouldGoLong(pos):
            quote = getLatestQuoteForPos(pos)
            bid_quote = quote["b"]
            buy_amount = round(initial_stocks.getBuyAmount() / bid_quote)
            if bid_quote*buy_amount*price_fix <= getCashBalance():
                openPosition(pos, quote["b"], buy_amount)
            else:
                print("#### can not buy " + pos + ". Balance too low!")

def getCashBalance():
    account_response = requests.get(urls.trading_urL + endpoints.account, headers=auth.createAuthParameter())
    json_data = json.loads(account_response.text)
    cash_to_invest = json_data["results"]["cash_to_invest"]
    # print("CASH: " + str(cash_to_invest))
    return cash_to_invest

# from date has to be max(!) 60 days in the past
def calculateFromDate():
    past_date = datetime.date.today() + datetime.timedelta(days=-59)
    return str(past_date)

# get hostorical data / OHLC data
def getOhlcForPos(pos):
    global dict_data
    endpoint_ohlc = endpoints.ohlc.replace("{ISIN}", pos)
    endpoint_ohlc = endpoint_ohlc.replace("{FROM}", calculateFromDate())
    ohlc_response = requests.get(urls.markets_url + endpoint_ohlc, headers=auth.createAuthParameter())
    json_data = json.loads(ohlc_response.text)
    # print(json_data)
    df = pd.DataFrame(json_data["results"]).dropna()
    dict_data[pos] = df

def calcBollingerMidBands(pos):
    # get close positions out of data frame
    global dict_data
    close_positions = dict_data[pos]["c"]
    # print("BOLLINGER CLOSE POSITIONS")
    # print(close_positions)
    # Bollinger Mid Band = 20 day SMA
    sma_df = ta.SMA(close_positions, 20).dropna()
    return sma_df.iloc[-1]

def calcEmaAndLength(pos, length):
    global dict_data
    close_positions = dict_data[pos]["c"]
    ema_df = ta.EMA(close_positions, timeperiod=length).dropna()
    return ema_df.iloc[-1]

# get latest quote
def getLatestQuoteForPos(pos):
    quote_response = requests.get(urls.markets_url + endpoints.quote + pos, headers=auth.createAuthParameter())
    json_data = json.loads(quote_response.text)
    for quote in json_data['results']:
        '''
        print(quote['isin'])
        print(quote['a']) # a = ask
        print(quote['b']) # b = bid
        print("\n")
        '''
        return quote

def shouldGoLong(pos):
    getOhlcForPos(pos)
    bb = calcBollingerMidBands(pos)
    ema9 = calcEmaAndLength(pos, 9)
    ema20 = calcEmaAndLength(pos, 20)
    if ema9 > bb and ema20 > bb:
        print("##### should buy: " + pos)
        return True
    else:
        print("##### position " + pos + " is fine.")
        return False

def shouldClose(pos):
    getOhlcForPos(pos)
    bb = calcBollingerMidBands(pos)
    ema9 = calcEmaAndLength(pos, 9)
    ema20 = calcEmaAndLength(pos, 20)
    if ema9 <= bb and ema20 <= bb:
        print("##### should close: " + pos)
        return True
    else:
        print("##### position " + pos + " is fine.")
        return False

def openPosition(pos, price, amount):
    buying_date = str(datetime.date.today())
    buy_response = requests.post(urls.trading_urL + endpoints.order,
                                 data=json.dumps({
                                  "isin": pos,
                                  "expires_at": buying_date,
                                  "side": "buy",
                                  "quantity": amount,
                                  "limit_price" : price,
                                  "venue": "XMUN",
                                }),
                                 headers=auth.createAuthParameter())
    json_data = json.loads(buy_response.text)
    print(json_data)
    order_id = json_data["results"]["id"]
    print("###### created BUY Order: " + str(order_id))
    activateOrder(order_id)

def closePosition(pos, amount):
    quote = getLatestQuoteForPos(pos)
    ask_quote = quote["a"]
    print("Closing position " + pos + " and quantity: " + str(amount))
    selling_date = str(datetime.date.today())
    sell_response = requests.post(urls.trading_urL + endpoints.order,
                                  data=json.dumps({
                                     "isin": pos,
                                     "expires_at": selling_date,
                                     "side": "sell",
                                     "limit_price": ask_quote,
                                     "quantity": amount
                                 }),
                                  headers=auth.createAuthParameter())
    json_data = json.loads(sell_response.text)
    print(json_data)
    order_id = json_data["results"]["id"]
    print("###### created SELL Order: " + str(order_id))
    activateOrder(order_id)

def activateOrder(orderId):
    param = endpoints.activate_order.replace("{ORDERID}", orderId)
    activation_response = requests.post(urls.trading_urL + param,
                                        data=json.dumps({
                                # todo: set real pin for prod
                                "pin": "1234"
                            }),
                                        headers=auth.createAuthParameter())
    json_data = json.loads(activation_response.text)
    print("####### ACTIVATING ORDER: " + str(orderId) + " has status: " + json_data["status"])
