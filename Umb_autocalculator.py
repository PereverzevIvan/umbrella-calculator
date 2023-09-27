# Это исходный файл, оставшийся после предыдущего разработчика.
# Большая его часть перенесена в "main.py".

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QTabWidget, QDoubleSpinBox, QDockWidget, QCheckBox, QGridLayout
from PyQt5.QtCore import QTimer, Qt, QRect, QPropertyAnimation,QCoreApplication, QPoint
from PyQt5.QtGui import QIntValidator, QFont
import websocket
import json
import threading
import requests
import time
import gzip



#USDT_DATA
usdt_data = {}
usdt_data_bybit = {}
usdt_data_okx = {}
usdt_data_huobi = {}
#COINS_DATA
coins_data = {}
coins_data_bybit = {}
coins_data_okx = {}
coins_data_huobi = {}

#USDT
usdt_price = 0
usdt_price_bybit = 0
usdt_price_okx = 0
usdt_price_huobi = 0
#BINANCE
trans_amount = "100000"
publisherType = None
tradeType = "buy"
payTypes = "TinkoffNew"
#BYBIT
amount = "100000"
side = "1"
payment = "75"
merch = False
#OKX
amount_okx = '100000'
side_okx = 'sell'
payment_okx = "Tinkoff"
merch_okx = "all"
#HUOBI
amount_huobi = '100000'
side_huobi = "sell"
payment_huobi = 28
merch_huobi = False
#Percentage
spinboxes = {
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


keep_running = True

#BINANCE
def connect_to_binance(trading_pairs):
    url = "wss://stream.binance.com:9443/stream?streams="

    streams = []
    for pair in trading_pairs:
        streams.append(f"{pair.lower()}@aggTrade")

    url += "/".join(streams)

    while keep_running:
        try:
            ws = websocket.WebSocketApp(
                url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )
            ws.run_forever()
        except Exception as e:
            print(f"Ошибка при подключении к вебсокетам: {e}")
            print("Повторное подключение через 5 секунд...")
            time.sleep(5)

def on_message(ws, message):
    global usdt_price, spinboxes
    data = json.loads(message)

    if 'data' in data:
        trade_data = data['data']
        symbol = trade_data['s']
        price = float(trade_data['p'])

        if symbol not in coins_data:
            coins_data[symbol] = {}

        coins_data[symbol]['price'] = price

        spinbox = spinboxes['binance']['spinbox']
        comm_spinbox = spinboxes['binance']['comm_spinbox']

        coms = sum([(-comm / 100) for comm in comm_spinbox])
        fees = [0] + [(-spin / 100) + coms for spin in spinbox]

        for index, fee in enumerate(fees):
            coins_data[symbol][f'calculation_{index}'] = price * (1 - fee) * usdt_price



def on_error(ws, error):
    print(f"Ошибка: {error}")

def on_close(ws):
    print("### Веб-сокет закрыт ###")

#BYBIT
def connect_to_bybit():
    bybit_ws_url = 'wss://stream.bybit.com/v5/public/spot'
    while keep_running:
        try:
            ws_bybit = websocket.WebSocketApp(
                bybit_ws_url,
                on_message=on_message_bybit,
                on_error=on_error_bybit,
                on_close=on_close_bybit,
            )
            ws_bybit.on_open = on_open_bybit

            ws_bybit.run_forever()
        except Exception as e:
            print(f"Ошибка при подключении к вебсокетам: {e}")
            print("Повторное подключение через 5 секунд...")
            time.sleep(5)

def on_message_bybit(ws_bybit, message_bybit):
    global usdt_price_bybit,spinboxes
    data = json.loads(message_bybit)

    if 'topic' in data and data['topic'].startswith('tickers'):
        symbol = data['data']['symbol'].lower()  # Переводим в нижний регистр, чтобы соответствовать вашим другим символам
        price = float(data['data']['lastPrice'])


        if symbol not in coins_data_bybit:
            coins_data_bybit[symbol] = {}

        coins_data_bybit[symbol]['price'] = price

        spinbox = spinboxes['bybit']['spinbox']
        comm_spinbox = spinboxes['bybit']['comm_spinbox']

        coms = sum([(-comm / 100) for comm in comm_spinbox])
        fees = [0] + [(-spin / 100) + coms for spin in spinbox]

        for index, fee in enumerate(fees):
            coins_data_bybit[symbol][f'calculation_{index}'] = price * (1 - fee) * usdt_price_bybit


def on_open_bybit(ws_bybit):
    subscribe_message = {
        "op": "subscribe",
        "args": ["tickers.BTCUSDT", "tickers.ETHUSDT"]
    }

    ws_bybit.send(json.dumps(subscribe_message))

def on_error_bybit(ws_bybit, error):
    print(f"Ошибка: {error}")

def on_close_bybit(ws_bybit):
    print("### Веб-сокет закрыт ###")
#OKX
def connect_to_okx(trading_pairs_okx):
    url = "wss://ws.okex.com:8443/ws/v5/public?compress=true"

    # создание списка для подписки на тикеры
    subscriptions = []
    for pair in trading_pairs_okx:
        subscriptions.append({"channel": "tickers", "instId": pair})

    # создание запроса подписки на каналы вебсокета
    request = {
        "op": "subscribe",
        "args": subscriptions
    }

    # преобразование запроса в формат JSON
    json_request = json.dumps(request)

    while keep_running:
        try:
            ws_okx = websocket.WebSocketApp(
                url,
                on_message=on_message_okx,
                on_error=on_error_okx,
                on_close=on_close_okx,
            )

            # отправка запроса подписки на каналы вебсокета
            ws_okx.on_open = lambda _: ws_okx.send(json_request)

            ws_okx.run_forever()

        except Exception as e:
            print(f"Ошибка при подключении к вебсокетам: {e}")
            print("Повторное подключение через 5 секунд...")
            time.sleep(5)

def on_message_okx(ws_okx, message_okx):
    global usdt_price_okx, spinboxes
    data = json.loads(message_okx)

    if 'arg' in data and 'data' in data:
        if data["arg"]["channel"] == "tickers":
            trade_data = data['data'][0]
            symbol = trade_data['instId']
            price = float(trade_data['last'])



            if symbol not in coins_data_okx:
                coins_data_okx[symbol] = {}

            coins_data_okx[symbol]['price'] = price

            spinbox = spinboxes['okx']['spinbox']
            comm_spinbox = spinboxes['okx']['comm_spinbox']

            coms = sum([(-comm / 100) for comm in comm_spinbox])
            fees = [0] + [(-spin / 100) + coms for spin in spinbox]

            for index, fee in enumerate(fees):
                coins_data_okx[symbol][f'calculation_{index}'] = price * (1 - fee) * usdt_price_okx

def on_error_okx(ws_okx, error):
    print(f"Ошибка: {error}")

def on_close_okx(ws_okx):
    print("### Веб-сокет закрыт ###")

#HUOBI
def connect_to_huobi():
    url = "wss://api-aws.huobi.pro/ws"
    while keep_running:
        try:
            ws_huobi = websocket.WebSocketApp(
                url,
                on_message=on_message_huobi,
                on_error=on_error_huobi,
                on_close=on_close_huobi,
            )
            ws_huobi.on_open = on_open_huobi

            ws_huobi.run_forever()
        except Exception as e:
            print(f"Ошибка при подключении к вебсокетам: {e}")
            print("Повторное подключение через 5 секунд...")
            time.sleep(5)

def on_message_huobi(ws_huobi, message_huobi):
    global usdt_price_huobi,spinboxes
    decompressed_data = gzip.decompress(message_huobi).decode()
    data = json.loads(decompressed_data)

    if 'ping' in data:
        ws_huobi.send(json.dumps({"pong": data['ping']}))
    elif 'tick' in data and 'ch' in data:
        trade_data = data['tick']
        symbol = data['ch'].split('.')[1]
        price = float(trade_data['close'])

        if symbol not in coins_data_huobi:
            coins_data_huobi[symbol] = {}

        coins_data_huobi[symbol]['price'] = price
        spinbox = spinboxes['huobi']['spinbox']
        comm_spinbox = spinboxes['huobi']['comm_spinbox']

        coms = sum([(-comm / 100) for comm in comm_spinbox])
        fees = [0] + [(-spin / 100) + coms for spin in spinbox]

        for index, fee in enumerate(fees):
            coins_data_huobi[symbol][f'calculation_{index}'] = price * (1 - fee) * usdt_price_huobi

def on_open_huobi(ws_huobi):
    reqs = [{"sub": f"market.{symbol}.ticker", "id": symbol} for symbol in trading_pairs_huobi]
    for req in reqs:
        ws_huobi.send(json.dumps(req))

def on_error_huobi(ws_huobi, error):
    print(f"Ошибка: {error}")

def on_close_huobi(ws_huobi):
    print("### Веб-сокет закрыт ###")



def update_usdt_price(trans_amount, publisherType, tradeType, payTypes):
    global usdt_price,keep_running, spinboxes, usdt_data
    url = 'https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search'
    headers = {
        'accept': '*/*',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }
    params = {
        "proMerchantAds": False,
        "page": 1,
        "rows": 10,
        "payTypes": [str(payTypes)] if payTypes else None,
        "countries": [],
        "publisherType": str(publisherType) if publisherType else None,
        "asset": "USDT",
        "fiat": "RUB",
        "tradeType": str(tradeType) if tradeType else None,
        "transAmount": str(trans_amount) if trans_amount else None
    }
    while keep_running :
        try:
            response = requests.post(url=url, headers=headers, json=params).json()
            usdt_price = float(response['data'][0]['adv']['price'])
            usdt_data = {}
            spinbox = spinboxes['binance']['spinbox']
            comm_spinbox = spinboxes['binance']['comm_spinbox']

            coms = sum([(-comm / 100) for comm in comm_spinbox[1:]])
            fees = [0] + [(-spin / 100) + coms for spin in spinbox]

            for index, fee in enumerate(fees):
                usdt_data[f'calculation_{index}'] = (1 - fee) * usdt_price

            time.sleep(5)
        except Exception as e:
            print(f"Ошибка при получении цены USDT: {e}")
            time.sleep(5)


def update_usdt_price_bybit(amount,side,payment,merch):
    global usdt_price_bybit, usdt_data_bybit, spinboxes
    url = "https://api2.bybit.com/fiat/otc/item/online"
    headers = {
        'accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }

    params = {"userId": "",
              "tokenId": "USDT",
              "currencyId": "RUB",
              "payment": [payment],
              "side": side,
              "size": "10",
              "page": "1",
              "amount": amount,
              "authMaker": merch,
              "canTrade": False}
    while keep_running:
        try:
            response = requests.post(url=url, headers=headers, json=params).json()
            usdt_price_bybit = float(response['result']['items'][0]['price'])
            usdt_data_bybit = {}
            spinbox = spinboxes['bybit']['spinbox']
            comm_spinbox = spinboxes['bybit']['comm_spinbox']

            coms = sum([(-comm / 100) for comm in comm_spinbox[1:]])
            fees = [0] + [(-spin / 100) + coms for spin in spinbox]

            for index, fee in enumerate(fees):
                usdt_data_bybit[f'calculation_{index}'] = (1 - fee) * usdt_price_bybit
            time.sleep(5)
        except Exception as e:
            time.sleep(5)

def okx(amount_okx,side_okx,payment_okx,merch_okx):
    global usdt_price_okx, usdt_data_okx, spinboxes

    url = "https://www.okx.cab/v3/c2c/tradingOrders/getMarketplaceAdsPrelogin?"
    headers = {
        'accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }

    params = f"t=" \
             f"&side={side_okx}" \
             f"&paymentMethod={payment_okx}" \
             f"&userType={merch_okx}" \
             f"&hideOverseasVerificationAds=False" \
             f"&quoteMinAmountPerOrder={amount_okx}" \
             f"&sortType=" \
             f"&urlId=5" \
             f"&limit=100" \
             f"&cryptoCurrency=usdt" \
             f"&fiatCurrency=rub" \
             f"&currentPage=1" \
             f"&numberPerPage=5"
    while keep_running:
        try:

            response = requests.get(url=url + params, headers=headers).json()

            usdt_price_okx = float(response['data'][side_okx][0]['price'])
            usdt_data_okx = {}
            spinbox = spinboxes['okx']['spinbox']
            comm_spinbox = spinboxes['okx']['comm_spinbox']

            coms = sum([(-comm / 100) for comm in comm_spinbox[1:]])
            fees = [0] + [(-spin / 100) + coms for spin in spinbox]

            for index, fee in enumerate(fees):
                usdt_data_okx[f'calculation_{index}'] = (1 - fee) * usdt_price_okx
            time.sleep(5)
        except Exception as e:
            print(f"Ошибка при получении цены USDT OKX: {e}. Ответ сервера: {response}")
            time.sleep(5)

def huobi(amount_huobi,side_huobi,payment_huobi,merch_huobi):
    global usdt_price_huobi, usdt_data_huobi, spinboxes
    url = "https://otc-api.trygofast.com/v1/data/trade-market?"
    headers = {
        'accept': '*/*',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }
    params = f"coinId=2" \
             "&currency=11" \
             f"&tradeType={side_huobi}" \
             "&currPage=1" \
             f"&payMethod={payment_huobi}" \
             "&acceptOrder=0" \
             "&country=" \
             "&blockType=general" \
             "&online=1" \
             "&range=0" \
             f"&amount={amount_huobi}" \
             "&isThumbsUp=false" \
             f"&isMerchant={merch_huobi}" \
             "&isTraded=false" \
             "&onlyTradable=false" \
             "&isFollowed=false"
    while keep_running:
        try:
            response = requests.get(url=url + params, headers=headers).json()
            usdt_price_huobi = float(response['data'][0]['price'])  # получить цену первого ордера
            usdt_data_huobi = {}
            spinbox = spinboxes['huobi']['spinbox']
            comm_spinbox = spinboxes['huobi']['comm_spinbox']

            coms = sum([(-comm / 100) for comm in comm_spinbox[1:]])
            fees = [0] + [(-spin / 100) + coms for spin in spinbox]

            for index, fee in enumerate(fees):
                usdt_data_huobi[f'calculation_{index}'] = (1 - fee) * usdt_price_huobi
            time.sleep(5)
        except Exception as e:
            print(f"Ошибка при получении цен для USDT HUOBI: {e}")
            time.sleep(5)



trading_pairs = ["BTCUSDT","ETHUSDT","BNBUSDT","SHIBUSDT"]
trading_pairs_binance = ["BTCUSDT","ETHUSDT"]
trading_pairs_bybit = ['btcusdt','ethusdt']
trading_pairs_okx = ["BTC-USDT", "ETH-USDT"]
trading_pairs_huobi = ['btcusdt','ethusdt']


t1 = threading.Thread(target=connect_to_binance, args=(trading_pairs,))

t8 = threading.Thread(target=connect_to_bybit)

t6 = threading.Thread(target=connect_to_okx, args=(trading_pairs_okx,))

t7 = threading.Thread(target=connect_to_huobi)

t2 = threading.Thread(target=update_usdt_price, args=(trans_amount, publisherType, tradeType, payTypes))

t3 = threading.Thread(target=update_usdt_price_bybit, args=(amount, side, payment, merch))

t4 = threading.Thread(target=okx, args=(amount_okx, side_okx, payment_okx, merch_okx))

t5 = threading.Thread(target=huobi, args=(amount_huobi, side_huobi, payment_huobi, merch_huobi))

t1.start()
t2.start()
t3.start()
t4.start()
t5.start()
t6.start()
t7.start()
t8.start()




class CoinInfoApp(QMainWindow):
    def __init__(self):
        super().__init__()



        self.setWindowTitle("UMBRELLA")

        self.mainwidget = QWidget()
        self.setCentralWidget(self.mainwidget)
        self.initUI()
        current_settings = {

            'trans_amount': trans_amount,
            'publisherType': publisherType,
            'tradeType': tradeType,
            'payTypes': payTypes,
            'amount': amount,
            'side': side,
            'payment': payment,
            'merch': merch,
            'amount_okx': amount_okx,
            'side_okx': side_okx,
            'payment_okx': payment_okx,
            'merch_okx': merch_okx,
            'amount_huobi': amount_huobi,
            'side_huobi': side_huobi,
            'payment_huobi': payment_huobi,
            'merch_huobi': merch_huobi,

        }
        widget_dict = {'usdt_label': self.usdt_label,
                       'labels': self.labels,
                       'usdt_label_bybit': self.usdt_label_bybit,
                       'labels_bybit': self.labels_bybit,
                       'usdt_label_okx': self.usdt_label_okx,
                       'labels_okx': self.labels_okx,
                       'usdt_label_huobi': self.usdt_label_huobi,
                       'labels_huobi': self.labels_huobi,
                       'label_exchange': self.label_exchange}
        self.settings_dock = SettingsDock(current_settings,widget_dict)
        self.settings_dock.setParent(self)
        self.settings_dock.hide()




    def initUI(self):
        exchanges = ["BINANCE", "BYBIT", "OKX", "HUOBI"]


        self.settings_button = QPushButton("⋮", self)
        self.settings_button.clicked.connect(self.open_settings_dialog)
        butn = QHBoxLayout()
        butn.addStretch(1)
        butn.addWidget(self.settings_button)

        grid = QGridLayout(self.mainwidget)

        grid.setColumnStretch(0, 1)  # Растягиваем первый столбец
        grid.setColumnStretch(1, 4)
        grid.setColumnStretch(2, 4)
        grid.setColumnStretch(3, 4)
        grid.setColumnStretch(4, 4)
        grid.setColumnStretch(5, 4)

        placeholder_widget = QWidget(self)
        placeholder_widget.setMinimumHeight(1)  # Устанавливаем фиксированную высоту
        grid.addWidget(placeholder_widget, 1, 6)
        grid.setHorizontalSpacing(1)
        self.label_exchange = {}

        for i, exchange in enumerate(exchanges):
            label = QLabel(self)
            label.setText(exchange)
            label.setAlignment(Qt.AlignCenter)

            grid.addWidget(label, i + 1, 0)
            self.label_exchange[exchange] = label
        # Binance

        self.usdt_label = QLabel(self)
        self.usdt_label.setText("USDT BINANCE: ")
        self.usdt_label.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.usdt_label, 1, 1)
        symbol_positions_binance = {
            'BTCUSDT': (1, 2),
            'ETHUSDT': (1, 3),
            'BNBUSDT': (1, 4),
            'SHIBUSDT': (1, 5)
        }
        self.labels = {}
        for symbol, position in symbol_positions_binance.items():
            lbl = QLabel(self)
            lbl.setText(symbol)
            lbl.setAlignment(Qt.AlignCenter)
            grid.addWidget(lbl, position [0], position [1])
            coins_data[symbol] = {}
            coins_data[symbol]['label'] = lbl
            self.labels[symbol] = lbl

        self.usdt_label_bybit = QLabel(self)
        self.usdt_label_bybit.setText("USDT BYBIT: ")
        self.usdt_label_bybit.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.usdt_label_bybit, 2, 1)

        symbol_positions_bybit = {
            'btcusdt': (2, 2),
            'ethusdt': (2, 3)}

        self.labels_bybit = {}
        for symbol, position in symbol_positions_bybit.items():
            lbl_bybit = QLabel(self)
            lbl_bybit.setText(symbol)
            lbl_bybit.setAlignment(Qt.AlignCenter)
            grid.addWidget(lbl_bybit, position [0], position [1])
            coins_data_bybit[symbol] = {}
            coins_data_bybit[symbol]['label_bybit'] = lbl_bybit
            self.labels_bybit[symbol] = lbl_bybit

        self.usdt_label_okx = QLabel(self)
        self.usdt_label_okx.setText("USDT OKX: ")
        self.usdt_label_okx.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.usdt_label_okx, 3, 1)

        symbol_positions_okx = {
            'BTC-USDT': (3, 2),
            'ETH-USDT': (3, 3)}

        self.labels_okx = {}
        for symbol, position in symbol_positions_okx.items():
            lbl_okx = QLabel(self)
            lbl_okx.setText(symbol)
            lbl_okx.setAlignment(Qt.AlignCenter)
            grid.addWidget(lbl_okx, position[0],position[1])
            coins_data_okx[symbol] = {}
            coins_data_okx[symbol]['label_okx'] = lbl_okx
            self.labels_okx[symbol] = lbl_okx

        self.usdt_label_huobi = QLabel(self)
        self.usdt_label_huobi.setText("USDT OKX: ")
        self.usdt_label_huobi.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.usdt_label_huobi, 4, 1)

        symbol_positions_huobi = {
            'btcusdt': (4, 2),
            'ethusdt': (4, 3)}

        self.labels_huobi = {}
        for symbol, position in symbol_positions_huobi.items():
            lbl_huobi = QLabel(self)
            lbl_huobi.setText(symbol)
            lbl_huobi.setAlignment(Qt.AlignCenter)
            grid.addWidget(lbl_huobi, position[0],position[1])
            coins_data_huobi[symbol] = {}
            coins_data_huobi[symbol]['label_huobi'] = lbl_huobi
            self.labels_huobi[symbol] = lbl_huobi

        butn.setAlignment(Qt.AlignTop | Qt.AlignRight)
        grid.addLayout(butn, 0,5)

        self.mainwidget.setLayout(grid)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_labels)
        self.timer.start(1000)  # Update labels every 1000 ms (1 second)
        self.setMinimumSize(1440, 500)






    def update_labels(self):
        global usdt_price, usdt_price_bybit, usdt_price_okx, usdt_price_huobi,usdt_data, spinboxes
        def format_text(symbol, price, calculations, no_decimal, exchange):
            formatted_calcs = []
            for calc in calculations:
                if symbol == 'SHIBUSDT':
                    formatted_calcs.append(f"{calc:,.6f}")
                else:
                    formatted_calcs.append(f"{calc:,.0f}" if no_decimal else f"{calc:,.1f}")
            formatted_spinboxes = [f"{spinbox:.2f}".rstrip('0').rstrip('.') for spinbox in spinboxes[exchange]['spinbox']]
            text = f"{symbol}\nPrice: {price:,.{int(no_decimal)}f}".replace(',', ' ')
            text += f"\t| {formatted_calcs[0]}".replace(',', ' ')
            for i, spinbox in enumerate(formatted_spinboxes, 1):
                text += f"\n{spinbox}%: {formatted_calcs[i]}".replace(',', ' ')
            return text

        calcs = [usdt_data.get(f'calculation_{i}', 0) for i in range(1, 4)]
        calcs_str = '\n'.join(
            f"{int(float(spin)) if float(spin).is_integer() else f'{float(spin):.2f}'.rstrip('0').rstrip('.')}%: {calc:.2f}"
            for spin, calc in zip(spinboxes['binance']['spinbox'], calcs)
        )
        self.usdt_label.setText(f"USDT PRICE: {usdt_price:,.2f}".replace(',', ' ') + "\n" + calcs_str)

        calcs_bybit = [usdt_data_bybit.get(f'calculation_{i}', 0) for i in range(1, 4)]
        calcs_str_bybit = '\n'.join(
            f"{int(float(spin)) if float(spin).is_integer() else f'{float(spin):.2f}'.rstrip('0').rstrip('.')}%: {calc:.2f}"
            for spin, calc in zip(spinboxes['bybit']['spinbox'], calcs_bybit)
        )
        self.usdt_label_bybit.setText(f"USDT PRICE: {usdt_price_bybit:,.2f}".replace(',', ' ') + "\n" + calcs_str_bybit)
        calcs_okx = [usdt_data_okx.get(f'calculation_{i}', 0) for i in range(1, 4)]
        calcs_str_okx = '\n'.join(
            f"{int(float(spin)) if float(spin).is_integer() else f'{float(spin):.2f}'.rstrip('0').rstrip('.')}%: {calc:.2f}"
            for spin, calc in zip(spinboxes['okx']['spinbox'], calcs_okx)
        )
        self.usdt_label_okx.setText(f"USDT PRICE: {usdt_price_okx:,.2f}".replace(',', ' ') + "\n" + calcs_str_okx )

        calcs_huobi = [usdt_data_huobi.get(f'calculation_{i}', 0) for i in range(1, 4)]
        calcs_str_huobi = '\n'.join(
            f"{int(float(spin)) if float(spin).is_integer() else f'{float(spin):.2f}'.rstrip('0').rstrip('.')}%: {calc:.2f}"
            for spin, calc in zip(spinboxes['huobi']['spinbox'], calcs_huobi)
        )
        self.usdt_label_huobi.setText(f"USDT PRICE: {usdt_price_huobi:,.2f}".replace(',', ' ') + "\n" + calcs_str_huobi)


        for symbol, data in coins_data.items():
            price = data.get('price', 0)
            calcs = [data.get(f'calculation_{i}', 0) for i in range(20)]
            no_decimal = symbol == "BTCUSDT"



            data['label'].setText(format_text(symbol, price, calcs[:4], no_decimal, 'binance'))

        for symbol, data in coins_data_bybit.items():

            price = data.get('price', 0)
            calcs = [data.get(f'calculation_{i}', 0) for i in range(4)]
            no_decimal = symbol == "BTCUSDT"
            if 'label_bybit' in data:

                data['label_bybit'].setText(format_text(symbol.upper(), price, calcs, no_decimal, 'bybit'))

        for symbol, data in coins_data_okx.items():
            price = data.get('price', 0)
            calcs = [data.get(f'calculation_{i}', 0) for i in range(4)]
            no_decimal = symbol == "BTCUSDT"

            data['label_okx'].setText(format_text(symbol, price, calcs, no_decimal, 'okx'))

        for symbol in trading_pairs_huobi:
            if symbol in coins_data_huobi:
                data = coins_data_huobi[symbol]
                price = data.get('price', 0)
                calcs = [data.get(f'calculation_{i}', 0) for i in range(4)]
                no_decimal = symbol == "BTCUSDT"


                data['label_huobi'].setText(format_text(symbol.upper(), price, calcs, no_decimal, 'huobi'))

    def open_settings_dialog(self):
        dock_width = 1100
        button_position = self.settings_button.pos()

        # Start geometry is right at the button.
        start_geometry = QRect(button_position.x(), button_position.y(), 0, self.geometry().height())

        # End geometry is dock_width pixels to the left of the button.
        end_geometry = QRect(button_position.x() - dock_width, button_position.y(), dock_width,
                             self.geometry().height())

        self.dock_animation = QPropertyAnimation(self.settings_dock, b'geometry')
        self.dock_animation.setDuration(500)
        self.dock_animation.setStartValue(start_geometry)
        self.dock_animation.setEndValue(end_geometry)

        if self.settings_dock.isVisible():
            self.dock_animation.setDirection(QPropertyAnimation.Backward)
            self.dock_animation.finished.connect(self.hide_dock_widget)
        else:
            self.settings_dock.show()
            self.dock_animation.setDirection(QPropertyAnimation.Forward)
            self.dock_animation.finished.connect(self.ensure_dock_widget_visible)

        self.dock_animation.start()

    def ensure_dock_widget_visible(self):
        self.settings_dock.show()
        self.dock_animation.finished.disconnect()
    def hide_dock_widget(self):
        self.settings_dock.hide()
        self.dock_animation.finished.disconnect()

    def show_dock_widget(self):
        self.settings_dock.show()
        self.dock_animation.finished.disconnect()

    def closeEvent(self, event):

        self.timer.stop()

        global t1, t2, t3, t4, t5, t6, t7, t8
        QCoreApplication.quit()

        t1.close()
        t2.close()
        t3.close()
        t4.close()
        t5.close()
        t6.close()
        t7.close()
        t8.close()
        event.accept()

class SettingsDock(QDockWidget):
    def __init__(self,current_settings,widget_dict,parent = None):
        super().__init__(parent)
        self.current_settings = current_settings
        self.widget_dict = widget_dict
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.setWindowTitle("Settings")


        self.initUI()


    def initUI(self):




        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        # Добавление вкладок

        self.tabs.addTab(self.tab1, "Binance")
        self.tabs.addTab(self.tab2, "Bybit")
        self.tabs.addTab(self.tab3, "Okx")
        self.tabs.addTab(self.tab4, "Huobi")
        # Установка первой вкладки
        self.tab1.setLayout(self.createBinanceLayout())

        # Установка второй вкладки
        self.tab2.setLayout(self.createBybitLayout())

         # Замените на другую функцию для другой биржи
        self.tab3.setLayout(self.createOkxLayout())

        self.tab4.setLayout(self.createHuobiLayout())

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)

        widget = QWidget()
        widget.setLayout(layout)

        apply_button = QPushButton("Применить", self)
        apply_button.clicked.connect(self.apply_settings)
        layout.addWidget(apply_button)
        self.load_settings()

        self.setWidget(widget)

    def load_settings(self):
        #BINANCE
        self.trans_amount_input.setText(str(self.current_settings['trans_amount']))

        index = max(self.publisher_type_combobox.findData(self.current_settings['publisherType']), 0)
        self.publisher_type_combobox.setCurrentIndex(index)
        index = max(self.trade_type_combobox.findData(self.current_settings['tradeType']), 0)
        self.trade_type_combobox.setCurrentIndex(index)
        index = max(self.pay_types_input.findData(self.current_settings['payTypes']), 0)
        self.pay_types_input.setCurrentIndex(index)
        #BYBIT
        self.amount_input.setText(self.current_settings['amount'])
        index = max(self.side_combobox.findData(self.current_settings['side']), 0)
        self.side_combobox.setCurrentIndex(index)
        index = max(self.payment_input.findData(self.current_settings['payment']), 0)
        self.payment_input.setCurrentIndex(index)
        index = max(self.merch_combobox.findData(self.current_settings['merch']), 0)
        self.merch_combobox.setCurrentIndex(index)
        #OKX
        self.amount_okx_input.setText(self.current_settings['amount_okx'])
        index = max(self.side_okx_combobox.findData(self.current_settings['side_okx']), 0)
        self.side_okx_combobox.setCurrentIndex(index)
        index = max(self.payment_okx_input.findData(self.current_settings['payment_okx']), 0)
        self.payment_okx_input.setCurrentIndex(index)
        index = max(self.merch_okx_combobox.findData(self.current_settings['merch_okx']), 0)
        self.merch_okx_combobox.setCurrentIndex(index)
        #HUOBI
        self.amount_huobi_input.setText(self.current_settings['amount_huobi'])
        index = max(self.side_huobi_combobox.findData(self.current_settings['side_huobi']), 0)
        self.side_huobi_combobox.setCurrentIndex(index)
        index = max(self.payment_huobi_input.findData(self.current_settings['payment_huobi']), 0)
        self.payment_huobi_input.setCurrentIndex(index)
        index = max(self.merch_huobi_combobox.findData(self.current_settings['merch_huobi']), 0)
        self.merch_huobi_combobox.setCurrentIndex(index)
    #BINANCE
    def createBinanceLayout(self):
        self.spinbox1_binance = QDoubleSpinBox()
        self.spinbox2_binance = QDoubleSpinBox()
        self.spinbox3_binance = QDoubleSpinBox()
        self.comm_spinbox1_binance = QDoubleSpinBox()
        self.comm_spinbox2_binance = QDoubleSpinBox()
        self.comm_spinbox3_binance = QDoubleSpinBox()
        hbox = QHBoxLayout()
        vbox = QVBoxLayout()
        hbox_settings = QHBoxLayout()

        self.binance_checkbox = QCheckBox("Binance", self)
        self.binance_checkbox.setChecked(True)
        self.binance_checkbox.stateChanged.connect(self.binance_checkbox_changed)
        hbox_settings.addWidget(self.binance_checkbox)

        self.usdt_binance_checkbox = QCheckBox("USDT", self)
        self.usdt_binance_checkbox.setChecked(True)
        self.usdt_binance_checkbox.stateChanged.connect(self.usdt_binance_check)
        hbox_settings.addWidget(self.usdt_binance_checkbox)

        self.btcusdt_binance_checkbox = QCheckBox("BTC", self)
        self.btcusdt_binance_checkbox.setChecked(True)
        self.btcusdt_binance_checkbox.stateChanged.connect(self.btc_binance_checkbox_changed)
        hbox_settings.addWidget(self.btcusdt_binance_checkbox)

        self.ethusdt_binance_checkbox = QCheckBox("ETH", self)
        self.ethusdt_binance_checkbox.setChecked(True)
        self.ethusdt_binance_checkbox.stateChanged.connect(self.eth_binance_checkbox_changed)
        hbox_settings.addWidget(self.ethusdt_binance_checkbox)

        self.bnbusdt_binance_checkbox = QCheckBox("BNB", self)
        self.bnbusdt_binance_checkbox.setChecked(True)
        self.bnbusdt_binance_checkbox.stateChanged.connect(self.bnb_checkbox_changed)
        hbox_settings.addWidget(self.bnbusdt_binance_checkbox)

        self.shibusdt_binance_checkbox = QCheckBox("SHIB", self)
        self.shibusdt_binance_checkbox.setChecked(True)
        self.shibusdt_binance_checkbox.stateChanged.connect(self.shib_checkbox_changed)
        hbox_settings.addWidget(self.shibusdt_binance_checkbox)

        vbox.addLayout(hbox_settings)
        # Сумма
        trans_amount_label = QLabel("Сумма:", self)
        vbox.addWidget(trans_amount_label)

        trans_amount_input = QLineEdit(self)
        validator = QIntValidator(0, 10000000)
        trans_amount_input.setValidator(validator)
        vbox.addWidget(trans_amount_input)
        self.trans_amount_input = trans_amount_input

        # publisherType
        publisher_type_label = QLabel("Тип публикатора:", self)
        vbox.addWidget(publisher_type_label)

        publisher_type_combobox = QComboBox(self)
        publisher_type_combobox.addItem("Мерчант")
        publisher_type_combobox.setItemData(publisher_type_combobox.findText('Мерчант'), 'merchant', role=Qt.UserRole)
        publisher_type_combobox.addItem('Все')
        publisher_type_combobox.setItemData(publisher_type_combobox.findText('Все'), None, role=Qt.UserRole)
        vbox.addWidget(publisher_type_combobox)
        self.publisher_type_combobox = publisher_type_combobox

        # tradeType
        trade_type_label = QLabel("Тип сделки:", self)
        vbox.addWidget(trade_type_label)

        trade_type_combobox = QComboBox(self)
        trade_type_combobox.addItem("Покупка")
        trade_type_combobox.setItemData(trade_type_combobox.findText('Покупка'), 'buy', role=Qt.UserRole)
        trade_type_combobox.addItem("Продажа")
        trade_type_combobox.setItemData(trade_type_combobox.findText('Продажа'), 'sell', role=Qt.UserRole)
        vbox.addWidget(trade_type_combobox)
        self.trade_type_combobox = trade_type_combobox

        # payTypes
        pay_types_label = QLabel("Способы оплаты:", self)
        vbox.addWidget(pay_types_label)

        pay_types_input = QComboBox(self)
        pay_types_input.addItem("Тинькофф")
        pay_types_input.setItemData(pay_types_input.findText('Тинькофф'), 'TinkoffNew', role=Qt.UserRole)
        pay_types_input.addItem("Сбербанк")
        pay_types_input.setItemData(pay_types_input.findText('Сбербанк'), 'RosBankNew', role=Qt.UserRole)
        pay_types_input.addItem("Райффайзен")
        pay_types_input.setItemData(pay_types_input.findText('Райффайзен'), 'RaiffeisenBank', role=Qt.UserRole)
        vbox.addWidget(pay_types_input)
        self.pay_types_input = pay_types_input

        hbox.addLayout(vbox)

        vbox_spin = QVBoxLayout()

        spinbox1_label = QLabel(self)
        spinbox1_label.setText('Первые вычисления')
        spinbox1_label.setAlignment(Qt.AlignLeft)
        vbox_spin.addWidget(spinbox1_label)
        self.spinbox1_binance.setDecimals(2)
        self.spinbox1_binance.setMinimum(-100)
        self.spinbox1_binance.setMaximum(100)
        self.spinbox1_binance.setValue(-0.3)
        self.spinbox1_binance.setSingleStep(0.05)
        vbox_spin.addWidget(self.spinbox1_binance)

        spinbox2_label = QLabel(self)
        spinbox2_label.setText('Вторые вычисления')
        spinbox2_label.setAlignment(Qt.AlignLeft)
        vbox_spin.addWidget(spinbox2_label)
        self.spinbox2_binance.setDecimals(2)
        self.spinbox2_binance.setMinimum(-100)
        self.spinbox2_binance.setMaximum(100)
        self.spinbox2_binance.setValue(-0.5)
        self.spinbox2_binance.setSingleStep(0.05)
        vbox_spin.addWidget(self.spinbox2_binance)

        spinbox3_label = QLabel(self)
        spinbox3_label.setText('Третьи вычисления')
        spinbox3_label.setAlignment(Qt.AlignLeft)
        vbox_spin.addWidget(spinbox3_label)
        self.spinbox3_binance.setDecimals(2)
        self.spinbox3_binance.setMinimum(-100)
        self.spinbox3_binance.setMaximum(100)
        self.spinbox3_binance.setValue(-1.0)
        self.spinbox3_binance.setSingleStep(0.05)
        vbox_spin.addWidget(self.spinbox3_binance)


        hbox.addLayout(vbox_spin)

        vbox_comm = QVBoxLayout()
        # Для первого QDoubleSpinBox

        comm_label1 = QLabel(self)
        comm_label1.setText('Комиссия спота:')
        self.comm_spinbox1_binance.setDecimals(2)
        self.comm_spinbox1_binance.setMinimum(-100)
        self.comm_spinbox1_binance.setMaximum(100)
        self.comm_spinbox1_binance.setValue(-0.1)
        self.comm_spinbox1_binance.setSingleStep(0.05)

        vbox_comm.addWidget(comm_label1)
        vbox_comm.addWidget(self.comm_spinbox1_binance)

        # Для второго QDoubleSpinBox
        comm_label2 = QLabel(self)
        comm_label2.setText('Комиссия за покупку:')
        self.comm_spinbox2_binance.setDecimals(2)
        self.comm_spinbox2_binance.setMinimum(-100)
        self.comm_spinbox2_binance.setMaximum(100)
        self.comm_spinbox2_binance.setValue(-0.1)
        self.comm_spinbox2_binance.setSingleStep(0.05)

        vbox_comm.addWidget(comm_label2)
        vbox_comm.addWidget(self.comm_spinbox2_binance)

        comm_label3 = QLabel(self)
        comm_label3.setText('Комиссия за продажу:')
        self.comm_spinbox3_binance.setDecimals(2)
        self.comm_spinbox3_binance.setMinimum(-100)
        self.comm_spinbox3_binance.setMaximum(100)
        self.comm_spinbox3_binance.setValue(-0.1)
        self.comm_spinbox3_binance.setSingleStep(0.05)

        vbox_comm.addWidget(comm_label3)
        vbox_comm.addWidget(self.comm_spinbox3_binance)
        self.spinbox1_binance.valueChanged.connect(self.update_spinboxs)
        self.spinbox2_binance.valueChanged.connect(self.update_spinboxs)
        self.spinbox3_binance.valueChanged.connect(self.update_spinboxs)
        self.comm_spinbox1_binance.valueChanged.connect(self.update_spinboxs)
        self.comm_spinbox2_binance.valueChanged.connect(self.update_spinboxs)
        self.comm_spinbox3_binance.valueChanged.connect(self.update_spinboxs)

        hbox.addLayout(vbox_comm)






        return hbox

    def binance_checkbox_changed(self, state):
        is_checked = state == Qt.Checked
        self.usdt_binance_checkbox.setChecked(is_checked)
        self.btcusdt_binance_checkbox.setChecked(is_checked)
        self.ethusdt_binance_checkbox.setChecked(is_checked)
        self.bnbusdt_binance_checkbox.setChecked(is_checked)
        self.shibusdt_binance_checkbox.setChecked(is_checked)

    def usdt_binance_check(self,state):
        is_checked = state == Qt.Checked
        self.widget_dict['usdt_label'].setVisible(is_checked)
        self.update_binance_checkbox_state()
        self.update_binance_checkbox_state1()


    def btc_binance_checkbox_changed(self,state):
        is_checked = state == Qt.Checked
        self.widget_dict['labels']['BTCUSDT'].setVisible(is_checked)
        self.update_binance_checkbox_state()
        self.update_binance_checkbox_state1()
    def eth_binance_checkbox_changed(self,state):
        is_checked = state == Qt.Checked
        self.widget_dict['labels']['ETHUSDT'].setVisible(is_checked)
        self.update_binance_checkbox_state()
        self.update_binance_checkbox_state1()
    def bnb_checkbox_changed(self,state):
        is_checked = state == Qt.Checked
        self.widget_dict['labels']['BNBUSDT'].setVisible(is_checked)
        self.update_binance_checkbox_state()
        self.update_binance_checkbox_state1()

    def shib_checkbox_changed(self,state):
        is_checked = state == Qt.Checked
        self.widget_dict['labels']['SHIBUSDT'].setVisible(is_checked)
        self.update_binance_checkbox_state()
        self.update_binance_checkbox_state1()

    def update_binance_checkbox_state(self):
        is_all_checked = (self.usdt_binance_checkbox.isChecked() and
                          self.btcusdt_binance_checkbox.isChecked() and
                          self.ethusdt_binance_checkbox.isChecked() and
                          self.bnbusdt_binance_checkbox.isChecked() and
                          self.shibusdt_binance_checkbox.isChecked())
        is_all_unchecked = (not self.usdt_binance_checkbox.isChecked() and
                            not self.btcusdt_binance_checkbox.isChecked() and
                            not self.ethusdt_binance_checkbox.isChecked() and
                            not self.bnbusdt_binance_checkbox.isChecked() and
                            not self.shibusdt_binance_checkbox.isChecked())
        if is_all_checked or is_all_unchecked:

            self.binance_checkbox.setChecked(is_all_checked)


    def update_binance_checkbox_state1(self):
        if any([self.usdt_binance_checkbox.isChecked(),
                self.btcusdt_binance_checkbox.isChecked(),
                self.ethusdt_binance_checkbox.isChecked(),
                self.bnbusdt_binance_checkbox.isChecked()]):
            self.widget_dict['label_exchange']['BINANCE'].setVisible(True)
        else:
            self.widget_dict['label_exchange']['BINANCE'].setVisible(False)

    # BYBIT
    def createBybitLayout(self):
        hbox_total = QHBoxLayout()

        vbox_bybit = QVBoxLayout()

        hbox_settings = QHBoxLayout()

        self.bybit_checkbox = QCheckBox("Bybit", self)
        self.bybit_checkbox.setChecked(True)
        self.bybit_checkbox.stateChanged.connect(self.bybit_checkbox_changed)
        hbox_settings.addWidget(self.bybit_checkbox)

        self.usdt_bybit_checkbox = QCheckBox("USDT", self)
        self.usdt_bybit_checkbox.setChecked(True)
        self.usdt_bybit_checkbox.stateChanged.connect(self.usdt_bybit_check)
        hbox_settings.addWidget(self.usdt_bybit_checkbox)

        self.btcusdt_bybit_checkbox = QCheckBox("BTC", self)
        self.btcusdt_bybit_checkbox.setChecked(True)
        self.btcusdt_bybit_checkbox.stateChanged.connect(self.btc_bybit_check)
        hbox_settings.addWidget(self.btcusdt_bybit_checkbox)

        self.ethusdt_bybit_checkbox = QCheckBox("ETH", self)
        self.ethusdt_bybit_checkbox.setChecked(True)
        self.ethusdt_bybit_checkbox.stateChanged.connect(self.eth_bybit_check)
        hbox_settings.addWidget(self.ethusdt_bybit_checkbox)


        vbox_bybit.addLayout(hbox_settings)
        # Сумма
        amount_label = QLabel("Сумма:", self)
        vbox_bybit.addWidget(amount_label)

        amount_input = QLineEdit(self)
        validator = QIntValidator(0, 10000000)
        amount_input.setValidator(validator)
        vbox_bybit.addWidget(amount_input)
        self.amount_input = amount_input

        # publisherType
        merch_label = QLabel("Тип публикатора:", self)
        vbox_bybit.addWidget(merch_label)

        merch_combobox = QComboBox(self)
        merch_combobox.addItem('Мерчант')
        merch_combobox.setItemData(merch_combobox.findText("Мерчант"), True, role=Qt.UserRole)
        merch_combobox.addItem('Все')
        merch_combobox.setItemData(merch_combobox.findText("Все"), False, role=Qt.UserRole)
        vbox_bybit.addWidget(merch_combobox)
        self.merch_combobox = merch_combobox

        # tradeType
        side_label = QLabel("Тип сделки:", self)
        vbox_bybit.addWidget(side_label)

        side_combobox = QComboBox(self)
        side_combobox.addItem("Покупка")  # Покупка
        side_combobox.setItemData(side_combobox.findText("Покупка"), "1", role=Qt.UserRole)
        side_combobox.addItem("Продажа")  # Продажа
        side_combobox.setItemData(side_combobox.findText("Продажа"), "0", role=Qt.UserRole)
        vbox_bybit.addWidget(side_combobox)
        self.side_combobox = side_combobox

        # payTypes
        payment_label = QLabel("Способы оплаты:", self)
        vbox_bybit.addWidget(payment_label)

        payment_input = QComboBox(self)
        payment_input.addItem('Тинькофф')
        payment_input.setItemData(payment_input.findText("Тинькофф"), "75", role=Qt.UserRole)
        payment_input.addItem('Сбербанк')
        payment_input.setItemData(payment_input.findText("Сбербанк"), "185", role=Qt.UserRole)
        payment_input.addItem('Райффайзен')
        payment_input.setItemData(payment_input.findText("Райффайзен"), "64", role=Qt.UserRole)
        vbox_bybit.addWidget(payment_input)
        self.payment_input = payment_input



        vbox_xyz = QVBoxLayout()
        self.spinbox1_bybit = QDoubleSpinBox()
        self.spinbox2_bybit = QDoubleSpinBox()
        self.spinbox3_bybit = QDoubleSpinBox()
        self.comm_spinbox1_bybit = QDoubleSpinBox()
        self.comm_spinbox2_bybit = QDoubleSpinBox()
        self.comm_spinbox3_bybit = QDoubleSpinBox()



        # Создаем три QDoubleSpinBox и устанавливаем начальные значения
        spinbox1_label = QLabel(self)
        spinbox1_label.setText('Первые вычисления')
        spinbox1_label.setAlignment(Qt.AlignLeft)
        vbox_xyz.addWidget(spinbox1_label)
        self.spinbox1_bybit.setDecimals(2)
        self.spinbox1_bybit.setMinimum(-100)
        self.spinbox1_bybit.setMaximum(100)
        self.spinbox1_bybit.setValue(-0.3)
        self.spinbox1_bybit.setSingleStep(0.05)
        vbox_xyz.addWidget(self.spinbox1_bybit)

        spinbox2_label = QLabel(self)
        spinbox2_label.setText('Вторые вычисления')
        spinbox2_label.setAlignment(Qt.AlignLeft)
        vbox_xyz.addWidget(spinbox2_label)
        self.spinbox2_bybit.setDecimals(2)
        self.spinbox2_bybit.setMinimum(-100)
        self.spinbox2_bybit.setMaximum(100)
        self.spinbox2_bybit.setValue(-0.5)
        self.spinbox2_bybit.setSingleStep(0.05)
        vbox_xyz.addWidget(self.spinbox2_bybit)

        spinbox3_label = QLabel(self)
        spinbox3_label.setText('Третьи вычисления')
        spinbox3_label.setAlignment(Qt.AlignLeft)
        vbox_xyz.addWidget(spinbox3_label)
        self.spinbox3_bybit.setDecimals(2)
        self.spinbox3_bybit.setMinimum(-100)
        self.spinbox3_bybit.setMaximum(100)
        self.spinbox3_bybit.setValue(-1.0)
        self.spinbox3_bybit.setSingleStep(0.05)

        vbox_xyz.addWidget(self.spinbox3_bybit)



        vbox_comm = QVBoxLayout()

        # Для первого QDoubleSpinBox
        comm_label1 = QLabel(self)
        comm_label1.setText('Комиссия спота:')
        self.comm_spinbox1_bybit.setDecimals(2)
        self.comm_spinbox1_bybit.setMinimum(-100)
        self.comm_spinbox1_bybit.setMaximum(100)
        self.comm_spinbox1_bybit.setValue(-0.1)
        self.comm_spinbox1_bybit.setSingleStep(0.05)

        vbox_comm.addWidget(comm_label1)
        vbox_comm.addWidget(self.comm_spinbox1_bybit)

        # Для второго QDoubleSpinBox
        comm_label2 = QLabel(self)
        comm_label2.setText('Комиссия за покупку:')
        self.comm_spinbox2_bybit.setDecimals(2)
        self.comm_spinbox2_bybit.setMinimum(-100)
        self.comm_spinbox2_bybit.setMaximum(100)
        self.comm_spinbox2_bybit.setValue(-0.1)
        self.comm_spinbox2_bybit.setSingleStep(0.05)

        vbox_comm.addWidget(comm_label2)
        vbox_comm.addWidget(self.comm_spinbox2_bybit)

        comm_label3 = QLabel(self)
        comm_label3.setText('Комиссия за продажу:')
        self.comm_spinbox3_bybit.setDecimals(2)
        self.comm_spinbox3_bybit.setMinimum(-100)
        self.comm_spinbox3_bybit.setMaximum(100)
        self.comm_spinbox3_bybit.setValue(-0.1)
        self.comm_spinbox3_bybit.setSingleStep(0.05)


        vbox_comm.addWidget(comm_label3)
        vbox_comm.addWidget(self.comm_spinbox3_bybit)






        hbox_total.addLayout(vbox_bybit)
        hbox_total.addLayout(vbox_xyz)
        hbox_total.addLayout(vbox_comm)

        self.spinbox1_bybit.valueChanged.connect(self.update_spinboxs)
        self.spinbox2_bybit.valueChanged.connect(self.update_spinboxs)
        self.spinbox3_bybit.valueChanged.connect(self.update_spinboxs)
        self.comm_spinbox1_bybit.valueChanged.connect(self.update_spinboxs)
        self.comm_spinbox2_bybit.valueChanged.connect(self.update_spinboxs)
        self.comm_spinbox3_bybit.valueChanged.connect(self.update_spinboxs)



        return hbox_total

    def bybit_checkbox_changed(self, state):
        is_checked = state == Qt.Checked
        self.usdt_bybit_checkbox.setChecked(is_checked)
        self.btcusdt_bybit_checkbox.setChecked(is_checked)
        self.ethusdt_bybit_checkbox.setChecked(is_checked)
        self.widget_dict['label_exchange']['BYBIT'].setVisible(is_checked)

    def usdt_bybit_check(self,state):
        is_checked = state == Qt.Checked
        self.widget_dict['usdt_label_bybit'].setVisible(is_checked)
        self.update_bybit_checkbox_state()
        self.update_bybit_checkbox_state1()
    def btc_bybit_check(self,state):
        is_checked = state == Qt.Checked
        self.widget_dict['labels_bybit']['btcusdt'].setVisible(is_checked)
        self.update_bybit_checkbox_state()
        self.update_bybit_checkbox_state1()

    def eth_bybit_check(self,state):
        is_checked = state == Qt.Checked
        self.widget_dict['labels_bybit']['ethusdt'].setVisible(is_checked)
        self.update_bybit_checkbox_state()
        self.update_bybit_checkbox_state1()

    def update_bybit_checkbox_state(self):
        is_all_checked = (self.usdt_bybit_checkbox.isChecked() and
                          self.btcusdt_bybit_checkbox.isChecked() and
                          self.ethusdt_bybit_checkbox.isChecked())
        is_all_unchecked = (not self.usdt_bybit_checkbox.isChecked() and
                            not self.btcusdt_bybit_checkbox.isChecked() and
                            not self.ethusdt_bybit_checkbox.isChecked())
        if is_all_checked or is_all_unchecked:
            self.bybit_checkbox.setChecked(is_all_checked)
    def update_bybit_checkbox_state1(self):
        if any([self.usdt_bybit_checkbox.isChecked(),
                self.btcusdt_bybit_checkbox.isChecked(),
                self.ethusdt_bybit_checkbox.isChecked()]):
            self.widget_dict['label_exchange']['BYBIT'].setVisible(True)
        else:
            self.widget_dict['label_exchange']['BYBIT'].setVisible(False)
    #OKX
    def createOkxLayout(self):
        self.spinbox1_okx = QDoubleSpinBox()
        self.spinbox2_okx = QDoubleSpinBox()
        self.spinbox3_okx = QDoubleSpinBox()
        self.comm_spinbox1_okx = QDoubleSpinBox()
        self.comm_spinbox2_okx = QDoubleSpinBox()
        self.comm_spinbox3_okx = QDoubleSpinBox()
        hbox = QHBoxLayout()

        vbox_okx = QVBoxLayout()
        hbox_settings = QHBoxLayout()
        self.okx_checkbox = QCheckBox("Okx", self)
        self.okx_checkbox.setChecked(True)
        self.okx_checkbox.stateChanged.connect(self.okx_checkbox_changed)
        hbox_settings.addWidget(self.okx_checkbox)

        self.usdt_okx_checkbox = QCheckBox("USDT", self)
        self.usdt_okx_checkbox.setChecked(True)
        self.usdt_okx_checkbox.stateChanged.connect(self.usdt_okx_check)
        hbox_settings.addWidget(self.usdt_okx_checkbox)

        self.btcusdt_okx_checkbox = QCheckBox("BTC", self)
        self.btcusdt_okx_checkbox.setChecked(True)
        self.btcusdt_okx_checkbox.stateChanged.connect(self.btc_okx_check)
        hbox_settings.addWidget(self.btcusdt_okx_checkbox)

        self.ethusdt_okx_checkbox = QCheckBox("ETH", self)
        self.ethusdt_okx_checkbox.setChecked(True)
        self.ethusdt_okx_checkbox.stateChanged.connect(self.eth_okx_check)
        hbox_settings.addWidget(self.ethusdt_okx_checkbox)

        vbox_okx.addLayout(hbox_settings)

        amount_okx_label = QLabel("Сумма:", self)
        vbox_okx.addWidget(amount_okx_label)

        amount_okx_input = QLineEdit(self)
        validator = QIntValidator(0, 10000000)
        amount_okx_input.setValidator(validator)
        vbox_okx.addWidget(amount_okx_input)
        self.amount_okx_input = amount_okx_input

        # publisherType
        merch_okx_label = QLabel("Тип публикатора:", self)
        vbox_okx.addWidget(merch_okx_label)

        merch_okx_combobox = QComboBox(self)
        merch_okx_combobox.addItem("Мерчант")
        merch_okx_combobox.setItemData(merch_okx_combobox.findText("Мерчант"), "certified", role=Qt.UserRole)
        merch_okx_combobox.addItem("Все")
        merch_okx_combobox.setItemData(merch_okx_combobox.findText("Все"), "all", role=Qt.UserRole)
        vbox_okx.addWidget(merch_okx_combobox)
        self.merch_okx_combobox = merch_okx_combobox

        # tradeType
        side_okx_label = QLabel("Тип сделки:", self)
        vbox_okx.addWidget(side_okx_label)

        side_okx_combobox = QComboBox(self)
        side_okx_combobox.addItem("Покупка")
        side_okx_combobox.setItemData(side_okx_combobox.findText("Покупка"), "sell", role=Qt.UserRole)
        side_okx_combobox.addItem("Продажа")
        side_okx_combobox.setItemData(side_okx_combobox.findText("Продажа"), "buy", role=Qt.UserRole)
        vbox_okx.addWidget(side_okx_combobox)
        self.side_okx_combobox = side_okx_combobox

        # payTypes
        payment_okx_label = QLabel("Способы оплаты:", self)
        vbox_okx.addWidget(payment_okx_label)

        payment_okx_input = QComboBox(self)
        payment_okx_input.addItem("Тинькофф")
        payment_okx_input.setItemData(payment_okx_input.findText("Тинькофф"), "Tinkoff", role=Qt.UserRole)
        payment_okx_input.addItem("Сбербанк")
        payment_okx_input.setItemData(payment_okx_input.findText("Сбербанк"), "Sberbank", role=Qt.UserRole)
        payment_okx_input.addItem("Райффайзен")
        payment_okx_input.setItemData(payment_okx_input.findText("Райффайзен"), "Raiffaizen", role=Qt.UserRole)
        vbox_okx.addWidget(payment_okx_input)
        self.payment_okx_input = payment_okx_input

        hbox.addLayout(vbox_okx)

        vbox_spin = QVBoxLayout()

        spinbox1_label = QLabel(self)
        spinbox1_label.setText('Первые вычисления')
        spinbox1_label.setAlignment(Qt.AlignLeft)
        vbox_spin.addWidget(spinbox1_label)
        self.spinbox1_okx.setDecimals(2)
        self.spinbox1_okx.setMinimum(-100)
        self.spinbox1_okx.setMaximum(100)
        self.spinbox1_okx.setValue(-0.3)
        self.spinbox1_okx.setSingleStep(0.05)
        vbox_spin.addWidget(self.spinbox1_okx)

        spinbox2_label = QLabel(self)
        spinbox2_label.setText('Вторые вычисления')
        spinbox2_label.setAlignment(Qt.AlignLeft)
        vbox_spin.addWidget(spinbox2_label)
        self.spinbox2_okx.setDecimals(2)
        self.spinbox2_okx.setMinimum(-100)
        self.spinbox2_okx.setMaximum(100)
        self.spinbox2_okx.setValue(-0.5)
        self.spinbox2_okx.setSingleStep(0.05)
        vbox_spin.addWidget(self.spinbox2_okx)

        spinbox3_label = QLabel(self)
        spinbox3_label.setText('Третьи вычисления')
        spinbox3_label.setAlignment(Qt.AlignLeft)
        vbox_spin.addWidget(spinbox3_label)
        self.spinbox3_okx.setDecimals(2)
        self.spinbox3_okx.setMinimum(-100)
        self.spinbox3_okx.setMaximum(100)
        self.spinbox3_okx.setValue(-1.0)
        self.spinbox3_okx.setSingleStep(0.05)
        vbox_spin.addWidget(self.spinbox3_okx)


        hbox.addLayout(vbox_spin)

        vbox_comm = QVBoxLayout()

        # Для первого QDoubleSpinBox
        comm_label1 = QLabel(self)
        comm_label1.setText('Комиссия спота:')
        self.comm_spinbox1_okx.setDecimals(2)
        self.comm_spinbox1_okx.setMinimum(-100)
        self.comm_spinbox1_okx.setMaximum(100)
        self.comm_spinbox1_okx.setValue(-0.1)
        self.comm_spinbox1_okx.setSingleStep(0.05)

        vbox_comm.addWidget(comm_label1)
        vbox_comm.addWidget(self.comm_spinbox1_okx)

        # Для второго QDoubleSpinBox
        comm_label2 = QLabel(self)
        comm_label2.setText('Комиссия за покупку:')
        self.comm_spinbox2_okx.setDecimals(2)
        self.comm_spinbox2_okx.setMinimum(-100)
        self.comm_spinbox2_okx.setMaximum(100)
        self.comm_spinbox2_okx.setValue(-0.1)
        self.comm_spinbox2_okx.setSingleStep(0.05)

        vbox_comm.addWidget(comm_label2)
        vbox_comm.addWidget(self.comm_spinbox2_okx)

        comm_label3 = QLabel(self)
        comm_label3.setText('Комиссия за продажу:')
        self.comm_spinbox3_okx.setDecimals(2)
        self.comm_spinbox3_okx.setMinimum(-100)
        self.comm_spinbox3_okx.setMaximum(100)
        self.comm_spinbox3_okx.setValue(-0.1)
        self.comm_spinbox3_okx.setSingleStep(0.05)

        vbox_comm.addWidget(comm_label3)
        vbox_comm.addWidget(self.comm_spinbox3_okx)

        self.spinbox1_okx.valueChanged.connect(self.update_spinboxs)
        self.spinbox2_okx.valueChanged.connect(self.update_spinboxs)
        self.spinbox3_okx.valueChanged.connect(self.update_spinboxs)
        self.comm_spinbox1_okx.valueChanged.connect(self.update_spinboxs)
        self.comm_spinbox2_okx.valueChanged.connect(self.update_spinboxs)
        self.comm_spinbox3_okx.valueChanged.connect(self.update_spinboxs)

        hbox.addLayout(vbox_comm)






        return hbox

    def okx_checkbox_changed(self, state):
        is_checked = state == Qt.Checked
        self.usdt_okx_checkbox.setChecked(is_checked)
        self.btcusdt_okx_checkbox.setChecked(is_checked)
        self.ethusdt_okx_checkbox.setChecked(is_checked)
        self.widget_dict['label_exchange']['OKX'].setVisible(is_checked)
    def usdt_okx_check(self,state):
        is_checked = state == Qt.Checked
        self.widget_dict['usdt_label_okx'].setVisible(is_checked)
        self.update_okx_checkbox_state()
        self.update_okx_checkbox_state1()
    def btc_okx_check(self,state):
        is_checked = state == Qt.Checked
        self.widget_dict['labels_okx']['BTC-USDT'].setVisible(is_checked)
        self.update_okx_checkbox_state()
        self.update_okx_checkbox_state1()

    def eth_okx_check(self,state):
        is_checked = state == Qt.Checked
        self.widget_dict['labels_okx']['ETH-USDT'].setVisible(is_checked)
        self.update_okx_checkbox_state()
        self.update_okx_checkbox_state1()
    def update_okx_checkbox_state(self):
        is_all_checked = (self.usdt_okx_checkbox.isChecked() and
                          self.btcusdt_okx_checkbox.isChecked() and
                          self.ethusdt_okx_checkbox.isChecked())
        is_all_unchecked = (not self.usdt_okx_checkbox.isChecked() and
                            not self.btcusdt_okx_checkbox.isChecked() and
                            not self.ethusdt_okx_checkbox.isChecked())
        if is_all_checked or is_all_unchecked:
            self.okx_checkbox.setChecked(is_all_checked)


    def update_okx_checkbox_state1(self):
        if any([self.usdt_okx_checkbox.isChecked(),
                self.btcusdt_okx_checkbox.isChecked(),
                self.ethusdt_okx_checkbox.isChecked()]):
            self.widget_dict['label_exchange']['OKX'].setVisible(True)
        else:
            self.widget_dict['label_exchange']['OKX'].setVisible(False)

    #HUOBI
    def createHuobiLayout(self):
        self.spinbox1_huobi = QDoubleSpinBox()
        self.spinbox2_huobi = QDoubleSpinBox()
        self.spinbox3_huobi = QDoubleSpinBox()
        self.comm_spinbox1_huobi = QDoubleSpinBox()
        self.comm_spinbox2_huobi = QDoubleSpinBox()
        self.comm_spinbox3_huobi = QDoubleSpinBox()
        hbox = QHBoxLayout()

        vbox_huobi = QVBoxLayout()

        hbox_settings = QHBoxLayout()

        self.huobi_checkbox = QCheckBox("Huobi", self)
        self.huobi_checkbox.setChecked(True)
        self.huobi_checkbox.stateChanged.connect(self.huobi_checkbox_changed)
        hbox_settings.addWidget(self.huobi_checkbox)

        self.usdt_huobi_checkbox = QCheckBox("USDT", self)
        self.usdt_huobi_checkbox.setChecked(True)
        self.usdt_huobi_checkbox.stateChanged.connect(self.usdt_huobi_check)
        hbox_settings.addWidget(self.usdt_huobi_checkbox)

        self.btcusdt_huobi_checkbox = QCheckBox("BTC", self)
        self.btcusdt_huobi_checkbox.setChecked(True)
        self.btcusdt_huobi_checkbox.stateChanged.connect(self.btc_huobi_check)
        hbox_settings.addWidget(self.btcusdt_huobi_checkbox)

        self.ethusdt_huobi_checkbox = QCheckBox("ETH", self)
        self.ethusdt_huobi_checkbox.setChecked(True)
        self.ethusdt_huobi_checkbox.stateChanged.connect(self.eth_huobi_check)
        hbox_settings.addWidget(self.ethusdt_huobi_checkbox)

        vbox_huobi.addLayout(hbox_settings)

        # Сумма
        amount_huobi_label = QLabel("Сумма:", self)
        vbox_huobi.addWidget(amount_huobi_label)

        amount_huobi_input = QLineEdit(self)
        validator = QIntValidator(0, 10000000)
        amount_huobi_input.setValidator(validator)
        vbox_huobi.addWidget(amount_huobi_input)
        self.amount_huobi_input = amount_huobi_input

        # publisherType
        merch_huobi_label = QLabel("Тип публикатора:", self)
        vbox_huobi.addWidget(merch_huobi_label)

        merch_huobi_combobox = QComboBox(self)
        merch_huobi_combobox.addItem("Мерчант")
        merch_huobi_combobox.setItemData(merch_huobi_combobox.findText("Мерчант"), True, role=Qt.UserRole)
        merch_huobi_combobox.addItem("Все")
        merch_huobi_combobox.setItemData(merch_huobi_combobox.findText("Все"), False, role=Qt.UserRole)
        vbox_huobi.addWidget(merch_huobi_combobox)
        self.merch_huobi_combobox = merch_huobi_combobox

        # tradeType
        side_huobi_label = QLabel("Тип сделки:", self)
        vbox_huobi.addWidget(side_huobi_label)

        side_huobi_combobox = QComboBox(self)
        side_huobi_combobox.addItem("Покупка")
        side_huobi_combobox.setItemData(side_huobi_combobox.findText("Покупка"), "sell", role=Qt.UserRole)
        side_huobi_combobox.addItem("Продажа")
        side_huobi_combobox.setItemData(side_huobi_combobox.findText("Продажа"), "buy", role=Qt.UserRole)
        vbox_huobi.addWidget(side_huobi_combobox)
        self.side_huobi_combobox = side_huobi_combobox

        # payTypes
        payment_huobi_label = QLabel("Способы оплаты:", self)
        vbox_huobi.addWidget(payment_huobi_label)

        payment_huobi_input = QComboBox(self)
        payment_huobi_input.addItem("Тинькофф")
        payment_huobi_input.setItemData(payment_huobi_input.findText("Тинькофф"), "28", role=Qt.UserRole)
        payment_huobi_input.addItem("Сбербанк")
        payment_huobi_input.setItemData(payment_huobi_input.findText("Сбербанк"), "29", role=Qt.UserRole)
        payment_huobi_input.addItem("Райффайзен")
        payment_huobi_input.setItemData(payment_huobi_input.findText("Райффайзен"), "36", role=Qt.UserRole)
        vbox_huobi.addWidget(payment_huobi_input)
        self.payment_huobi_input = payment_huobi_input

        hbox.addLayout(vbox_huobi)

        vbox_spin = QVBoxLayout()

        spinbox1_label = QLabel(self)
        spinbox1_label.setText('Первые вычисления')
        spinbox1_label.setAlignment(Qt.AlignLeft)
        vbox_spin.addWidget(spinbox1_label)
        self.spinbox1_huobi.setDecimals(2)
        self.spinbox1_huobi.setMinimum(-100)
        self.spinbox1_huobi.setMaximum(100)
        self.spinbox1_huobi.setValue(-0.3)
        self.spinbox1_huobi.setSingleStep(0.05)
        vbox_spin.addWidget(self.spinbox1_huobi)

        spinbox2_label = QLabel(self)
        spinbox2_label.setText('Вторые вычисления')
        spinbox2_label.setAlignment(Qt.AlignLeft)
        vbox_spin.addWidget(spinbox2_label)
        self.spinbox2_huobi.setDecimals(2)
        self.spinbox2_huobi.setMinimum(-100)
        self.spinbox2_huobi.setMaximum(100)
        self.spinbox2_huobi.setValue(-0.5)
        self.spinbox2_huobi.setSingleStep(0.05)
        vbox_spin.addWidget(self.spinbox2_huobi)

        spinbox3_label = QLabel(self)
        spinbox3_label.setText('Третьи вычисления')
        spinbox3_label.setAlignment(Qt.AlignLeft)
        vbox_spin.addWidget(spinbox3_label)
        self.spinbox3_huobi.setDecimals(2)
        self.spinbox3_huobi.setMinimum(-100)
        self.spinbox3_huobi.setMaximum(100)
        self.spinbox3_huobi.setValue(-1.0)
        self.spinbox3_huobi.setSingleStep(0.05)
        vbox_spin.addWidget(self.spinbox3_huobi)


        hbox.addLayout(vbox_spin)

        vbox_comm = QVBoxLayout()

        # Для первого QDoubleSpinBox
        comm_label1 = QLabel(self)
        comm_label1.setText('Комиссия спота:')
        self.comm_spinbox1_huobi.setDecimals(2)
        self.comm_spinbox1_huobi.setMinimum(-100)
        self.comm_spinbox1_huobi.setMaximum(100)
        self.comm_spinbox1_huobi.setValue(-0.1)
        self.comm_spinbox1_huobi.setSingleStep(0.05)

        vbox_comm.addWidget(comm_label1)
        vbox_comm.addWidget(self.comm_spinbox1_huobi)

        # Для второго QDoubleSpinBox
        comm_label2 = QLabel(self)
        comm_label2.setText('Комиссия за покупку:')
        self.comm_spinbox2_huobi.setDecimals(2)
        self.comm_spinbox2_huobi.setMinimum(-100)
        self.comm_spinbox2_huobi.setMaximum(100)
        self.comm_spinbox2_huobi.setValue(-0.1)
        self.comm_spinbox2_huobi.setSingleStep(0.05)

        vbox_comm.addWidget(comm_label2)
        vbox_comm.addWidget(self.comm_spinbox2_huobi)

        comm_label3 = QLabel(self)
        comm_label3.setText('Комиссия за продажу:')
        self.comm_spinbox3_huobi.setDecimals(2)
        self.comm_spinbox3_huobi.setMinimum(-100)
        self.comm_spinbox3_huobi.setMaximum(100)
        self.comm_spinbox3_huobi.setValue(-0.1)
        self.comm_spinbox3_huobi.setSingleStep(0.05)

        vbox_comm.addWidget(comm_label3)
        vbox_comm.addWidget(self.comm_spinbox3_huobi)

        self.spinbox1_huobi.valueChanged.connect(self.update_spinboxs)
        self.spinbox2_huobi.valueChanged.connect(self.update_spinboxs)
        self.spinbox3_huobi.valueChanged.connect(self.update_spinboxs)
        self.comm_spinbox1_huobi.valueChanged.connect(self.update_spinboxs)
        self.comm_spinbox2_huobi.valueChanged.connect(self.update_spinboxs)
        self.comm_spinbox3_huobi.valueChanged.connect(self.update_spinboxs)

        hbox.addLayout(vbox_comm)




        return hbox

    def huobi_checkbox_changed(self, state):
        is_checked = state == Qt.Checked
        self.usdt_huobi_checkbox.setChecked(is_checked)
        self.btcusdt_huobi_checkbox.setChecked(is_checked)
        self.ethusdt_huobi_checkbox.setChecked(is_checked)
        self.widget_dict['label_exchange']['HUOBI'].setVisible(is_checked)
    def usdt_huobi_check(self,state):
        is_checked = state == Qt.Checked
        self.widget_dict['usdt_label_huobi'].setVisible(is_checked)
        self.update_huobi_checkbox_state()
        self.update_huobi_checkbox_state1()
    def btc_huobi_check(self,state):
        is_checked = state == Qt.Checked
        self.widget_dict['labels_huobi']['btcusdt'].setVisible(is_checked)
        self.update_huobi_checkbox_state()
        self.update_huobi_checkbox_state1()
    def eth_huobi_check(self,state):
        is_checked = state == Qt.Checked
        self.widget_dict['labels_huobi']['ethusdt'].setVisible(is_checked)
        self.update_huobi_checkbox_state()
        self.update_huobi_checkbox_state1()

    def update_huobi_checkbox_state(self):
        is_all_checked = (self.usdt_huobi_checkbox.isChecked() and
                          self.btcusdt_huobi_checkbox.isChecked() and
                          self.ethusdt_huobi_checkbox.isChecked())
        is_all_unchecked = (not self.usdt_huobi_checkbox.isChecked() and
                            not self.btcusdt_huobi_checkbox.isChecked() and
                            not self.ethusdt_huobi_checkbox.isChecked())
        if is_all_checked or is_all_unchecked:
            self.huobi_checkbox.blockSignals(True)
            self.huobi_checkbox.setChecked(is_all_checked)
            self.huobi_checkbox.blockSignals(False)
    def update_huobi_checkbox_state1(self):
        if any([self.usdt_huobi_checkbox.isChecked(),
                self.btcusdt_huobi_checkbox.isChecked(),
                self.ethusdt_huobi_checkbox.isChecked()]):
            self.widget_dict['label_exchange']['HUOBI'].setVisible(True)
        else:
            self.widget_dict['label_exchange']['HUOBI'].setVisible(False)
    def update_spinboxs(self):
        global spinboxes
        spinboxes['binance']['spinbox'] = [
            self.spinbox1_binance.value(),
            self.spinbox2_binance.value(),
            self.spinbox3_binance.value()
        ]
        spinboxes['binance']['comm_spinbox'] = [
            self.comm_spinbox1_binance.value(),
            self.comm_spinbox2_binance.value(),
            self.comm_spinbox3_binance.value()
        ]
        spinboxes['bybit']['spinbox'] = [
            self.spinbox1_bybit.value(),
            self.spinbox2_bybit.value(),
            self.spinbox3_bybit.value()
        ]
        spinboxes['bybit']['comm_spinbox'] = [
            self.comm_spinbox1_bybit.value(),
            self.comm_spinbox2_bybit.value(),
            self.comm_spinbox3_bybit.value()
        ]
        spinboxes['okx']['spinbox'] = [
            self.spinbox1_okx.value(),
            self.spinbox2_okx.value(),
            self.spinbox3_okx.value()
        ]
        spinboxes['okx']['comm_spinbox'] = [
            self.comm_spinbox1_okx.value(),
            self.comm_spinbox2_okx.value(),
            self.comm_spinbox3_okx.value()
        ]
        spinboxes['huobi']['spinbox'] = [
            self.spinbox1_huobi.value(),
            self.spinbox2_huobi.value(),
            self.spinbox3_huobi.value()
        ]
        spinboxes['huobi']['comm_spinbox'] = [
            self.comm_spinbox1_huobi.value(),
            self.comm_spinbox2_huobi.value(),
            self.comm_spinbox3_huobi.value()
        ]
    def apply_settings(self):
        global trans_amount, t2, keep_running, publisherType, tradeType, payTypes
        keep_running = False
        trans_amount = self.trans_amount_input.text()
        publisherType = self.publisher_type_combobox.currentData()
        tradeType = self.trade_type_combobox.currentData()
        payTypes = self.pay_types_input.currentData()
        #BYBIT
        global amount,side,payment,merch,t3
        amount = self.amount_input.text()
        side = self.side_combobox.currentData()
        payment = self.payment_input.currentData()
        merch = self.merch_combobox.currentData()
        #OKX
        global amount_okx,side_okx,payment_okx,merch_okx,t4
        amount_okx = self.amount_okx_input.text()
        side_okx = self.side_okx_combobox.currentData()
        payment_okx = self.payment_okx_input.currentData()
        merch_okx = self.merch_okx_combobox.currentData()
        #HUOBI
        global amount_huobi,side_huobi,payment_huobi,merch_huobi,t5
        amount_huobi = self.amount_huobi_input.text()
        side_huobi = self.side_huobi_combobox.currentData()
        payment_huobi = self.payment_huobi_input.currentData()
        merch_huobi = self.merch_huobi_combobox.currentData()
        #FEES


        # Сохраняем текущие значения параметров
        self.current_settings['trans_amount'] = trans_amount
        self.current_settings['publisherType'] = publisherType
        self.current_settings['tradeType'] = tradeType
        self.current_settings['payTypes'] = payTypes
        self.current_settings['amount'] = amount
        self.current_settings['side'] = side
        self.current_settings['payment'] = payment
        self.current_settings['merch'] = merch
        self.current_settings['amount_okx'] = amount_okx
        self.current_settings['side_okx'] = side_okx
        self.current_settings['payment_okx'] = payment_okx
        self.current_settings['merch_okx'] = merch_okx
        self.current_settings['amount_huobi'] = amount_huobi
        self.current_settings['side_huobi'] = side_huobi
        self.current_settings['payment_huobi'] = payment_huobi
        self.current_settings['merch_huobi'] = merch_huobi


        t2.join()  # Дождитесь завершения предыдущего потока
        t3.join()
        t4.join()
        t5.join()
        keep_running = True
        t2 = threading.Thread(target=update_usdt_price, args=(trans_amount, publisherType, tradeType, payTypes))
        t3 = threading.Thread(target=update_usdt_price_bybit, args=(amount, side, payment, merch))
        t4 = threading.Thread(target=okx, args=(amount_okx, side_okx, payment_okx, merch_okx))
        t5 = threading.Thread(target=huobi, args=(amount_huobi, side_huobi, payment_huobi, merch_huobi))
        t2.start()
        t3.start()
        t4.start()
        t5.start()

        self.close()

def main():
    app = QApplication(sys.argv)
    coin_info_app = CoinInfoApp()
    coin_info_app.show()


    sys.exit(app.exec_())



if __name__ == '__main__':
    main()