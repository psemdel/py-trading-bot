#!/usr/bin/env bash
 cd bot
 
 redis-server & 
 python3 manage.py runserver & 
 sleep 15
 xdg-open http://localhost:8000/
 celery -A trading_bot worker -l info 
 && fg
 

 

