import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
graceful_timeout = 30
bind = "127.0.0.1:8765"
accesslog = "/var/log/roiify/gunicorn_access.log"
errorlog = "/var/log/roiify/gunicorn_error.log"
loglevel = "info"
pidfile = "/var/run/roiify/gunicorn.pid"
