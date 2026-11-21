from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

required_db_vars = [
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
]

missing_vars = [
    var for var in required_db_vars if not os.environ.get(var)
]

if missing_vars:
    raise ImproperlyConfigured(
        f"Missing database environment variables: {', '.join(missing_vars)}"
    )


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ["POSTGRES_HOST"],
        "PORT": os.environ["POSTGRES_PORT"],
        "CONN_MAX_AGE": 60,
    }
}
