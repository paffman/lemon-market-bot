########################################
# Utility to clean up positions
# in paper trading
########################################

import json
import requests
from config import endpoints, auth
from config import urls
import trading

def main():
    for res in trading.checkPendingOrders():
        if res["status"] != "expired" and res["status"] != "cancelled" and res["status"] != "inactive":
            param = endpoints.cancel_order.replace("{ORDERID}", res["id"])
            response = requests.delete(urls.trading_urL + param,
                                      headers=auth.createAuthParameter())
            json_data = json.loads(response.text)
            print(json_data)

main()
