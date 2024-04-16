import logging
import time
import importlib.util
import strategies
import json
from tqdm import tqdm
from utils.env_loader import load_env_vars
from utils.logger_config import configure_logging
from utils.exceptions import BinanceException
from utils.file_monitor import FileChangeHandler
from binance_client import BinanceClient
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def run_strategies(klines):
    strategies_list = ['str', 'rsi', 'macd', 'ema']
    signals = []
    
    signals.append(strategies.ema200_50(klines))
    signals.append(strategies.str_signal(klines))
    signals.append(strategies.macd_ema(klines))
    signals.append(strategies.rsi_signal(klines))

    return signals

def check_parameter_change():
    spec = importlib.util.spec_from_file_location("parameters", "./parameters.py")
    parameters = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parameters)
    current_parameters = {
        "TP": parameters.TP,
        "SL": parameters.SL,
        "VOLUME": parameters.VOLUME,
        "LEVERAGE": parameters.LEVERAGE,
        "TYPE": parameters.TYPE,
        "QTY": parameters.QTY
    }
    logging.info("[parameters] %s", current_parameters)
    return parameters

def main():
    configure_logging()
    api_key, api_secret = load_env_vars()

    observer = Observer()
    observer.schedule(FileChangeHandler(), path=".", recursive=False)

    client = BinanceClient(api_key, api_secret)

    orders = 0
    symbol = ''

    symbols = client.get_tickers_usdt()
    observer.start()
    
    while True:
        parameters = check_parameter_change()
        
        balance = client.get_balance_usdt()
        time.sleep(1)
        if balance == None:
            logging.info('Cant connect to API. Check IP, restrictions or wait some time')
        if balance != None:
            logging.info("My balance is: %f USDT", balance)

            pos = []
            pos = client.get_pos()
            logging.info("You have %d opened positions: %s", len(pos), pos)

            logging.info("Removing orders that positions are closed")
            ord = []
            ord = client.check_orders()

            for elem in ord:
                if not elem in pos:
                    response = client.close_open_orders(elem)
                    logging.info("[%s] %s", elem, response)
            
            if len(pos) < parameters.QTY:
                with tqdm(total=len(symbols), desc="Processing symbols", unit="symbol") as pbar:
                    for elem in symbols:
                        pbar.update(1)

                        klines = client.klines(elem)

                        results = run_strategies(klines)
                        # logging.info("[%s] Results: %s", elem, results)

                        has_up, has_down = any(item == "up" for item in results), any(item == "down" for item in results)

                        if has_up and not has_down:
                            if elem != 'USDCUSDT' and not elem in pos and not elem in ord and elem != symbol:
                                logging.info("[%s] Found BUY signal: %s", elem, results)
                                mode = client.set_mode(elem, parameters.TYPE)
                                time.sleep(1)
                                leverage = client.set_leverage(elem, parameters.LEVERAGE)
                                time.sleep(1)
                                logging.info("[%s] Placing order", elem)
                                client.new_order(elem, 'buy', mode, leverage, parameters.VOLUME, parameters.QTY, parameters.TP, parameters.SL)
                                symbol = elem
                                order = True
                                pos = client.get_pos()
                                time.sleep(1)
                                ord = client.check_orders()
                                time.sleep(1)
                                time.sleep(10)
                        if has_down and not has_up:
                            if elem != 'USDCUSDT' and not elem in pos and not elem in ord and elem != symbol:
                                logging.info("[%s] Found SELL signal: %s", elem, results)
                                mode = client.set_mode(elem, parameters.TYPE)
                                time.sleep(1)
                                leverage = client.set_leverage(elem, parameters.LEVERAGE)
                                time.sleep(1)
                                logging.info("[%s] Placing order", elem)
                                client.new_order(elem, 'sell', mode, leverage, parameters.VOLUME, parameters.QTY, parameters.TP, parameters.SL)
                                symbol = elem
                                order = True
                                pos = client.get_pos()
                                time.sleep(1)
                                ord = client.check_orders()
                                time.sleep(1)
                        if has_up and has_down:
                            logging.info("[%s] has_up and has_down: %s", elem, results)
        wait_time = 30
        logging.info('Waiting %s seconds', wait_time)
        time.sleep(wait_time)


if __name__ == "__main__":
    main()