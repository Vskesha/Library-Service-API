import os

from dotenv import load_dotenv

from config.settings.base import *  # noqa: F403, F405

load_dotenv()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost",
).split(",")

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

IN_DOCKER = os.environ.get("IN_DOCKER", "False").lower() == "true"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ.get("POSTGRES_HOST") if IN_DOCKER else "localhost",
        "PORT": os.environ["POSTGRES_PORT"],
    }
}

if "DEFAULT_THROTTLE_RATES" in REST_FRAMEWORK:
    del REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
