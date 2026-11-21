from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

SQLITE_PATH = os.environ.get("SQLITE_PATH")

if not SQLITE_PATH:
    raise ImproperlyConfigured("SQLITE_PATH environment variable is required.")

DATABASES["default"]["NAME"] = SQLITE_PATH