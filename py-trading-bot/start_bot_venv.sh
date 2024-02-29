#!/bin/bash

source /mnt/Gros/Progra/Anaconda/bin/activate PyTradingBot39 
 redis-server & 
 python3 manage.py runserver & 
 sleep 50
 xdg-open http://localhost:8000/start_bot
 celery -A trading_bot worker -l info
 && fg
 


