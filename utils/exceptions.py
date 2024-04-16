

class BinanceException(Exception):
    def __init__(self, method,status_code, error_code, error_message):
        self.method = method
        self.status_code = status_code
        self.error_code = error_code
        self.error_message = error_message
        super().__init__(self.error_message)