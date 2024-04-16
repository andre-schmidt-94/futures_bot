import logging
from colorlog import ColoredFormatter
import re

# Define a function to strip ANSI escape codes
def strip_ansi_escape_codes(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def configure_logging(log_file_path="output/logs/app.log"):
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create a formatter with timestamp and colored output
    formatter = ColoredFormatter(
        "%(asctime)s %(log_color)s%(levelname)-8s%(reset)s %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )

    # Create a console handler and set the formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Create a file handler and set the formatter
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)

    # Add the console handler and file handler to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Define a custom filter to strip ANSI escape codes before writing to the file
    class StripAnsiFilter(logging.Filter):
        def filter(self, record):
            record.msg = strip_ansi_escape_codes(record.msg)
            return True

    # Add the custom filter to the file handler
    file_handler.addFilter(StripAnsiFilter())

# Example usage:
# configure_logging("output/logs/app.log")
# logging.debug("This is a debug message.")
# logging.info("This is an info message.")
# logging.warning("This is a warning message.")
# logging.error("This is an error message.")
# logging.critical("This is a critical message.")
