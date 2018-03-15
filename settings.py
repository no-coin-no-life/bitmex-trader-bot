from dotenv import load_dotenv

import os

app_home = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "./"))
env_path = os.path.join(app_home, ".env")

load_dotenv(dotenv_path=env_path)