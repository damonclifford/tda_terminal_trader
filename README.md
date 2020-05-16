# TD Ameritrade Command Line trading terminal (python)

Command Line TD Ameritrade Trading Terminal

This is a command line trading terminal that uses Python and the TD Ameritrade Developer API. From this terminal you can:
- Get Stock Quotes
- Check your day trading buying power
- Place trades (market, limit, stop limit)
- Check your positions
- View working orders

In addition, this terminal will automatically update your API Auth Token on every load, using your Refresh Token stored in an .env file (see usage below).

This terminal allows you to quickly enter and exit trades by using a simple menu and terminal commands. Below are some examples:

To Buy 1000 shares of FB at the market, a simple command of: *'b 1000 fb'*
To Sell $50,000 worth of FB shares at 210, a simple command of: *'s 50000 fb 210'*

A basic menu system is in place to navigate through the program.

**Usage:**

Step 1 - You must first have a TD Ameritrade Developer API account created, and have succesfully obtained a REFRESH TOKEN and a CLIENT ID. Once you have obtained those, update the .env file accordingly with those values in addition to your account id, prior to starting the script.

Step 2 - Start the script using *python OrderTerminal.py* from your favorite command line. An api call will be made to obtain a new authorization token, and a new token.json file will be created which the script will read from on every call. If the auth token is expired, a new one will be fetch.

**Warning**

This is a live application connecting to your live trading account at TD Ameritrade. Use at your own risk and confirm all actions with the TD Ameritrade web trading platform or mobile apps!
