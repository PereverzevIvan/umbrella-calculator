# Файл для проверки соединения с апи бирж

import requests
import json

url = 'https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search'
headers = {
    'accept': '*/*',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
    "geolocation": "RU",
    "userPreferredCurrency": "RUB_USD",
    "common_fiat": "RUB",
    "bnc-uuid": "27132151-a6ee-4c60-aabd-c939b2124467",
    "source": "organic",
    "Accept-Encoding": "gzip, deflate, br",
    "C2ctype": "c2c_merchant",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Content-Type": "application/json",
    "BNC_FV_KEY_T": "101-lbVMrO7uMkAXC22uBA%2B9bdGk2ixU0aUgEFg29a5CJohCNgAluY5lTe%2FCklxlxThVSQfWKGwawg0S1wVeDnmTlg%3D%3D-J6%2BUi3sruDSsWO9IPfmH%2BQ%3D%3D-e0",
    "lang": "ru",
    "Referer": "https://p2p.binance.com/ru/trade/all-payments/USDT?fiat=RUB",
}

params = {
    "asset": "USDT",
    "countries": [],
    "fiat": "RUB",
    "page": 1,
    "rows": 10,
    "payTypes": [],
    "proMerchantAds": False,
    "publisherType": None,
    "shieldMerchantAds": False,
    "tradeType": "BUY"
}

response = requests.post(url=url, headers=headers, json=params).json()
print(response)