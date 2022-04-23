## Endpoint Definitions

# receive account data
account = "/account/"

# read positions
positions = "/positions/"

# read quotes
quote = "/quotes/latest/?isin="

# get OHLC data for ISIN
'''
m1	The data is aggregated on a per-minute basis.
h1	The data is aggregated on an hourly basis.
d1	The data is aggregated on a daily basis.
'''
ohlc = "/ohlc/d1/?mic=XMUN&isin={ISIN}&from={FROM}&isin="

# create orders
order = "/orders/"

# each order must be activated otherwise it will not be placed!
activate_order = "/orders/{ORDERID}/activate/"

cancel_order = "/orders/{ORDERID}/"