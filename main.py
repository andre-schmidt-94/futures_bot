import logging
import time
import importlib.util
from tqdm import tqdm
from utils.env_loader import load_env_vars
from utils.logger_config import configure_logging
from utils.exceptions import BinanceException
from utils.file_monitor import FileChangeHandler
from binance_client import BinanceClient
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


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
    observer.start()

    client = BinanceClient(api_key, api_secret)

    orders = 0
    symbol = ''

    symbols = client.get_tickers_usdt()

    while True:
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

                logging.info("Removing orders that positions are gone")
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

        except BinanceException as exception:
            logging.error("[%s] %s, %s, %s", 
                        exception.method,
                        exception.status_code, 
                        exception.error_code, 
                        exception.error_message)
    
        observer.stop()
        print('Waiting 2 min')
        time.sleep(120)

    



if __name__ == "__main__":
    main()