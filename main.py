
from utils.env_loader import load_env_vars
from utils.logger_config import configure_logging


def main():
    configure_logging()
    api_key, api_secret = load_env_vars()

    
    pass



if __name__ == "__main__":
    main()