from dotenv import load_dotenv
import os

def load_env_vars():
    load_dotenv()

    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")

    return api_key, api_secret
