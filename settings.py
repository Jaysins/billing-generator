# settings.py
"""
settings.py

The base settings file for the project. This file will be imported by any modules that require settings functionality.
All variables and paths are loaded up from the environmental variables setup by in the .env file in use.
"""

import os

from celery.schedules import crontab, schedule
from dotenv import load_dotenv

# import the necessary
# .env file based on what environment you are in
# The base folder will be the env folder at the root of the project
env = os.getenv("ENV", "dev")  # get environment

# Implementing staging and production bypass. Useful for kubernetes environment.
if env not in ["staging", "production"]:
    dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__name__)), "configs",
                               "{env}.env".format(env=env))  # determine .env path
    # Load settings variables using dotenv
    load_dotenv(verbose=True, dotenv_path=dotenv_path)

DEV_SETTINGS = False if env in ["production"] else True

MONGO_BASE = os.getenv("MONGO_BASE", "mongodb+srv")
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_USERNAME = os.getenv("MONGO_USERNAME", "")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_DATABASE = os.getenv("MONGO_DATABASE")
MONGO_DATABASE_TEST_PREFIX = os.getenv("MONGO_DATABASE_TEST_PREFIX", "test_")
MONGO_URI_PARAMS = os.getenv("MONGO_URI_PARAMS","")
M = '{username}:{password}@'.format(username=MONGO_USERNAME, password=MONGO_PASSWORD)
MONGO_CRED = "" if len(M) < 6 else M
DATABASE_URL = '{mongo_base}://{cred}{host}/{database}?{params}'.format(
    mongo_base=MONGO_BASE,
    cred=MONGO_CRED,
    host=MONGO_HOST,
    database=MONGO_DATABASE,
    params=MONGO_URI_PARAMS
)

REDIS_URL = os.getenv("REDIS_URL")
API_BASE = os.getenv("API_BASE", "")
AUTH_SOURCE = os.getenv("AUTH_SOURCE", "key_store")

