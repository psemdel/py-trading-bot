#!/usr/bin/env bash

 redis-server & 
 python3 manage.py runserver & 
 sleep 20
 xdg-open http://localhost:8000/start_bot
 celery -A trading_bot worker -l info
 && fg
 

 

