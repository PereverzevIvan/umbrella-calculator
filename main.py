# -* coding: utf-8 *-

# ------------- СПИСОК ОШИБОК ---------------------
# 1) Из-за наличия потоков программа не завершается после закрытия
# окна приложения. Питон не предоставляет методов для принудительного
# уничтожения потоков, а как исправить код функций, работающих в потоках,
# я не знаю. Временное решение: вызов несуществующего метода (ошибки)
# при закрытии окна (метод closeEvent() в классе MainWindow)

# Команда для компиляции exe-файла
# pyinstaller --onefile --noconsole --name="Umbrella" --icon="src/icons/Vector.ico" main.py

# Для корректной работы программе нужно следующее: 
# 1) Папака src
# 2) файл settings.py
# 3) файл resources_rc.py


# Импорт необходимых библиотек
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer, Qt, Qt, QPropertyAnimation, QSequentialAnimationGroup, QCoreApplication
from PyQt5.QtGui import QIcon, QFontDatabase, QFont, QIntValidator
from src.modules.ui_main_window import Ui_MainWindow
import websocket
import json
import threading
import requests
import time
import gzip
from settings import *


# Подключение к BINANCE
def connect_to_binance(trading_pairs):
    global keep_running
    url = "wss://stream.binance.com:9443/stream?streams="

    streams = []
    for pair in trading_pairs:
        streams.append(f"{pair.lower()}@aggTrade")

    url += "/".join(streams)

    while keep_running:
        try:
            ws = websocket.WebSocketApp(
                url,
                on_message=on_message_binance,
                on_error=on_error,
                on_close=on_close,
            )
            ws.run_forever()
        except Exception as e:
            print(f"Ошибка при подключении к вебсокетам: {e}")
            print("Повторное подключение через 5 секунд...")
            time.sleep(5)
    ws.close()


# Функции, вызываемая, если было получении сообщение от апи
def on_message_binance(ws, message):
    global BINANCE_USDT_PRICE, SPINBOXES
    data = json.loads(message)

    if 'data' in data:
        trade_data = data['data']
        symbol = trade_data['s']
        price = float(trade_data['p'])

        if symbol == 'SHIBUSDT':
            return
        
        if symbol not in BINANCE_COINS_DATA:
            BINANCE_COINS_DATA[symbol] = {}

        BINANCE_COINS_DATA[symbol]['price'] = price

        spinbox = SPINBOXES['binance']['spinbox']
        comm_spinbox = SPINBOXES['binance']['comm_spinbox']

        coms = sum([(-comm / 100) for comm in comm_spinbox])
        fees = [0] + [(-spin / 100) + coms for spin in spinbox]

        for index, fee in enumerate(fees):
            BINANCE_COINS_DATA[symbol][f'calculation_{index}'] = price * (1 - fee) * BINANCE_USDT_PRICE


# Функция, вызываемая при получении ошибки от апи
def on_error(ws, error):
    print(f"Ошибка: {error}")


# Функция, вызываемая при закрытии подключения к бирже
def on_close(ws):
    print("### Веб-сокет закрыт ###")


# BYBIT
def connect_to_bybit():
    global keep_running
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
    ws_bybit.close()


def on_message_bybit(ws_bybit, message_bybit):
    global BYBIT_USDT_PRICE, SPINBOXES
    data = json.loads(message_bybit)

    if 'topic' in data and data['topic'].startswith('tickers'):
        # Переводим в нижний регистр, чтобы соответствовать вашим другим символам
        symbol = data['data']['symbol'].lower()
        price = float(data['data']['lastPrice'])

        if symbol not in BYBIT_COINS_DATA:
            BYBIT_COINS_DATA[symbol] = {}

        BYBIT_COINS_DATA[symbol]['price'] = price

        spinbox = SPINBOXES['bybit']['spinbox']
        comm_spinbox = SPINBOXES['bybit']['comm_spinbox']

        coms = sum([(-comm / 100) for comm in comm_spinbox])
        fees = [0] + [(-spin / 100) + coms for spin in spinbox]

        for index, fee in enumerate(fees):
            BYBIT_COINS_DATA[symbol][f'calculation_{index}'] = price * (1 - fee) * BYBIT_USDT_PRICE


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


# OKX
def connect_to_okx(trading_pairs_okx):
    global keep_running
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
    ws_okx.close()


def on_message_okx(ws_okx, message_okx):
    global OKEX_USDT_PRICE, SPINBOXES
    data = json.loads(message_okx)

    if 'arg' in data and 'data' in data:
        if data["arg"]["channel"] == "tickers":
            trade_data = data['data'][0]
            symbol = trade_data['instId']
            price = float(trade_data['last'])

            if symbol not in OKEX_COINS_DATA:
                OKEX_COINS_DATA[symbol] = {}

            OKEX_COINS_DATA[symbol]['price'] = price

            spinbox = SPINBOXES['okx']['spinbox']
            comm_spinbox = SPINBOXES['okx']['comm_spinbox']

            coms = sum([(-comm / 100) for comm in comm_spinbox])
            fees = [0] + [(-spin / 100) + coms for spin in spinbox]

            for index, fee in enumerate(fees):
                OKEX_COINS_DATA[symbol][f'calculation_{index}'] = price * (
                    1 - fee) * OKEX_USDT_PRICE


def on_error_okx(ws_okx, error):
    print(f"Ошибка: {error}")


def on_close_okx(ws_okx):
    print("### Веб-сокет закрыт ###")


# HUOBI
def connect_to_huobi():
    global keep_running
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
    ws_huobi.close()


def on_message_huobi(ws_huobi, message_huobi):
    global HUOBI_USDT_PRICE, SPINBOXES
    decompressed_data = gzip.decompress(message_huobi).decode()
    data = json.loads(decompressed_data)

    if 'ping' in data:
        ws_huobi.send(json.dumps({"pong": data['ping']}))
    elif 'tick' in data and 'ch' in data:
        trade_data = data['tick']
        symbol = data['ch'].split('.')[1]
        price = float(trade_data['close'])

        if symbol not in HUOBI_COINS_DATA:
            HUOBI_COINS_DATA[symbol] = {}

        HUOBI_COINS_DATA[symbol]['price'] = price

        spinbox = SPINBOXES['huobi']['spinbox']
        comm_spinbox = SPINBOXES['huobi']['comm_spinbox']

        coms = sum([(-comm / 100) for comm in comm_spinbox])
        fees = [0] + [(-spin / 100) + coms for spin in spinbox]

        for index, fee in enumerate(fees):
            HUOBI_COINS_DATA[symbol][f'calculation_{index}'] = price * (
                1 - fee) * HUOBI_USDT_PRICE


def on_open_huobi(ws_huobi):
    reqs = [{"sub": f"market.{symbol}.ticker", "id": symbol}
            for symbol in trading_pairs_huobi]
    for req in reqs:
        ws_huobi.send(json.dumps(req))


def on_error_huobi(ws_huobi, error):
    print(f"Ошибка: {error}")


def on_close_huobi(ws_huobi):
    print("### Веб-сокет закрыт ###")


# Функция для обновления стоимость usdt на binance
def update_usdt_price_binance():
    global BINANCE_USDT_PRICE, keep_running, SPINBOXES, BINANCE_USDT_DATA
    url = 'https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search'
    headers = {
        'accept': '*/*',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }

    while keep_running:
        params = {
            "proMerchantAds": False,
            "page": 1,
            "rows": 1,
            "payTypes": [str(BINANCE_PAY_TYPES)] if BINANCE_PAY_TYPES else None,
            "countries": [],
            "publisherType": str(BINANCE_PUB_TYPE) if BINANCE_PUB_TYPE else None,
            "asset": "USDT",
            "fiat": "RUB",
            "tradeType": str(BINANCE_TRADE_TYPE) if BINANCE_TRADE_TYPE else None,
            "transAmount": str(BINANCE_AMOUNT) if BINANCE_AMOUNT else None
        }

        try:
            response = requests.post(
                url=url, headers=headers, json=params).json()

            BINANCE_USDT_PRICE = float(response['data'][0]['adv']['price'])
            BINANCE_USDT_DATA = {}
            spinbox = SPINBOXES['binance']['spinbox']
            comm_spinbox = SPINBOXES['binance']['comm_spinbox']

            coms = sum([(-comm / 100) for comm in comm_spinbox[1:]])
            fees = [0] + [(-spin / 100) + coms for spin in spinbox]

            for index, fee in enumerate(fees):
                BINANCE_USDT_DATA[f'calculation_{index}'] = (1 - fee) * BINANCE_USDT_PRICE

            time.sleep(5)
        except Exception as e:
            print(f"Ошибка при получении цены USDT: {e}")
            BINANCE_USDT_PRICE = 0
            time.sleep(5)


def update_usdt_price_bybit():
    global BYBIT_USDT_PRICE, BYBIT_USDT_DATA, SPINBOXES
    url = "https://api2.bybit.com/fiat/otc/item/online"
    headers = {
        'accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }

    while keep_running:
        params = {
            "userId": "",
            "tokenId": "USDT",
            "currencyId": "RUB",
            "payment": [BYBIT_PAY_TYPES],
            "side": BYBIT_TRADE_TYPE,
            "size": "10",
            "page": "1",
            "amount": BYBIT_AMOUNT,
            "authMaker": BYBIT_PUB_TYPE,
            "canTrade": False
        }

        try:
            response = requests.post(
                url=url, headers=headers, json=params).json()
            BYBIT_USDT_PRICE = float(response['result']['items'][0]['price'])
            BYBIT_USDT_DATA = {}
            spinbox = SPINBOXES['bybit']['spinbox']
            comm_spinbox = SPINBOXES['bybit']['comm_spinbox']

            coms = sum([(-comm / 100) for comm in comm_spinbox[1:]])
            fees = [0] + [(-spin / 100) + coms for spin in spinbox]

            for index, fee in enumerate(fees):
                BYBIT_USDT_DATA[f'calculation_{index}'] = (
                    1 - fee) * BYBIT_USDT_PRICE
            time.sleep(5)
        except Exception as e:
            BYBIT_USDT_PRICE = 0
            time.sleep(5)


def update_usdt_price_okx():
    global OKEX_USDT_PRICE, OKEX_USDT_DATA, SPINBOXES

    url = "https://www.okx.cab/v3/c2c/tradingOrders/getMarketplaceAdsPrelogin?"
    headers = {
        'accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }

    while keep_running:
        params = f"t=" \
            f"&side={OKEX_TRADE_TYPE}" \
            f"&paymentMethod={OKEX_PAY_TYPES}" \
            f"&userType={OKEX_PUB_TYPE}" \
            f"&hideOverseasVerificationAds=False" \
            f"&quoteMinAmountPerOrder={OKEX_AMOUNT}" \
            f"&sortType=" \
            f"&urlId=5" \
            f"&limit=100" \
            f"&cryptoCurrency=usdt" \
            f"&fiatCurrency=rub" \
            f"&currentPage=1" \
            f"&numberPerPage=5"

        try:
            response = requests.get(url=url + params, headers=headers).json()

            OKEX_USDT_PRICE = float(response['data'][OKEX_TRADE_TYPE][0]['price'])
            OKEX_USDT_DATA = {}
            spinbox = SPINBOXES['okx']['spinbox']
            comm_spinbox = SPINBOXES['okx']['comm_spinbox']

            coms = sum([(-comm / 100) for comm in comm_spinbox[1:]])
            fees = [0] + [(-spin / 100) + coms for spin in spinbox]

            for index, fee in enumerate(fees):
                OKEX_USDT_DATA[f'calculation_{index}'] = (
                    1 - fee) * OKEX_USDT_PRICE
            time.sleep(5)
        except Exception as e:
            print(
                f"Ошибка при получении цены USDT OKX: {e}. Ответ сервера: {response}")
            OKEX_USDT_PRICE = 0
            time.sleep(5)


def update_usdt_price_huobi():
    global HUOBI_USDT_PRICE, HUOBI_USDT_DATA, SPINBOXES
    url = "https://otc-api.trygofast.com/v1/data/trade-market?"
    headers = {
        'accept': '*/*',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }
    
    while keep_running:
        params = f"coinId=2" \
            "&currency=11" \
            f"&tradeType={HUOBI_TRADE_TYPE}" \
            "&currPage=1" \
            f"&payMethod={HUOBI_PAY_TYPES}" \
            "&acceptOrder=0" \
            "&country=" \
            "&blockType=general" \
            "&online=1" \
            "&range=0" \
            f"&amount={HUOBI_AMOUNT}" \
            "&isThumbsUp=false" \
            f"&isMerchant={HUOBI_PUB_TYPE}" \
            "&isTraded=false" \
            "&onlyTradable=false" \
            "&isFollowed=false"

        try:
            response = requests.get(url=url + params, headers=headers).json()
            # получить цену первого ордера
            HUOBI_USDT_PRICE = float(response['data'][0]['price'])
            HUOBI_USDT_DATA = {}
            spinbox = SPINBOXES['huobi']['spinbox']
            comm_spinbox = SPINBOXES['huobi']['comm_spinbox']

            coms = sum([(-comm / 100) for comm in comm_spinbox[1:]])
            fees = [0] + [(-spin / 100) + coms for spin in spinbox]

            for index, fee in enumerate(fees):
                HUOBI_USDT_DATA[f'calculation_{index}'] = (
                    1 - fee) * HUOBI_USDT_PRICE
            time.sleep(5)
        except Exception as e:
            print(f"Ошибка при получении цен для USDT HUOBI: {e}")
            HUOBI_USDT_PRICE = 0
            time.sleep(5)


def format_text(symbol, price, calculations, no_decimal, exchange):
    formatted_calcs = []
    for calc in calculations:
        if symbol == 'SHIBUSDT':
            formatted_calcs.append(f"{calc:,.6f}")
        else:
            formatted_calcs.append(
                f"{calc:,.0f}" if no_decimal else f"{calc:,.1f}")
    formatted_spinboxes = [f"{spinbox:.2f}".rstrip('0').rstrip(
        '.') for spinbox in SPINBOXES[exchange]['spinbox']]
    text = f"{symbol}\nPrice: {price:,.{int(no_decimal)}f}".replace(',', ' ')
    text += f"\t| {formatted_calcs[0]}".replace(',', ' ')
    for i, spinbox in enumerate(formatted_spinboxes, 1):
        text += f"\n{spinbox}%: {formatted_calcs[i]}".replace(',', ' ')
    return text


# Создаем потоки
t1 = threading.Thread(target=connect_to_binance, args=(trading_pairs,))
t8 = threading.Thread(target=connect_to_bybit)
t6 = threading.Thread(target=connect_to_okx, args=(trading_pairs_okx,))
t7 = threading.Thread(target=connect_to_huobi)
t2 = threading.Thread(target=update_usdt_price_binance, args=())
t3 = threading.Thread(target=update_usdt_price_bybit, args=())
t4 = threading.Thread(target=update_usdt_price_okx, args=())
t5 = threading.Thread(target=update_usdt_price_huobi, args=())

# Запускаем все потоки
threads = [t1, t2, t3, t4, t5, t6, t7, t8]
[thread.start() for thread in threads]


class MainWindow(QMainWindow, Ui_MainWindow):
    ''' Класс главного окна приложения '''

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)  # Инициализация дизайна
        self.setWindowTitle("Umbrella")  # Текст в тайтлбаре
        self.setWindowIcon(QIcon('./src/icons/Vector.svg'))  # Иконка в тайтлбаре
        self.settings_container.setMaximumWidth(0)  # Прячем блок с настройками

        # Установка шрифта
        fontId = QFontDatabase.addApplicationFont(":/fonts/fonts/Manrope-Regular.ttf")
        if fontId == 0:
            fontName = QFontDatabase.applicationFontFamilies(fontId)[0]
            self.font = QFont(fontName, 30)
        else:
            self.font = QFont()
        self.central_widget.setFont(self.font)  

        # Вызов функций
        self.init_settings()
        self.load_settings()
        self.set_timer()
        self.update_labels()
        self.bybit_blocks['bnb'].setStyleSheet('max-height: 0px')
        self.okex_blocks['bnb'].setStyleSheet('max-height: 0px')
        self.huobi_blocks['bnb'].setStyleSheet('max-height: 0px')

        self.bybit_blocks['bnb'].hide()
        self.bybit_seps['bnb'].hide()
        self.okex_blocks['bnb'].hide()
        self.okex_seps['bnb'].hide()
        self.huobi_blocks['bnb'].hide()
        self.huobi_seps['bnb'].hide()

        # Переменные приложения
        self.settings_is_hide = True
        self.checkboxes_is_changes = False

        # Привязка функций к событиям
        self.settings_btn.clicked.connect(self.toggle_settings)
        self.submit_btn.clicked.connect(self.apply_settings)
        self.submit_btn_2.clicked.connect(self.apply_settings)
        self.submit_btn_3.clicked.connect(self.apply_settings)
        self.submit_btn_4.clicked.connect(self.apply_settings)

        self.binance_checkboxes['binance'].stateChanged.connect(lambda: self.change_checkboxes(self.binance_checkboxes, 'binance'))
        self.binance_checkboxes['usdt'].stateChanged.connect(lambda: self.change_checkboxes(self.binance_checkboxes, 'usdt'))
        self.binance_checkboxes['btc'].stateChanged.connect(lambda: self.change_checkboxes(self.binance_checkboxes, 'btc'))
        self.binance_checkboxes['eth'].stateChanged.connect(lambda: self.change_checkboxes(self.binance_checkboxes, 'eth'))
        self.binance_checkboxes['bnb'].stateChanged.connect(lambda: self.change_checkboxes(self.binance_checkboxes, 'bnb'))

        self.bybit_checkboxes['bybit'].stateChanged.connect(lambda: self.change_checkboxes(self.bybit_checkboxes, 'bybit'))
        self.bybit_checkboxes['usdt'].stateChanged.connect(lambda: self.change_checkboxes(self.bybit_checkboxes, 'usdt'))
        self.bybit_checkboxes['btc'].stateChanged.connect(lambda: self.change_checkboxes(self.bybit_checkboxes, 'btc'))
        self.bybit_checkboxes['eth'].stateChanged.connect(lambda: self.change_checkboxes(self.bybit_checkboxes, 'eth'))

        self.okex_checkboxes['okex'].stateChanged.connect(lambda: self.change_checkboxes(self.okex_checkboxes, 'okex'))
        self.okex_checkboxes['usdt'].stateChanged.connect(lambda: self.change_checkboxes(self.okex_checkboxes, 'usdt'))
        self.okex_checkboxes['btc'].stateChanged.connect(lambda: self.change_checkboxes(self.okex_checkboxes, 'btc'))
        self.okex_checkboxes['eth'].stateChanged.connect(lambda: self.change_checkboxes(self.okex_checkboxes, 'eth'))

        self.huobi_checkboxes['huobi'].stateChanged.connect(lambda: self.change_checkboxes(self.huobi_checkboxes, 'huobi'))
        self.huobi_checkboxes['usdt'].stateChanged.connect(lambda: self.change_checkboxes(self.huobi_checkboxes, 'usdt'))
        self.huobi_checkboxes['btc'].stateChanged.connect(lambda: self.change_checkboxes(self.huobi_checkboxes, 'btc'))
        self.huobi_checkboxes['eth'].stateChanged.connect(lambda: self.change_checkboxes(self.huobi_checkboxes, 'eth'))

    def change_checkboxes(self, checks, cur_key):
        main_key = list(checks)[0]
        secondary_key = list(checks)[1::]
        index = list(checks).index(cur_key)
        all_sec_checks_is_false = all([not(checks[key].isChecked()) for key in secondary_key])
        any_sec_checks_is_true = any([checks[key].isChecked() for key in secondary_key])

        print(cur_key, index)

        if index == 0:
            if checks[main_key].isChecked():
                if all_sec_checks_is_false:
                    [checks[key].setChecked(True) for key in secondary_key]
            else:
                [checks[key].setChecked(False) for key in secondary_key]
        else:
            if any_sec_checks_is_true:
                checks[main_key].setChecked(True)
            elif all_sec_checks_is_false:
                checks[main_key].setChecked(False)

    def change_blocks_visible(self):
        ''' Метод для обновления видимости элементов интерфейса в 
        соответствии с чекбоксами в настройках '''
        checkbox_lists = [
            [self.binance_checkboxes, self.binance_blocks, self.binance_seps],
            [self.bybit_checkboxes, self.bybit_blocks, self.bybit_seps],
            [self.okex_checkboxes, self.okex_blocks, self.okex_seps], 
            [self.huobi_checkboxes, self.huobi_blocks, self.huobi_seps]
        ]

        for checks, blocks, seps in  checkbox_lists:
            for parametr in checks.keys():
                if not (checks[parametr].isChecked()):
                    if parametr in seps:
                        seps[parametr].hide()
                    blocks[parametr].hide()
                else:
                    if parametr in seps:
                        seps[parametr].show()
                    blocks[parametr].show()

    def init_settings(self):
        ''' Метод инициализации словарей для обращения к элементам
         GUI и текущим настройкам '''
        
        validator = QIntValidator(0, 10000000)
        self.sum_line.setValidator(validator)
        self.sum_line_2.setValidator(validator)
        self.sum_line_3.setValidator(validator)
        self.sum_line_4.setValidator(validator)

        # Текущие настройки
        self.current_settings = {
            'trans_amount': BINANCE_AMOUNT,
            'publisherType': BINANCE_PUB_TYPE,
            'tradeType': BINANCE_TRADE_TYPE,
            'payTypes': BINANCE_PAY_TYPES,
            'amount': BYBIT_AMOUNT,
            'side': BYBIT_TRADE_TYPE,
            'payment': BYBIT_PAY_TYPES,
            'merch': BYBIT_PUB_TYPE,
            'amount_okx': OKEX_AMOUNT,
            'side_okx': OKEX_TRADE_TYPE,
            'payment_okx': OKEX_PAY_TYPES,
            'merch_okx': OKEX_PUB_TYPE,
            'amount_huobi': HUOBI_AMOUNT,
            'side_huobi': HUOBI_TRADE_TYPE,
            'payment_huobi': HUOBI_PAY_TYPES,
            'merch_huobi': HUOBI_PUB_TYPE,
        }

        # Все блоки площадки binance
        self.binance_blocks = {
            'binance': self.card_1,
            'usdt': self.usdt,
            'btc': self.btcustd,
            'eth': self.ethusdt,
            'bnb': self.bnbusdt,
        }

        # Все разделители для карточки binance
        self.binance_seps = {
            'usdt': self.binance_sep,
            'btc': self.binance_sep_2,
            'eth': self.binance_sep_3,
            'bnb': self.binance_sep_4,
        }

        # Все лэйблы для компании binance (ЗНАЧЕНИЯ)
        self.binance_values = {
            'usdt': {
                'title': self.usdt_title,
                'price': self.usdt_price,
                '0.3': self.usdt_three,
                '0.5': self.usdt_five,
                '1': self.usdt_one,
            },
            'btc': {
                'title': self.btc_title,
                'price': self.btc_price,
                '0.3': self.btc_three,
                '0.5': self.btc_five,
                '1': self.btc_one,
            },
            'eth': {
                'title': self.eth_title,
                'price': self.eth_price,
                '0.3': self.eth_three,
                '0.5': self.eth_five,
                '1': self.eth_one,
            },
            'bnb': {
                'title': self.bnb_title,
                'price': self.bnb_price,
                '0.3': self.bnb_three,
                '0.5': self.bnb_five,
                '1': self.bnb_one,
            }
        }

        # Все лэйблы для компании binance (НАДПИСИ)
        self.binance_labels = {
            'usdt': {
                '0.3': self.usdt_first_label,
                '0.5': self.usdt_second_label,
                '1': self.usdt_third_label,
            },
            'btc': {
                '0.3': self.btc_first_label,
                '0.5': self.btc_second_label,
                '1': self.btc_third_label,
            },
            'eth': {
                '0.3': self.eth_first_label,
                '0.5': self.eth_second_label,
                '1': self.eth_third_label,
            },
            'bnb': {
                '0.3': self.bnb_first_label,
                '0.5': self.bnb_second_label,
                '1': self.bnb_third_label,
            }
        }

        # Все блоки площадки bybit
        self.bybit_blocks = {
            'bybit': self.card_2,
            'usdt': self.usdt_2,
            'btc': self.btcustd_2,
            'eth': self.ethusdt_2,
            'bnb': self.bnbusdt_2,
        }

        # Все разделители для карточки bybit
        self.bybit_seps = {
            'usdt': self.bybit_sep,
            'btc': self.bybit_sep_2,
            'eth': self.bybit_sep_3,
            'bnb': self.bybit_sep_4,
        }

        

        # Все лэйблы для компании bybit (ЗНАЧЕНИЯ)
        self.bybit_values = {
            'usdt': {
                'title': self.usdt_title_2,
                'price': self.usdt_price_2,
                '0.3': self.usdt_three_2,
                '0.5': self.usdt_five_2,
                '1': self.usdt_one_2,
            },
            'btc': {
                'title': self.btc_title_2,
                'price': self.btc_price_2,
                '0.3': self.btc_three_2,
                '0.5': self.btc_five_2,
                '1': self.btc_one_2,
            },
            'eth': {
                'title': self.eth_title_2,
                'price': self.eth_price_2,
                '0.3': self.eth_three_2,
                '0.5': self.eth_five_2,
                '1': self.eth_one_2,
            },
            'bnb': {
                'title': self.bnb_title_2,
                'price': self.bnb_price_2,
                '0.3': self.bnb_three_2,
                '0.5': self.bnb_five_2,
                '1': self.bnb_one_2,
            }
        }

        # Все лэйблы для компании bybit (НАДПИСИ)
        self.bybit_labels = {
            'usdt': {
                '0.3': self.usdt_first_label_2,
                '0.5': self.usdt_second_label_2,
                '1': self.usdt_third_label_2,
            },
            'btc': {
                '0.3': self.btc_first_label_2,
                '0.5': self.btc_second_label_2,
                '1': self.btc_third_label_2,
            },
            'eth': {
                '0.3': self.eth_first_label_2,
                '0.5': self.eth_second_label_2,
                '1': self.eth_third_label_2,
            },
            'bnb': {
                '0.3': self.bnb_first_label_2,
                '0.5': self.bnb_second_label_2,
                '1': self.bnb_third_label_2,
            }
        }

        # Все блоки площадки okex
        self.okex_blocks = {
            'okex': self.card_3,
            'usdt': self.usdt_3,
            'btc': self.btcustd_3,
            'eth': self.ethusdt_3,
            'bnb': self.bnbusdt_3,
        }

        # Все разделители для карточки okex
        self.okex_seps = {
            'usdt': self.okx_sep,
            'btc': self.okx_sep_2,
            'eth': self.okx_sep_3,
            'bnb': self.okx_sep_4,
        }

        # Все лэйблы для компании okex (ЗНАЧЕНИЯ)
        self.okex_values = {
            'usdt': {
                'title': self.usdt_title_3,
                'price': self.usdt_price_3,
                '0.3': self.usdt_three_3,
                '0.5': self.usdt_five_3,
                '1': self.usdt_one_3,
            },
            'btc': {
                'title': self.btc_title_3,
                'price': self.btc_price_3,
                '0.3': self.btc_three_3,
                '0.5': self.btc_five_3,
                '1': self.btc_one_3,
            },
            'eth': {
                'title': self.eth_title_3,
                'price': self.eth_price_3,
                '0.3': self.eth_three_3,
                '0.5': self.eth_five_3,
                '1': self.eth_one_3,
            },
            'bnb': {
                'title': self.bnb_title_3,
                'price': self.bnb_price_3,
                '0.3': self.bnb_three_3,
                '0.5': self.bnb_five_3,
                '1': self.bnb_one_3,
            }
        }

        # Все лэйблы для компании okex (НАДПИСИ)
        self.okex_labels = {
            'usdt': {
                '0.3': self.usdt_first_label_3,
                '0.5': self.usdt_second_label_3,
                '1': self.usdt_third_label_3,
            },
            'btc': {
                '0.3': self.btc_first_label_3,
                '0.5': self.btc_second_label_3,
                '1': self.btc_third_label_3,
            },
            'eth': {
                '0.3': self.eth_first_label_3,
                '0.5': self.eth_second_label_3,
                '1': self.eth_third_label_3,
            },
            'bnb': {
                '0.3': self.bnb_first_label_3,
                '0.5': self.bnb_second_label_3,
                '1': self.bnb_third_label_3,
            }
        }

        # Все блоки площадки huobi
        self.huobi_blocks = {
            'huobi': self.card_4,
            'usdt': self.usdt_4,
            'btc': self.btcustd_4,
            'eth': self.ethusdt_4,
            'bnb': self.bnbusdt_4,
        }

        # Все разделители для карточки huobi
        self.huobi_seps = {
            'usdt': self.huobi_sep,
            'btc': self.huobi_sep_2,
            'eth': self.huobi_sep_3,
            'bnb': self.huobi_sep_4,
        }

        # Все лэйблы для компании huobi (ЗНАЧЕНИЯ)
        self.huobi_values = {
            'usdt': {
                'title': self.usdt_title_4,
                'price': self.usdt_price_4,
                '0.3': self.usdt_three_4,
                '0.5': self.usdt_five_4,
                '1': self.usdt_one_4,
            },
            'btc': {
                'title': self.btc_title_4,
                'price': self.btc_price_4,
                '0.3': self.btc_three_4,
                '0.5': self.btc_five_4,
                '1': self.btc_one_4,
            },
            'eth': {
                'title': self.eth_title_4,
                'price': self.eth_price_4,
                '0.3': self.eth_three_4,
                '0.5': self.eth_five_4,
                '1': self.eth_one_4,
            },
            'bnb': {
                'title': self.bnb_title_4,
                'price': self.bnb_price_4,
                '0.3': self.bnb_three_4,
                '0.5': self.bnb_five_4,
                '1': self.bnb_one_4,
            }
        }

        # Все лэйблы для компании huobi (НАДПИСИ)
        self.huobi_labels = {
            'usdt': {
                '0.3': self.usdt_first_label_4,
                '0.5': self.usdt_second_label_4,
                '1': self.usdt_third_label_4,
            },
            'btc': {
                '0.3': self.btc_first_label_4,
                '0.5': self.btc_second_label_4,
                '1': self.btc_third_label_4,
            },
            'eth': {
                '0.3': self.eth_first_label_4,
                '0.5': self.eth_second_label_4,
                '1': self.eth_third_label_4,
            },
            'bnb': {
                '0.3': self.bnb_first_label_4,
                '0.5': self.bnb_second_label_4,
                '1': self.bnb_third_label_4,
            }
        }

        # Все поля настроек для площадки binance
        self.binance_settings = {
            'sum': self.sum_line,
            'publicator': self.pub_edit,
            'deal': self.deal_edit,
            'pay_method': self.pay_type,
            'first': self.first_math,
            'second': self.second_math,
            'third': self.third_math,
            'spot': self.comm_spot,
            'buy': self.comm_buy,
            'sale': self.comm_sale,
            'submit': self.submit_btn,
        }

        self.binance_checkboxes = {
            'binance': self.binance_check,
            'usdt': self.usdt_check,
            'btc': self.btc_check,
            'eth': self.eth_check,
            'bnb': self.bnb_check,
        }

        # Все поля настроек для площадки bybit
        self.bybit_settings = {
            'sum': self.sum_line_2,
            'publicator': self.pub_edit_2,
            'deal': self.deal_edit_2,
            'pay_method': self.pay_type_2,
            'first': self.first_math_2,
            'second': self.second_math_2,
            'third': self.third_math_2,
            'spot': self.comm_spot_2,
            'buy': self.comm_buy_2,
            'sale': self.comm_sale_2,
            'submit': self.submit_btn_2,
        }

        self.bybit_checkboxes = {
            'bybit': self.bybit_check,
            'usdt': self.usdt_check_2,
            'btc': self.btc_check_2,
            'eth': self.eth_check_2,
        }

        # Все поля настроек для площадки okex
        self.okex_settings = {
            'sum': self.sum_line_3,
            'publicator': self.pub_edit_3,
            'deal': self.deal_edit_3,
            'pay_method': self.pay_type_3,
            'first': self.first_math_3,
            'second': self.second_math_3,
            'third': self.third_math_3,
            'spot': self.comm_spot_3,
            'buy': self.comm_buy_3,
            'sale': self.comm_sale_3,
            'submit': self.submit_btn_3,
        }

        self.okex_checkboxes = {
            'okex': self.okex_check,
            'usdt': self.usdt_check_3,
            'btc': self.btc_check_3,
            'eth': self.eth_check_3,
        }

        # Все поля настроек для площадки huobi
        self.huobi_settings = {
            'sum': self.sum_line_4,
            'publicator': self.pub_edit_4,
            'deal': self.deal_edit_4,
            'pay_method': self.pay_type_4,
            'first': self.first_math_4,
            'second': self.second_math_4,
            'third': self.third_math_4,
            'spot': self.comm_spot_4,
            'buy': self.comm_buy_4,
            'sale': self.comm_sale_4,
            'submit': self.submit_btn_4,
        }

        self.huobi_checkboxes = {
            'huobi': self.huobi_check,
            'usdt': self.usdt_check_4,
            'btc': self.btc_check_4,
            'eth': self.eth_check_4,
        }

    def update_labels(self):
        ''' Изменение надписей процентажа в соответствии со спинбоксами в настройках '''
        global SPINBOXES
        
        # Binance
        for parametr in self.binance_labels:
            for i, label in enumerate(self.binance_labels[parametr]):
                self.binance_labels[parametr][label].setText(f"{round(SPINBOXES['binance']['spinbox'][i], 2)}%:")

        # Bybit
        for parametr in self.bybit_labels:
            for i, label in enumerate(self.bybit_labels[parametr]):
                self.bybit_labels[parametr][label].setText(f"{round(SPINBOXES['bybit']['spinbox'][i], 2)}%:")
        
        # Okex 
        for parametr in self.okex_labels:
            for i, label in enumerate(self.okex_labels[parametr]):
                self.okex_labels[parametr][label].setText(f"{round(SPINBOXES['okx']['spinbox'][i], 2)}%:")

        # Huobi
        for parametr in self.huobi_labels:
            for i, label in enumerate(self.huobi_labels[parametr]):
                self.huobi_labels[parametr][label].setText(f"{round(SPINBOXES['huobi']['spinbox'][i], 2)}%:")

    def set_labels_value(self, label_list, values):
        ''' Метод присваивания значений лэйблам '''
        for parametr in label_list.keys():
            # Игнорируется заголовок раздела, так как я не понял, что туда вставлять
            if parametr != 'title':
                value = round(values.pop(0), 2) if values else '-'
                label_list[parametr].setText(str(value))

    def update_binance(self):
        # Собираем информация
        calcs = [BINANCE_USDT_DATA.get(f'calculation_{i}', 0) for i in range(1, 4)]
        if BINANCE_USDT_PRICE == 0:
            calcs = [0, 0, 0]

        usdt_info = [BINANCE_USDT_PRICE] + [BINANCE_USDT_DATA.get(f'calculation_{i}', 0) for i in range(1, 4)]
        bloks = ['btc', 'eth', 'bnb']

        self.set_labels_value(self.binance_values['usdt'], usdt_info)
        for i, symbol in enumerate(BINANCE_COINS_DATA):

            data = BINANCE_COINS_DATA[symbol]
            price = data.get('price', 0)
            calcs = [data.get(f'calculation_{i}', 0) for i in range(1, 4)]
            
            self.binance_values[bloks[i]]['price'].setText(f'{price:,.2f}'.replace(',', '  '))
            self.binance_values[bloks[i]]['0.3'].setText(f'{calcs[0]:,.2f}'.replace(',', '  '))
            self.binance_values[bloks[i]]['0.5'].setText(f'{calcs[1]:,.2f}'.replace(',', '  '))
            self.binance_values[bloks[i]]['1'].setText(f'{calcs[2]:,.2f}'.replace(',', '  '))

    def update_bybit(self):
        # Собираем информация
        calcs = [BYBIT_USDT_DATA.get(f'calculation_{i}', 0) for i in range(1, 4)]
        if BYBIT_USDT_PRICE == 0:
            calcs = [0, 0, 0]

        usdt_info = [BYBIT_USDT_PRICE] + calcs
        bloks = ['btc', 'eth']

        self.set_labels_value(self.bybit_values['usdt'], usdt_info)
        for i, symbol in enumerate(BYBIT_COINS_DATA):
            data = BYBIT_COINS_DATA[symbol]
            price = data.get('price', 0)
            calcs = [data.get(f'calculation_{i}', 0) for i in range(1, 4)]
            
            self.bybit_values[bloks[i]]['price'].setText(f'{price:,.2f}'.replace(',', '  '))
            self.bybit_values[bloks[i]]['0.3'].setText(f'{calcs[0]:,.2f}'.replace(',', '  '))
            self.bybit_values[bloks[i]]['0.5'].setText(f'{calcs[1]:,.2f}'.replace(',', '  '))
            self.bybit_values[bloks[i]]['1'].setText(f'{calcs[2]:,.2f}'.replace(',', '  '))

    def update_okex(self):
        # Собираем информация
        calcs = [OKEX_USDT_DATA.get(f'calculation_{i}', 0) for i in range(1, 4)]
        if OKEX_USDT_PRICE == 0:
            calcs = [0, 0, 0]
        
        usdt_info = [OKEX_USDT_PRICE] + calcs
        bloks = ['btc', 'eth']

        self.set_labels_value(self.okex_values['usdt'], usdt_info)
        for i, symbol in enumerate(OKEX_COINS_DATA):
            data = OKEX_COINS_DATA[symbol]
            price = data.get('price', 0)
            calcs = [data.get(f'calculation_{i}', 0) for i in range(1, 4)]
            
            self.okex_values[bloks[i]]['price'].setText(f'{price:,.2f}'.replace(',', '  '))
            self.okex_values[bloks[i]]['0.3'].setText(f'{calcs[0]:,.2f}'.replace(',', '  '))
            self.okex_values[bloks[i]]['0.5'].setText(f'{calcs[1]:,.2f}'.replace(',', '  '))
            self.okex_values[bloks[i]]['1'].setText(f'{calcs[2]:,.2f}'.replace(',', '  '))

    def update_huobi(self):
        # Собираем информация
        calcs = [HUOBI_USDT_DATA.get(f'calculation_{i}', 0) for i in range(1, 4)]
        if HUOBI_USDT_PRICE == 0:
            calcs = [0, 0, 0]

        usdt_info = [HUOBI_USDT_PRICE] + calcs
        bloks = ['btc', 'eth']

        self.set_labels_value(self.huobi_values['usdt'], usdt_info)
        for i, symbol in enumerate(HUOBI_COINS_DATA):
            data = HUOBI_COINS_DATA[symbol]
            price = data.get('price', 0)
            calcs = [data.get(f'calculation_{i}', 0) for i in range(1, 4)]
            
            self.huobi_values[bloks[i]]['price'].setText(f'{price:,.2f}'.replace(',', '  '))
            self.huobi_values[bloks[i]]['0.3'].setText(f'{calcs[0]:,.2f}'.replace(',', '  '))
            self.huobi_values[bloks[i]]['0.5'].setText(f'{calcs[1]:,.2f}'.replace(',', '  '))
            self.huobi_values[bloks[i]]['1'].setText(f'{calcs[2]:,.2f}'.replace(',', '  '))

    def update_values(self):
        ''' Метод обновления информации для всех площадок '''
        self.update_binance()
        self.update_bybit()
        self.update_okex()
        self.update_huobi()

    def load_settings(self):
        ''' Метод загрузки текущих настроек в интерфейс (ПРИМЕР) '''
        # Шорткаты
        cur_settings = self.current_settings

        # Binance
        gui = self.binance_settings
        checkboxes = self.binance_checkboxes

        # Заполнение LineEdit и ComboBox`ов
        gui['sum'].setText(str(cur_settings['trans_amount']))
        index = max(gui['publicator'].findData(
            cur_settings['publisherType']), 0)
        gui['publicator'].setCurrentIndex(index)
        index = max(gui['deal'].findData(cur_settings['tradeType']), 0)
        gui['deal'].setCurrentIndex(index)
        index = max(gui['pay_method'].findData(cur_settings['payTypes']), 0)
        gui['pay_method'].setCurrentIndex(index)
        
        # Присваивание идентификаторов для вариантов в выпадающих списках
        gui['publicator'].setItemData(0, None, role=Qt.UserRole)
        gui['publicator'].setItemData(1, 'merchant', role=Qt.UserRole)
        gui['deal'].setItemData(0, 'buy', role=Qt.UserRole)
        gui['deal'].setItemData(1, 'sell', role=Qt.UserRole)
        gui['pay_method'].setItemData(0, 'RaiffeisenBank', role=Qt.UserRole) # Райффайзен
        gui['pay_method'].setItemData(1, 'TinkoffNew', role=Qt.UserRole) # Тинькофф
        gui['pay_method'].setItemData(2, 'RosBankNew', role=Qt.UserRole) # Сбербанк

        # Заполнение спинбоксов
        gui['first'].setValue(-0.3)
        gui['second'].setValue(-0.5)
        gui['third'].setValue(-1.0)
        gui['spot'].setValue(-0.1)
        gui['buy'].setValue(-0.1)
        gui['sale'].setValue(-0.1)

        # Заполнение чекбоксов
        [checkboxes[item].setChecked(True) for item in checkboxes]

        # Bybit
        gui = self.bybit_settings
        checkboxes = self.bybit_checkboxes

        # Заполнение LineEdit и ComboBox`ов
        gui['sum'].setText(str(cur_settings['amount']))
        index = max(gui['publicator'].findData(cur_settings['merch']), 0)
        gui['publicator'].setCurrentIndex(index)
        index = max(gui['deal'].findData(cur_settings['side']), 0)
        gui['deal'].setCurrentIndex(index)
        index = max(gui['pay_method'].findData(cur_settings['payment']), 0)
        gui['pay_method'].setCurrentIndex(index)

        # Присваивание идентификаторов для вариантов в выпадающих списках
        gui['publicator'].setItemData(0, False, role=Qt.UserRole)
        gui['publicator'].setItemData(1, True, role=Qt.UserRole)
        gui['deal'].setItemData(0, "1", role=Qt.UserRole)
        gui['deal'].setItemData(1, "0", role=Qt.UserRole)
        gui['pay_method'].setItemData(0, "64", role=Qt.UserRole)  # Райффайзен
        gui['pay_method'].setItemData(1, "75", role=Qt.UserRole)  # Тинькофф
        gui['pay_method'].setItemData(2, "185", role=Qt.UserRole)  # Сбербанк

        # Заполнение спинбоксов
        gui['first'].setValue(-0.3)
        gui['second'].setValue(-0.5)
        gui['third'].setValue(-1.0)
        gui['spot'].setValue(-0.1)
        gui['buy'].setValue(-0.1)
        gui['sale'].setValue(-0.1)

        # Заполнение чекбоксов
        [checkboxes[item].setChecked(True) for item in checkboxes]

        # Okex
        gui = self.okex_settings
        checkboxes = self.okex_checkboxes

        # Заполнение LineEdit и ComboBox`ов
        gui['sum'].setText(str(cur_settings['amount_okx']))
        index = max(gui['publicator'].findData(cur_settings['merch_okx']), 0)
        gui['publicator'].setCurrentIndex(index)
        index = max(gui['deal'].findData(cur_settings['side_okx']), 0)
        gui['deal'].setCurrentIndex(index)
        index = max(gui['pay_method'].findData(cur_settings['payment_okx']), 0)
        gui['pay_method'].setCurrentIndex(index)

        # Присваивание идентификаторов для вариантов в выпадающих списках
        gui['publicator'].setItemData(0, "all", role=Qt.UserRole)
        gui['publicator'].setItemData(1, "certified", role=Qt.UserRole)
        gui['deal'].setItemData(0, "buy", role=Qt.UserRole)
        gui['deal'].setItemData(1, "sell", role=Qt.UserRole)
        gui['pay_method'].setItemData(0, "Raiffaizen", role=Qt.UserRole)  # Райффайзен
        gui['pay_method'].setItemData(1, "Tinkoff", role=Qt.UserRole)  # Тинькофф
        gui['pay_method'].setItemData(2, "Sberbank", role=Qt.UserRole)  # Сбербанк

        # Заполнение спинбоксов
        gui['first'].setValue(-0.3)
        gui['second'].setValue(-0.5)
        gui['third'].setValue(-1.0)
        gui['spot'].setValue(-0.1)
        gui['buy'].setValue(-0.1)
        gui['sale'].setValue(-0.1)

        # Заполнение чекбоксов
        [checkboxes[item].setChecked(True) for item in checkboxes]

        # Huobi
        gui = self.huobi_settings
        checkboxes = self.huobi_checkboxes

        # Заполнение LineEdit и ComboBox`ов
        gui['sum'].setText(str(cur_settings['amount_huobi']))
        index = max(gui['publicator'].findData(cur_settings['merch_okx']), 0)
        gui['publicator'].setCurrentIndex(index)
        index = max(gui['deal'].findData(cur_settings['merch_huobi']), 0)
        gui['deal'].setCurrentIndex(index)
        index = max(gui['pay_method'].findData(
            cur_settings['payment_huobi']), 0)
        gui['pay_method'].setCurrentIndex(index)

        # Присваивание идентификаторов для вариантов в выпадающих списках
        gui['publicator'].setItemData(0, False, role=Qt.UserRole)
        gui['publicator'].setItemData(1, True, role=Qt.UserRole)
        gui['deal'].setItemData(0, "buy", role=Qt.UserRole)
        gui['deal'].setItemData(1, "sell", role=Qt.UserRole)
        gui['pay_method'].setItemData(0, "36", role=Qt.UserRole)  # Райффайзен
        gui['pay_method'].setItemData(1, "28", role=Qt.UserRole)  # Тинькофф
        gui['pay_method'].setItemData(2, "29", role=Qt.UserRole)  # Сбербанк

        # Заполнение спинбоксов
        gui['first'].setValue(-0.3)
        gui['second'].setValue(-0.5)
        gui['third'].setValue(-1.0)
        gui['spot'].setValue(-0.1)
        gui['buy'].setValue(-0.1)
        gui['sale'].setValue(-0.1)

        # Заполнение чекбоксов
        [checkboxes[item].setChecked(True) for item in checkboxes]

    def update_spinboxs(self):
        ''' Метод для обновления значений спинбоксов для вычислений комиссий и прочего '''
        global SPINBOXES

        SPINBOXES['binance']['spinbox'] = [
            self.binance_settings['first'].value(),
            self.binance_settings['second'].value(),
            self.binance_settings['third'].value()
        ]
        SPINBOXES['binance']['comm_spinbox'] = [
            self.binance_settings['spot'].value(),
            self.binance_settings['buy'].value(),
            self.binance_settings['sale'].value()
        ]
        SPINBOXES['bybit']['spinbox'] = [
            self.bybit_settings['first'].value(),
            self.bybit_settings['second'].value(),
            self.bybit_settings['third'].value()
        ]
        SPINBOXES['bybit']['comm_spinbox'] = [
            self.bybit_settings['spot'].value(),
            self.bybit_settings['buy'].value(),
            self.bybit_settings['sale'].value()
        ]
        SPINBOXES['okx']['spinbox'] = [
            self.okex_settings['first'].value(),
            self.okex_settings['second'].value(),
            self.okex_settings['third'].value()
        ]
        SPINBOXES['okx']['comm_spinbox'] = [
            self.okex_settings['spot'].value(),
            self.okex_settings['buy'].value(),
            self.okex_settings['sale'].value()
        ]
        SPINBOXES['huobi']['spinbox'] = [
            self.huobi_settings['first'].value(),
            self.huobi_settings['second'].value(),
            self.huobi_settings['third'].value()
        ]
        SPINBOXES['huobi']['comm_spinbox'] = [
            self.huobi_settings['spot'].value(),
            self.huobi_settings['buy'].value(),
            self.huobi_settings['sale'].value()
        ]

        self.update_labels()

    def apply_settings(self):
        ''' Метод сохранения и применения новых настроек '''
        global BINANCE_AMOUNT, t2, keep_running, BINANCE_PUB_TYPE, BINANCE_TRADE_TYPE, BINANCE_PAY_TYPES

        # Шорткаты
        _binance = self.binance_settings
        _bybit = self.bybit_settings
        _okex = self.okex_settings
        _huobi = self.huobi_settings

        # Binance
        BINANCE_AMOUNT = _binance['sum'].text()
        BINANCE_PUB_TYPE = _binance['publicator'].currentData()
        BINANCE_TRADE_TYPE = _binance['deal'].currentData()
        BINANCE_PAY_TYPES = _binance['pay_method'].currentData()

        # BYBIT
        global BYBIT_AMOUNT, BYBIT_TRADE_TYPE, BYBIT_PAY_TYPES, BYBIT_PUB_TYPE, t3
        BYBIT_AMOUNT = _bybit['sum'].text()
        BYBIT_TRADE_TYPE = _bybit['deal'].currentData()
        BYBIT_PAY_TYPES = _bybit['pay_method'].currentData()
        BYBIT_PUB_TYPE = _bybit['publicator'].currentData()

        # OKX
        global OKEX_AMOUNT, OKEX_TRADE_TYPE, OKEX_PAY_TYPES, OKEX_PUB_TYPE, t4
        OKEX_AMOUNT = _okex['sum'].text()
        OKEX_TRADE_TYPE = _okex['deal'].currentData()
        OKEX_PAY_TYPES = _okex['pay_method'].currentData()
        OKEX_PUB_TYPE = _okex['publicator'].currentData()

        # HUOBI
        global HUOBI_AMOUNT, HUOBI_TRADE_TYPE, HUOBI_PAY_TYPES, HUOBI_PUB_TYPE, t5
        HUOBI_AMOUNT = _huobi['sum'].text()
        HUOBI_TRADE_TYPE = _huobi['deal'].currentData()
        HUOBI_PAY_TYPES = _huobi['pay_method'].currentData()
        HUOBI_PUB_TYPE = _huobi['publicator'].currentData()

        # Сохраняем текущие значения параметров
        self.current_settings['trans_amount'] = BINANCE_AMOUNT
        self.current_settings['publisherType'] = BINANCE_PUB_TYPE
        self.current_settings['tradeType'] = BINANCE_TRADE_TYPE
        self.current_settings['payTypes'] = BINANCE_PAY_TYPES
        self.current_settings['amount'] = BYBIT_AMOUNT
        self.current_settings['side'] = BYBIT_TRADE_TYPE
        self.current_settings['payment'] = BYBIT_PAY_TYPES
        self.current_settings['merch'] = BYBIT_PUB_TYPE
        self.current_settings['amount_okx'] = OKEX_AMOUNT
        self.current_settings['side_okx'] = OKEX_TRADE_TYPE
        self.current_settings['payment_okx'] = OKEX_PAY_TYPES
        self.current_settings['merch_okx'] = OKEX_PUB_TYPE
        self.current_settings['amount_huobi'] = HUOBI_AMOUNT
        self.current_settings['side_huobi'] = HUOBI_TRADE_TYPE
        self.current_settings['payment_huobi'] = HUOBI_PAY_TYPES
        self.current_settings['merch_huobi'] = HUOBI_PUB_TYPE

        self.update_spinboxs()
        self.change_blocks_visible()
        self.toggle_settings()

    def set_timer(self):
        ''' Метод запуска таймера для обновления информации '''
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_values)
        self.timer.start(1000)

    def toggle_settings(self):
        ''' Метод показа/скрытия блока с натройками '''
        self.settings_open_anim = QPropertyAnimation(self.settings_container, b"maximumWidth")
        self.settings_open_anim.setStartValue(0)
        self.settings_open_anim.setEndValue(2000)
        self.settings_open_anim.setDuration(100)
        
        self.cards_close_anim = QPropertyAnimation(self.cards_container, b"maximumWidth")
        self.cards_close_anim.setStartValue(2000)
        self.cards_close_anim.setEndValue(0)
        self.cards_close_anim.setDuration(100)

        self.settings_close_anim = QPropertyAnimation(self.settings_container, b"maximumWidth")
        self.settings_close_anim.setStartValue(2000)
        self.settings_close_anim.setEndValue(0)
        self.settings_close_anim.setDuration(100)
        
        self.cards_open_anim = QPropertyAnimation(self.cards_container, b"maximumWidth")
        self.cards_open_anim.setStartValue(0)
        self.cards_open_anim.setEndValue(2000)
        self.cards_open_anim.setDuration(100)

        self.show_anim_group = QSequentialAnimationGroup()
        self.show_anim_group.addAnimation(self.cards_close_anim)
        self.show_anim_group.addAnimation(self.settings_open_anim)

        self.hide_anim_group = QSequentialAnimationGroup()
        self.hide_anim_group.addAnimation(self.settings_close_anim)
        self.hide_anim_group.addAnimation(self.cards_open_anim)

        if self.settings_is_hide:
            self.show_anim_group.start()
            self.settings_container.setMaximumHeight(10000)
        else:
            self.hide_anim_group.start()
            self.settings_container.setMaximumHeight(0)
        self.settings_is_hide = not (self.settings_is_hide)

    def closeEvent(self, event):
        ''' Метод, выполняющийся перед закрытием окна '''
        global threads, keep_running

        keep_running = False
        self.timer.stop()

        QCoreApplication.quit()
        [thread.stop() for thread in threads]
        event.accept()


# Запуск приложения
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    wnd = MainWindow()
    wnd.show()
    sys.exit(app.exec())
