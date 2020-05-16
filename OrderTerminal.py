#! /usr/bing/env python

##############################
# very simple order script with user input
##############################

import requests
import json
import sys
import time
import os
from datetime import datetime
import logging

from colorama import init
from colorama import Fore, Back
from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import yes_no_dialog
from prompt_toolkit.styles import Style


load_dotenv()
init(autoreset=True)

dialog_style = Style.from_dict({
    'dialog':             'bg:#88ff88',
    'dialog frame.label': 'bg:#ffffff #000000',
    'dialog.body':        'bg:#000000 #00ff00',
    'dialog shadow':      'bg:#00aa00',
})

REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")

#################
# Get a new access token and save to token.json file
# This get's executed on script load, and when expired token
# is used in api calls
#################



def getNewToken():

    print(" Fetching new token, please wait...")
    time.sleep(2)

    payload = {'grant_type': 'refresh_token', 'refresh_token': REFRESH_TOKEN,
               'client_id': CLIENT_ID}

    r = requests.post(
        "https://api.tdameritrade.com/v1/oauth2/token", data=payload)

    if r.status_code != 200:
        print("Unable to obtain new token...Please try again ")
        return
    print(" New access token obtained")
    data = r.json()

    with open(os.path.join(sys.path[0], 'token.json'), 'w') as file:
        json.dump(data, file)

    getInput()

#################
# Grab the fresh access token located in token.json file to
# use throughout the script
#################


def grabToken():
    with open(os.path.join(sys.path[0], 'token.json')) as f:
        accessData = json.load(f)

    grabToken.authcode = accessData['access_token']

    # Refresh token saved in env file. Get a new on of these every 90 days manually
    grabToken.token = REFRESH_TOKEN

    os.system('cls')


def title():
    print(Back.GREEN + Fore.WHITE +
          "\n ######################### \n COMMAND LINE TRADING APP  \n ######################### ")


def initialLoad():
    title()
    getNewToken()


def positionReport():
    grabToken()
    os.system('cls')
    title()
    headers = {'Authorization': f'Bearer {grabToken.authcode}'}

    r = requests.get(
        f"https://api.tdameritrade.com/v1/accounts/{ACCOUNT_ID}?fields=positions", headers=headers)

    if r.status_code != 200:
        print("Errored out...getting new token. Then try again ")
        getNewToken()
        return

    symbols = r.json()['securitiesAccount']['positions']
    print(f"\n Current Positions:")
    for symbol in symbols:
        stringShort = f"-{[symbol][0]['shortQuantity']}"
        stringPnl = str(round([symbol][0]['currentDayProfitLoss'], 2))
        pnl = round([symbol][0]['currentDayProfitLoss'], 2)
        print(f" --------------------------------\n {[symbol][0]['instrument']['symbol']} | Qty: { stringShort if [symbol][0]['shortQuantity'] > 0 else [symbol][0]['longQuantity']} | Market Value: {round([symbol][0]['marketValue'],2)} | Avg price: {round([symbol][0]['averagePrice'],2)} | Day PnL: $ {Fore.RED + stringPnl if pnl < 0 else Fore.GREEN + stringPnl}")


def getOrders():
    grabToken()
    os.system('cls')
    title()
    headers = {'Authorization': f'Bearer {grabToken.authcode}'}

    r = requests.get(
        f"https://api.tdameritrade.com/v1/accounts/{ACCOUNT_ID}/orders?status=queued", headers=headers)

    if r.status_code != 200:
        print("Errored out...getting new token. Then try again ")
        getNewToken()
        return

    orders = r.json()
    print(f"\n Working Orders:")
    if orders:
        for order in orders:
            print(f" Id: {order['orderId']} | Symbol: {order['orderLegCollection'][0]['instrument']['symbol']} | Type: {order['orderType']} | Side: {order['orderLegCollection'][0]['instruction']} | Qty: {order['orderLegCollection'][0]['quantity']}")
    else:
        print(" No working orders")

    getInput()


def balancesReport():
    grabToken()
    os.system('cls')
    title()
    headers = {'Authorization': f'Bearer {grabToken.authcode}'}

    r = requests.get(
        f"https://api.tdameritrade.com/v1/accounts/{ACCOUNT_ID}?", headers=headers)

    if r.status_code != 200:
        print("Errored out...getting new token. Then try again ")
        getNewToken()
        return

    data = r.json()['securitiesAccount']['projectedBalances']
    print(f"\n Balance Report:")
    print(f"\n Day Trading Buying Power: {data['dayTradingBuyingPower']}")

    getInput()


def getQuote(symbol):
    grabToken()
    os.system('cls')
    title()
    headers = {'Authorization': f'Bearer {grabToken.authcode}',
               'Content-Type': 'application/json'}

    # find current ask price
    r = requests.get(
        f"https://api.tdameritrade.com/v1/marketdata/{symbol}/quotes", headers=headers)

    if r.status_code != 200:
        print("Errored out...getting new token. Then try again ")
        getNewToken()
        return

    data = r.json()
    print(f"\n Symbol: {data[symbol.upper()]['symbol']} \n Bid: {data[symbol.upper()]['bidPrice']} \n Ask: {data[symbol.upper()]['askPrice']} \n Volume: {data[symbol.upper()]['totalVolume']} \n % Change: {data[symbol.upper()]['netPercentChangeInDouble']} ")

    getInput()

######################
# ORDER ENTRY FUNCTIONS
# Note: 'notional' orders are when you want to just quickly enter a dollar amount
# to trade with, the system will calculate the number of shares to trade from that. ex: "I
# want to buy $50000 dollars worth of facebook at market" - the system calculates the amount
# to buy based upon dollar figure and the current ask price
######################


def placeMarketTradeNotional(orderType, symbol, side, dollarQty):
    grabToken()
    headers = {'Authorization': f'Bearer {grabToken.authcode}',
               'Content-Type': 'application/json'}

    # find current ask price
    r = requests.get(
        f"https://api.tdameritrade.com/v1/marketdata/{symbol}/quotes", headers=headers)

    data = r.json()

    askPrice = data[symbol.upper()]['askPrice']

    payload = {
        "orderType": orderType,
        "session": "NORMAL",
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "orderLegCollection": [
                    {
                        "instruction": side,
                        "quantity": (round(float(dollarQty) / askPrice)),
                        "instrument": {
                            "symbol": symbol,
                            "assetType": "EQUITY"
                        }
                    }
        ]
    }

    requests.post(
        f"https://api.tdameritrade.com/v1/accounts/{ACCOUNT_ID}/orders", headers=headers, data=json.dumps(payload))

    getOrders()


def placeMarketTradeShares(orderType, symbol, side, qty):
    grabToken()
    headers = {'Authorization': f'Bearer {grabToken.authcode}',
               'Content-Type': 'application/json'}
    payload = {
        "orderType": orderType,
        "session": "NORMAL",
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "orderLegCollection": [
                    {
                        "instruction": side,
                        "quantity": qty,
                        "instrument": {
                            "symbol": symbol,
                            "assetType": "EQUITY"
                        }
                    }
        ]
    }

    requests.post(
        f"https://api.tdameritrade.com/v1/accounts/{ACCOUNT_ID}/orders", headers=headers, data=json.dumps(payload))

    getOrders()


def placeLimitTradeNotional(orderType, symbol, side, price, dollarQty):
    grabToken()
    headers = {'Authorization': f'Bearer {grabToken.authcode}',
               'Content-Type': 'application/json'}

    # find current ask price
    r = requests.get(
        f"https://api.tdameritrade.com/v1/marketdata/{symbol}/quotes", headers=headers)

    data = r.json()

    askPrice = data[symbol.upper()]['askPrice']

    headers = {'Authorization': f'Bearer {grabToken.authcode}',
               'Content-Type': 'application/json'}
    payload = {
        "orderType": orderType,
        "session": "NORMAL",
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "price": price,
        "orderLegCollection": [
                    {
                        "instruction": side,
                        "quantity": (round(float(dollarQty) / askPrice)),
                        "instrument": {
                            "symbol": symbol,
                            "assetType": "EQUITY"
                        }
                    }
        ]
    }

    requests.post(
        f"https://api.tdameritrade.com/v1/accounts/{ACCOUNT_ID}/orders", headers=headers, data=json.dumps(payload))

    getOrders()


def placeLimitTradeShares(orderType, symbol, side, price, qty):
    grabToken()
    headers = {'Authorization': f'Bearer {grabToken.authcode}',
               'Content-Type': 'application/json'}
    payload = {
        "orderType": orderType,
        "session": "NORMAL",
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "price": price,
        "orderLegCollection": [
                    {
                        "instruction": side,
                        "quantity": qty,
                        "instrument": {
                            "symbol": symbol,
                            "assetType": "EQUITY"
                        }
                    }
        ]
    }

    requests.post(
        f"https://api.tdameritrade.com/v1/accounts/{ACCOUNT_ID}/orders", headers=headers, data=json.dumps(payload))

    getOrders()


def placeStopLimitTradeShares(symbol, side, stopPrice, qty):
    grabToken()
    headers = {'Authorization': f'Bearer {grabToken.authcode}',
               'Content-Type': 'application/json'}
    payload = {
        "orderType": "STOP",
        "session": "NORMAL",
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "stopPrice": stopPrice,
        "stopType": "STANDARD",
        "orderLegCollection": [
                    {
                        "instruction": side,
                        "quantity": qty,
                        "instrument": {
                            "symbol": symbol,
                            "assetType": "EQUITY"
                        }
                    }
        ]
    }

    requests.post(
        f"https://api.tdameritrade.com/v1/accounts/{ACCOUNT_ID}/orders", headers=headers, data=json.dumps(payload))

    getOrders()

######################
# user inputs / menu
######################


def getInput():

    print(Fore.YELLOW + " --- MAIN MENU ---")
    prompt = input(
        " Please Select: \n Trade (t)\n Position Report (p)\n Quote (q)\n Balance Report (b)\n View Working Orders (o)\n ")
    ######### trading ############
    if prompt == "t":
        os.system('cls')
        title()
        print(Fore.YELLOW + " --- Order Type Selection ---")
        type = input(
            " Please Select: \n Market Order (m)\n Limit Order (l) \n Stop (s) \n Cancel (c). ")
        ######### stop #########
        if type == "s":
            cmd = input(
                " Enter LIMIT trade command (ex: 's 1000 fb 210.5') or (c) to cancel: ")
            if len(cmd.split()) != 4 and cmd != "c":
                print(" Invalid format, starting over...")
                getInput()
            if cmd == "c":
                os.system('cls')
                title()
                getInput()
            else:
                side, qty, symbol, stopPrice = cmd.split()
                if side == "b":
                    printSide = "Buy"
                if side == "s":
                    printSide = "Sell"
                confirmTrade = input(
                    f" Confirm trade? [{printSide} {qty} shares of {symbol} at STOP PRICE: {stopPrice}] YES (y) or NO (n)")
                if confirmTrade == "y":
                    if side == "b":
                        cleanSide = "BUY"
                    else:
                        cleanSide = "SELL"
                    cleanPrice = stopPrice

                    # actually place the trade
                    placeStopLimitTradeShares(
                        symbol, cleanSide, cleanPrice, qty)
                    getInput()
                else:
                    os.system('cls')
                    title()
                    getInput()
        ######### limit type #########
        if type == "l":
            print(Fore.YELLOW + " --- Quantity Options ---")
            whichType = input(
                " Please Select:\n Notional Quantity (n)\n Shares Quantity (s)\n Cancel (c) \n ")
            if whichType == "n":
                print(Fore.YELLOW + " --- Trade Script ---")
                cmd = input(
                    " Enter trade command, use $ notional value (ex: 'b 100000 fb 210.5') or (c) to cancel: ")
                if len(cmd.split()) != 4 and cmd != "c":
                    print(" Invalid format, starting over...")
                    getInput()
                if cmd == "c":
                    os.system('cls')
                    title()
                    getInput()
                else:
                    side, qty, symbol, price = cmd.split()
                    if side == "b":
                        printSide = "Buying"
                    if side == "s":
                        printSide = "Selling"
                    print(Fore.YELLOW + " --- Confirm ---")

                    confirmTrade = yes_no_dialog(
                    title='Confirm Trade',
                    style=dialog_style,
                    text=f" Confirm {printSide} {qty} $ worth of {symbol} at {price}").run()

                    if confirmTrade == True:
                        if side == "b":
                            cleanSide = "BUY"
                        else:
                            cleanSide = "SELL"
                        cleanOrderType = "LIMIT"
                        cleanPrice = price

                        # actually place the trade
                        placeLimitTradeNotional(
                            cleanOrderType, symbol, cleanSide, cleanPrice, qty)
                        getInput()
                    else:
                        os.system('cls')
                        title()
                        getInput()
            if whichType == "s":
                cmd = input(
                    " Enter trade command (ex: 'b 1000 fb 210.5') or (c) to cancel: ")
                if len(cmd.split()) != 4 and cmd != "c":
                    print(" Invalid format, starting over...")
                    getInput()
                if cmd == "c":
                    os.system('cls')
                    title()
                    getInput()
                else:
                    side, qty, symbol, price = cmd.split()
                    if side == "b":
                        printSide = "Buying"
                    if side == "s":
                        printSide = "Selling"

                    confirmTrade = yes_no_dialog(
                    title='Confirm Trade',
                    style=dialog_style,
                    text=f" Confirm {printSide} {qty} shares of {symbol} at {price}").run()

                    if confirmTrade == True:
                        if side == "b":
                            cleanSide = "BUY"
                        else:
                            cleanSide = "SELL"
                        cleanOrderType = "LIMIT"
                        cleanPrice = price

                        # actually place the trade
                        placeLimitTradeShares(
                            cleanOrderType, symbol, cleanSide, cleanPrice, qty)
                        getInput()
                    else:
                        os.system('cls')
                        title()
                        getInput()
            if whichType == "c":
                ######### cancel #############
                os.system('cls')
                title()
                getInput()
            else:
                os.system('cls')
                title()
                print(" Unknown entry...")
                getInput()
        ######### market type ###########
        if type == "m":
            print(Fore.YELLOW + " --- Quantity Options ---")
            whichType = input(
                " Please Select:\n Notional Quantity (n)\n Shares Quantity (s)\n (c) Cancel\n ")
            if whichType == "n":
                print(Fore.YELLOW + " --- Trade Script ---")
                cmd = input(
                    " Enter trade command, use $ notional value (ex: 'b 100000 fb') or (c) to cancel: ")
                if len(cmd.split()) != 3 and cmd != "c":
                    print(" Invalid format, starting over...")
                    getInput()
                if cmd == "c":
                    os.system('cls')
                    title()
                    getInput()
                else:
                    side, qty, symbol = cmd.split()
                    if side == "b":
                        printSide = "Buying"
                    if side == "s":
                        printSide = "Selling"

                    confirmTrade = yes_no_dialog(
                    title='Confirm Trade',
                    style=dialog_style,
                    text=f"Confirm {printSide} {qty} $ worth of {symbol} at the market?").run()
  
                if confirmTrade == True:
                    if side == "b":
                        cleanSide = "BUY"
                    else:
                        cleanSide = "SELL"
                    cleanOrderType = "MARKET"

                    # actually place the trade
                    placeMarketTradeNotional(
                        cleanOrderType, symbol, cleanSide, qty)
                    getInput()
                else:
                    os.system('cls')
                    title()
                    getInput()
                if cmd == "c":
                    os.system('cls')
                    title()
                    getInput()
            if whichType == "s":
                print(Fore.YELLOW + " --- Trade Script ---")
                cmd = input(
                    " Enter trade command (ex: 'b 1000 fb') or (c) to cancel: ")
                if len(cmd.split()) != 3 and cmd != "c":
                    print(" Invalid format, starting over...")
                    getInput()
                if cmd == "c":
                    os.system('cls')
                    title()
                    getInput()
                else:
                    side, qty, symbol = cmd.split()
                    if side == "b":
                        printSide = "Buying"
                    if side == "s":
                        printSide = "Selling"

                    confirmTrade = yes_no_dialog(
                    title='Confirm Trade',
                    style=dialog_style,
                    text=f" Confirm {printSide} {qty} shares of {symbol} at the market").run()
                    
                if confirmTrade == True:
                    if side == "b":
                        cleanSide = "BUY"
                    else:
                        cleanSide = "SELL"
                    cleanOrderType = "MARKET"

                    # actually place the trade
                    placeMarketTradeShares(
                        cleanOrderType, symbol, cleanSide, qty)
                    getInput()
                else:
                    os.system('cls')
                    title()
                    getInput()
                if cmd == "c":
                    os.system('cls')
                    title()
                    getInput()
            if whichType == "c":
                ######### cancel #############
                os.system('cls')
                title()
                getInput()
            else:
                print(" Unknown entry...")
                getInput()
        ######### cancel #############
        if type == "c":
            os.system('cls')
            title()
            getInput()
    ######### view working orders #######
    if prompt == "o":
        getOrders()
    ######### position report ########
    if prompt == "p":
        positionReport()
        getInput()
    ######### quote ########
    if prompt == "q":
        symbol = input(" Please enter symbol: ")
        getQuote(symbol)
    ######### balances report ########
    if prompt == "b":
        balancesReport()
    else:
        os.system('cls')
        print("Unrecognized command. Try again..")
        getInput()


os.system('cls')
initialLoad()
