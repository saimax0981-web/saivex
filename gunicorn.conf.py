import multiprocessing
import os

port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"

# Keep this light for free/small servers.
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "180"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))

worker_class = "gthread"
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")

preload_app = False
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", "100"))
