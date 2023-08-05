import multiprocessing

bind = "0.0.0.0:9696"
workers = multiprocessing.cpu_count() * 2 + 1 # Number of workers that can handle a request
threads = multiprocessing.cpu_count() * 2    
worker_class = "gthread"
wsgi_app = "app:app"