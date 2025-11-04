#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  1 13:07:46 2025

@author: maxime
"""

import vectorbtpro as vbt
import logging
import asyncio
import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

with open('../trading_bot/etc/TELEGRAM_TOKEN') as f:
    TELEGRAM_TOKEN = f.read().strip()

    
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
res=requests.get(url).json()

if res['ok']:
     chat_id=res['result'][0]['message']['chat']['id']
else:
     print("Chat id not found. Did you type /start in your telegram bot?")

telegram_bot = vbt.TelegramBot(token=TELEGRAM_TOKEN)
telegram_bot.chat_ids.add(chat_id)
asyncio.run(telegram_bot.send_message_to_all("test"))