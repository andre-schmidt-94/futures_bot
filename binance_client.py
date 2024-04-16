import logging
import time
import json
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
        
    def klines(self, symbol):
        try:
            resp = pd.DataFrame(self.client.klines(symbol, '15m'))
            resp = resp.iloc[:,:6]
            resp.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
            resp = resp.set_index('Time')
            resp.index = pd.to_datetime(resp.index, unit = 'ms')
            resp = resp.astype(float)
            return resp
        except ClientError as error:
            raise BinanceException(
                'klines', error.status_code, error.error_code, error.error_message
            ) from error

    def set_mode(self, symbol, type):
        try:
            response = self.client.change_margin_type(
                symbol=symbol, marginType=type, recvWindow=30000
            )
            return response
        except ClientError as error:
            logging.error("[set_mode] %s, %s, %s",
                        error.status_code, 
                        error.error_code, 
                        error.error_message)
        
    def set_leverage(self, symbol, level):
        try:
            response = self.client.change_leverage(
                symbol=symbol, leverage=level, recvWindow=30000 
            )
            return response
        except ClientError as error:
            raise BinanceException(
                'set_leverage', error.status_code, error.error_code, error.error_message
            ) from error
    
    # Price precision. BTC has 1, XRP has 4
    def get_price_precision(self, symbol):
        resp = self.client.exchange_info()['symbols']
        for elem in resp:
            if elem['symbol'] == symbol:
                return elem['pricePrecision']


    # Amount precision. BTC has3 , XRP has 1
    def get_qty_precision(self, symbol):
        resp = self.client.exchange_info()['symbols']
        for elem in resp:
            if elem['symbol'] == symbol:
                return elem['quantityPrecision']
            
    def new_order(self, symbol, side, mode, leverage, volume, qty, tp, sl):
        price = float(self.client.ticker_price(symbol)['price'])
        qty_precision = self.get_qty_precision(symbol)
        price_precision = self.get_price_precision(symbol)
        qty = round(volume/price, qty_precision)
        if side == 'buy':
            try:
                resp1 = self.client.new_order(symbol=symbol, side='BUY', type='LIMIT', quantity=qty, timeInForce='GTC', price=price, recvWindow=40000)
                # print(symbol, side, "placing order")
                logging.info(json.dumps(resp1))
                time.sleep(2)
                sl_price = round(price - price*sl, price_precision)
                resp2 = self.client.new_order(symbol=symbol, side='SELL', type='STOP_MARKET', quantity=qty, timeInForce='GTC', stopPrice=sl_price, recvWindow=40000)
                logging.info(json.dumps(resp2))
                time.sleep(2)
                tp_price = round(price + price * tp, price_precision)
                resp3 = self.client.new_order(symbol=symbol, side='SELL', type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce='GTC', stopPrice=tp_price, recvWindow=40000)
                logging.info(json.dumps(resp3))
            except ClientError as error:
                logging.error(
                    "[new_order] Found error. status: %s, error code: %s, error message: %s",
                        error.status_code, 
                        error.error_code, 
                        error.error_message)
        if side == 'sell':
            try:
                resp1 = self.client.new_order(symbol=symbol, side='SELL', type='LIMIT', quantity=qty, timeInForce='GTC', price=price, recvWindow=40000)
                # print(symbol, side, "placing order")
                logging.info(json.dumps(resp1))
                time.sleep(2)
                sl_price = round(price + price*sl, price_precision)
                resp2 = self.client.new_order(symbol=symbol, side='BUY', type='STOP_MARKET', quantity=qty, timeInForce='GTC', stopPrice=sl_price, recvWindow=40000)
                logging.info(json.dumps(resp2))
                time.sleep(2)
                tp_price = round(price - price * tp, price_precision)
                resp3 = self.client.new_order(symbol=symbol, side='BUY', type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce='GTC', stopPrice=tp_price, recvWindow=40000)
                logging.info(json.dumps(resp3))
            except ClientError as error:
                logging.error(
                    "[new_order] Found error. status: %s, error code: %s, error message: %s",
                        error.status_code, 
                        error.error_code, 
                        error.error_message)