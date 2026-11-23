import multiprocessing
import os

bind = "0.0.0.0:" + os.environ.get("PORT", "8000")
workers = int(os.environ.get("WEB_CONCURRENCY", min(multiprocessing.cpu_count() + 1, 4)))
timeout = int(os.environ.get("APP_GUNICORN_TIMEOUT", "120"))
preload_app = True  # REQUIRED: single create_app() call, shared SECRET_KEY
accesslog = "-"
errorlog = "-"
loglevel = "info"
