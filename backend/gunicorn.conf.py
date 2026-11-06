"""Gunicorn configuration for CodeSphere (gunicorn -c gunicorn.conf.py)."""
import multiprocessing
import os

# Nginx proxies to this address inside the Docker network.
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")

# Classic rule of thumb: (2 x CPU cores) + 1 worker processes.
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
# Threads let one worker wait on a sandbox container while serving others.
threads = int(os.environ.get("GUNICORN_THREADS", 2))
worker_class = "gthread"

# A submission compiles once and runs every test case in its own sandbox
# container, so allow long requests (Nginx proxy_read_timeout matches).
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 120))
graceful_timeout = 30
keepalive = 5

# Recycle workers periodically to contain memory leaks.
max_requests = 1000
max_requests_jitter = 100

# Log to stdout/stderr so `docker logs` / `docker compose logs` show them.
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
forwarded_allow_ips = "*"  # trust X-Forwarded-* from the Nginx container
