import logging
import time
import importlib.util
import threading
import strategies
from queue import Queue
from tqdm import tqdm
from utils.env_loader import load_env_vars
from utils.logger_config import configure_logging
from utils.exceptions import BinanceException
from utils.file_monitor import FileChangeHandler
from binance_client import BinanceClient
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def run_strategy(klines, strategy, result_queue):
    # logging.info("New Thread with strategy %s", strategy)

    if strategy == 'ema':
        signal = strategies.ema200_50(klines)
    if strategy == 'str':
        signal = strategies.str_signal(klines)
    if strategy == 'macd':
        signal = strategies.macd_ema(klines)
    if strategy == 'rsi':
        signal = strategies.rsi_signal(klines)
    
    result_queue.put({
        "strategy": strategy,
        "signal": signal
    })

def check_parameter_change():
    spec = importlib.util.spec_from_file_location("parameters", "./parameters.py")
    parameters = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parameters)
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

    while True:
        observer.start()
        try:
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
                        for symbol in symbols:
                            pbar.update(1)

                            klines = client.klines(symbol)
                            result_queue = Queue()
                            threads = []
                            strategies = ['str', 'rsi', 'macd', 'ema']

                            for strategy in strategies:
                                thread = threading.Thread(target=run_strategy, args=(klines, strategy, result_queue))
                                thread.start()
                                threads.append(thread)
                            
                            for thread in threads:
                                thread.join()

                            results = []
                            while not result_queue.empty():
                                results.append(result_queue.get())
                            # logging.info("[%s] Results: %s", symbol, results)

                            has_up, has_down = any(item == "up" for item in results), any(item == "down" for item in results)

                            if has_up and not has_down:
                                logging.info("[%s] has_up: %s", symbol, results)
                                pass
                            if has_down and not has_up:
                                logging.info("[%s] has_down: %s", symbol, results)
                                pass
                            if has_up and has_down:
                                logging.info("[%s] has_up and has_down: %s", symbol, results)
                                pass

        except BinanceException as exception:
            logging.error("[%s] %s, %s, %s", 
                        exception.method,
                        exception.status_code, 
                        exception.error_code, 
                        exception.error_message)
    
        observer.stop()
        wait_time = 30
        logging.info('Waiting %s seconds', wait_time)
        time.sleep(wait_time)


if __name__ == "__main__":
    main()