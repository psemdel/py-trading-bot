#!/bin/bash

#start your venv
source <your path>/Anaconda/bin/activate
conda activate <venv name>

#start the rest
 redis-server & 
 python manage.py runserver & 
 sleep 50
 xdg-open http://localhost:8000/start_bot
 celery -A trading_bot worker -l info
 && fg
 


