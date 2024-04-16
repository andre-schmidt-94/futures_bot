import logging
from binance.um_futures import UMFutures
from binance.error import ClientError
from utils.exceptions import BinanceException
import pandas as pd

class BinanceClient:
    def __init__(self, api_key, api_secret):
        self.client = UMFutures(key = api_key, secret=api_secret)

    def get_tickers_usdt(self):
        tickers = []
        resp = self.client.ticker_price()
        for elem in resp:
            if 'USDT' in elem['symbol']:
                tickers.append(elem['symbol'])
        return tickers
    
    def get_balance_usdt(self):
        try:
            response = self.client.balance(recvWindow=30000)
            for elem in response:
                if elem['asset'] == 'USDT':
                    return float(elem['balance'])

        except ClientError as error:
            raise BinanceException(
                'get_balance_usdt', error.status_code, error.error_code, error.error_message
            ) from error
        
    def get_pos(self):
        try:
            resp = self.client.get_position_risk(recvWindow=30000)
            pos = []
            for elem in resp:
                if float(elem['positionAmt']) != 0:
                    pos.append(elem['symbol'])
            return pos
        except ClientError as error:
            raise BinanceException(
                'get_pos', error.status_code, error.error_code, error.error_message
            ) from error
        
    def check_orders(self):
        try:
            response = self.client.get_orders(recvWindow=30000)
            sym = []
            for elem in response:
                sym.append(elem['symbol'])
            return sym
        except ClientError as error:
            raise BinanceException(
                'check_orders', error.status_code, error.error_code, error.error_message
            ) from error
        
    def close_open_orders(self, symbol):
        try:
            response = self.client.cancel_open_orders(symbol=symbol, recvWindow=30000)
            return response
        except ClientError as error:
            raise BinanceException(
                'close_open_orders', error.status_code, error.error_code, error.error_message
            ) from error