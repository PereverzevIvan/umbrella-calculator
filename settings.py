# Файл с глобальными переменными

#USDT_DATA
BINANCE_USDT_DATA = {}
BYBIT_USDT_DATA = {}
OKEX_USDT_DATA = {}
HUOBI_USDT_DATA = {}

#COINS_DATA
BINANCE_COINS_DATA = {}
BYBIT_COINS_DATA = {}
OKEX_COINS_DATA = {}
HUOBI_COINS_DATA = {}

#USDT
BINANCE_USDT_PRICE = 0
BYBIT_USDT_PRICE = 0
OKEX_USDT_PRICE = 0
HUOBI_USDT_PRICE = 0

#BINANCE
BINANCE_AMOUNT = "100000"
BINANCE_PUB_TYPE = None
BINANCE_TRADE_TYPE = "buy"
BINANCE_PAY_TYPES = "RaiffeisenBank"

#BYBIT
BYBIT_AMOUNT = "100000"
BYBIT_TRADE_TYPE = "1"
BYBIT_PAY_TYPES = "64"
BYBIT_PUB_TYPE = False

#OKX
OKEX_AMOUNT = '100000'
OKEX_TRADE_TYPE = 'sell'
OKEX_PAY_TYPES = "Raiffaizen"
OKEX_PUB_TYPE = "all"

#HUOBI
HUOBI_AMOUNT = '100000'
HUOBI_TRADE_TYPE = "sell"
HUOBI_PAY_TYPES = "36"
HUOBI_PUB_TYPE = False

#Percentage
SPINBOXES = {
    'binance': {
        'spinbox': [-0.3, -0.5, -1],
        'comm_spinbox': [-0.1, -0.1, -0.1]},
    'bybit': {
        'spinbox': [-0.3, -0.5, -1],
        'comm_spinbox': [-0.1, -0.1, -0.1]},
    'okx': {
        'spinbox': [-0.3, -0.5, -1],
        'comm_spinbox': [-0.1, -0.1, -0.1]},
    'huobi': {
        'spinbox': [-0.3, -0.5, -1],
        'comm_spinbox': [-0.1, -0.1, -0.1]}
}

trading_pairs = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SHIBUSDT"]
trading_pairs_binance = ["BTCUSDT", "ETHUSDT"]
trading_pairs_bybit = ['btcusdt', 'ethusdt']
trading_pairs_okx = ["BTC-USDT", "ETH-USDT"]
trading_pairs_huobi = ['btcusdt', 'ethusdt']

keep_running = True

