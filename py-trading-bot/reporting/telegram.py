0#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 12 14:09:14 2022

@author: maxime
"""
import os

from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.db.models.query import QuerySet

#from telegram.ext import CommandHandler
import logging
logger = logging.getLogger(__name__)
import vectorbtpro as vbt

from celery import shared_task
import sys

if sys.version_info.minor>=9:
    from zoneinfo import ZoneInfo
else:
    from backports.zoneinfo import ZoneInfo

from reporting.models import Report, Alert, ListOfActions

from orders.ib import retrieve_ib_pf, get_last_price, get_ratio, exit_order
from orders.models import Action, StockEx, Order, ActionCategory, pf_retrieve_all
from core import constants

from trading_bot.settings import _settings
from reporting import telegram_sub #actually it is the file from vbt, I have it separately if some changes are needed.

from datetime import time
''' Contains the logic for:
 - Telegram bot
 - Sending alert if the market price variation exceeds a certain threshold
 - Triggering the report writting at regular hour
 - Send message after each order
'''
logging.basicConfig(level=logging.INFO)  
    
def start():
    if settings.DEBUG: #
        with open('trading_bot/etc/TELEGRAM_TOKEN') as f:
            TELEGRAM_TOKEN = f.read().strip()
    else:
        TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN') 
        
   
    res=async_sched.delay(TELEGRAM_TOKEN)
    print("bot started, task id " + str(res.id))

@shared_task(bind=True)   
def async_sched(self,TELEGRAM_TOKEN): 
    #note: only serializable data can be sent to async task
    #TelegramBot without change here
    bot = telegram_sub.TelegramBot(token=TELEGRAM_TOKEN) #normally vbt.TelegramBot should be sufficient
    bot.start(in_background=True)
    MyScheduler(bot)

def stop(bot, sched):
    bot.stop()
    sched.stop()    

class MyScheduler():
    def __init__(self, telegram_bot,**kwargs):
        self.manager = vbt.ScheduleManager()
        self.telegram_bot=telegram_bot
        
        #Settings
        self.pf_check=_settings["PF_CHECK"]
        self.index_check=_settings["INDEX_CHECK"]
        self.report_17h=_settings["REPORT_17h"]
        self.report_22h=_settings["REPORT_22h"]
        self.heartbeat=_settings["HEARTBEAT"] # to test if telegram is working ok
        self.cleaning=True
        
        tz_Paris=ZoneInfo('Europe/Paris') #Berlin is as Paris
        tz_NY=ZoneInfo('US/Eastern') #does not seem to be at ease with multiple tz
                        
        if self.pf_check:
            self.manager.every(_settings["TIME_INTERVAL_CHECK"], 'minutes').do(self.check_pf)
            self.do_weekday(time(9,3,tzinfo=tz_Paris), self.check_pf, opening="9h")
            self.do_weekday(time(9,33,tzinfo=tz_NY), self.check_pf, opening="15h")
        if self.index_check:
            self.manager.every(_settings["TIME_INTERVAL_CHECK"], 'minutes').do(self.check_index)
            self.do_weekday(time(9,3,tzinfo=tz_Paris), self.check_index, opening="9h")
            self.do_weekday(time(9,33,tzinfo=tz_NY), self.check_index, opening="15h")       
        if self.report_17h: #round 15 min before closing
            self.do_weekday(time(17,15,tzinfo=tz_Paris),self.daily_report_17h)
        if self.report_22h: #round 15 min before closing
            self.do_weekday(time(15,45,tzinfo=tz_NY),self.daily_report_22h)
        if self.heartbeat:
            self.manager.every(10, 'seconds').do(self.heartbeat_f)
        if self.cleaning:
            self.do_weekday(time(16,2,tzinfo=tz_NY),self.cleaning_f)

        if (self.pf_check    or
            self.index_check or
            self.report_17h  or
            self.report_22h  or
            self.heartbeat):
            
            #the "background is created by celery"
            #OOTB vbt start_in_background does not seem to be compatible with django
            if not kwargs.get("test",False):
                self.manager.start() 
            self.telegram_bot.send_message_to_all( 
                                "Scheduler started in background, settings:"
                               +"\n pf " + str(self.pf_check) 
                               +"\n index " + str(self.index_check)
                               +"\n 17h " + str(self.report_17h)
                               +"\n 22h " + str(self.report_22h)
                               +"\n heartbeat " + str(self.heartbeat)
                               +"\n cleaning " + str(self.cleaning) 
                               )   

    #no trade the weekend
    def do_weekday(self, strh, f, **kwargs):
        self.manager.every('monday', strh).do(f, **kwargs)
        self.manager.every('tuesday', strh).do(f, **kwargs)
        self.manager.every('wednesday', strh).do(f, **kwargs)
        self.manager.every('thursday', strh).do(f, **kwargs)
        self.manager.every('friday', strh).do(f, **kwargs)
        
    def cleaning_f(self):
        alerts=Alert.objects.filter(active=True)
        for alert in alerts:
            alert.active=False
            alert.save()
        
    def check_change(self,ratio, action,short,**kwargs):
        try:
            symbols_opportunity=constants.INDEXES+constants.RAW
            now=timezone.now().time()

            alerting_reco=False
            alerting=False
            alarming=False
            opportunity=False
            opening=bool(kwargs.get("opening",False))
            stock_open=(now >action.stock_ex.opening_time and\
                        now <action.stock_ex.closing_time)
            
            if stock_open:
                if (short and ratio>_settings["ALERT_THRESHOLD"]) or (not short and ratio < -_settings["ALERT_THRESHOLD"]):
                    alerting=True
                    if (short and ratio>_settings["ALARM_THRESHOLD"]) or (not short and ratio<-_settings["ALARM_THRESHOLD"]):
                        alarming=True     
                    
                if (short and ratio>(_settings["ALERT_THRESHOLD"]-_settings["ALERT_HYST"])) or \
                    (not short and ratio < -(_settings["ALERT_THRESHOLD"]-_settings["ALERT_HYST"])):
                    alerting_reco=True    
                    
                if (action.symbol in symbols_opportunity and not short and ratio>_settings["ALERT_THRESHOLD"]):
                    alerting=True
                    opportunity=True
                    if ratio>_settings["ALARM_THRESHOLD"]:
                        alarming=True     
                
                c1 = Q(action=action)
                c2 = Q(active=True)
                #must be the same direction otherwise as the criterium depends on it
                c3 = Q(short=short) 
                c4 = Q(opportunity=opportunity)
                c5 = Q(opening=opening)
                
                alerts=Alert.objects.filter(c1 & c2 & c3 & c4 & c5)
                
                op_text=""
                if opportunity:
                    op_text="Opportunity "
                    
                this_alert=None
                if isinstance(alerts, QuerySet):
                    if len(alerts)>0:
                        this_alert=alerts[0]
               
                if alerting:
                    if this_alert is None:
                        alert=Alert(action=action,alarm=alarming, short=short,\
                                    trigger_date=timezone.now(),\
                                    opportunity=opportunity    )
                        alert.save()
                        
                        if opening:
                            op_text+="Opening "
                        self.telegram_bot.send_message_to_all(op_text+"Alert, action: "+ action.name +"\npresent variation: " + str(round(ratio,2)) + " %")
                        
                        if opening: #immediately recover
                            this_alert.active=False
                            this_alert.alarm=False
                            this_alert.recovery_date=timezone.now()
                            this_alert.save()
                    else:
                        if not this_alert.alarm and alarming:
                            this_alert.alarm=alarming
                            this_alert.save()
                           
                            self.telegram_bot.send_message_to_all(
                                op_text+"Alarm, action: "+ action.name +"\npresent variation: " + str(round(ratio,2)) + " %")
                else:
                    if this_alert is not None and alerting_reco==False:
                        this_alert.active=False
                        this_alert.alarm=False
                        this_alert.recovery_date=timezone.now()
                        
                        
                        this_alert.save()
                        self.telegram_bot.send_message_to_all( 
                                op_text+"Recovery, action: "+ action.name +"\npresent variation: " + str(round(ratio,2)) + " %")
                
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass

    def check_cours(self,actions, short,**kwargs):
      #  if symbols!=[]:
        try:
            for action in actions: #otherwise issue with NaN
                try:
                    #check ETF --> better to check the underlying
                        indexes=None
                        if action.category==ActionCategory.objects.get(short="ETFLONG"):
                            indexes=Action.objects.filter(etf_long=action)
                        elif action.category==ActionCategory.objects.get(short="ETFSHORT"):
                            indexes=Action.objects.filter(etf_short=action)
                       
                        if indexes is not None and len(indexes)>0:
                            action=indexes[0]
                except Exception as msg:
                     print("exception in check change ETF")
                     print(msg)
                     print(action.symbol)

                ratio=get_ratio(action,**kwargs)
                self.check_change(ratio, action,short,**kwargs)
                
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass   

    def check_index(self,**kwargs):
        try:
            print("check index")
            cat=ActionCategory.objects.get(short="IND")
            c3=Q(category=cat)
            if kwargs.get("opening")=="9h":
                stockEx1=StockEx.objects.get(name="Paris")
                stockEx2=StockEx.objects.get(name="XETRA")
                
                c1 = Q(stock_ex=stockEx1)
                c2 = Q(stock_ex=stockEx2)
                
                indexes = Action.objects.filter((c1|c2)&c3)
            elif kwargs.get("opening")=="15h":
                stockEx1=StockEx.objects.get(name="Nasdaq")
                c1 = Q(stock_ex=stockEx1)
                indexes = Action.objects.filter(c1&c3)
            else:
                indexes = Action.objects.filter(c3)

            self.check_cours(indexes, False,index=True,**kwargs)
            self.check_cours(indexes, True,index=True,**kwargs)
            
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass

    def check_pf(self,**kwargs):
        try:
            actions=pf_retrieve_all(**kwargs)
            actions_short=pf_retrieve_all(short=True,**kwargs)
            ib_pf, ib_pf_short=retrieve_ib_pf()
            
            actions.extend(x for x in ib_pf if x not in actions)
            actions_short.extend(x for x in ib_pf_short if x not in actions_short)
            
            if len(actions)>0:
                self.check_sl(actions)
                self.check_cours(actions, False,**kwargs)
        
            if len(actions_short)>0:
                self.check_cours(actions_short, True,**kwargs)
                
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass

    def check_sl(self,actions,**kwargs):
        for action in actions:
            c1 = Q(action=action)
            c2 = Q(active=True)
            order=Order.objects.filter(c1 & c2)
            
            if len(order)>0:
                if order[0].sl_threshold is not None:
                    cours_pres=get_last_price(action)
                    if cours_pres<order[0].sl_threshold:
                        exit_order(action.symbol,
                                   order[0].pf.strategy, 
                                   order[0].pf.strategy.stock_ex.name,
                                   False,
                                   **kwargs)
                        self.send_exit_msg(action.symbol,suffix="stop loss")

    def send_order(self,report):
        for auto in [False, True]:
            for entry in [False, True]:
                for short in [False, True]:
                    try:
                        ent_ex_symbols=ListOfActions.objects.get(report=report,auto=auto,entry=entry,short=short)
                        for a in ent_ex_symbols.actions.all():
                            self.send_entry_exit_msg(a.symbol,entry,short,auto) 
                    except:
                        pass

        if report.text:
             self.telegram_bot.send_message_to_all(report.text)       
        
    def daily_report_17h(self):
        try:
            print("writting daily report 17h")
            report1=Report()
            report1.save()

            st=report1.daily_report_action("Paris")
            if st is None:
                raise ValueError("The creation of the strategy failed, report creation interrupted")
                
            report1.presel(st,"Paris")
            report1.presel_wq(st,"Paris")
            self.send_order(report1)
            
            report2=Report()
            report2.save()            

            st=report2.daily_report_action("XETRA")
            if st is None:
                raise ValueError("The creation of the strategy failed, report creation interrupted")
                
            report2.presel(st,"XETRA")
            report2.presel_wq(st,"XETRA")
            self.send_order(report2)
            
            report3=Report()
            report3.save()    

            report3.daily_report_index(["^FCHI","^GDAXI"]) # "BZ=F" issue
            self.send_order(report3)

            self.telegram_bot.send_message_to_all("Daily report 17h ready")
            
        except ValueError as e:
            logger.error(e, stack_info=True, exc_info=True)  
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass
    
    def daily_report_22h(self):
        try:
            print("writting daily report 22h")
            report1=Report()
            report1.save()

            st=report1.daily_report_action("Nasdaq") 
            if st is None:
                raise ValueError("The creation of the strategy failed, report creation interrupted")
            
            report1.presel(st,"Nasdaq")
            report1.presel_wq(st,"Nasdaq")
            self.send_order(report1)
            
            for s in _settings["NYSE_SECTOR_TO_SCAN"]:  
                print("starting report " + s)
                report=Report()
                report.save()
            
                st=report.daily_report_action("NYSE",sec=s) 
                report.presel(st,"NYSE",sec=s)
                report.presel_wq(st,"NYSE",sec=s)
                self.send_order(report)
            
            report2=Report()
            report2.save()            
            report2.daily_report_index(["^IXIC"])
            self.send_order(report2)
             
            self.telegram_bot.send_message_to_all( 
                             "Daily report 22h ready")  
            
        except ValueError as e:
            logger.error(e, stack_info=True, exc_info=True)  
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass

    def send_entry_exit_msg(self,symbol,entry,short, auto):
        if auto:
            part1=""
            part2=""
        else:
            part1="Manual "
            part2="requested for "
        
        if entry:
            part1+="entry "
        else:
            part1+="exit "
            
        if short:
            part3=" short"
        else:
            part3=""
            
        self.telegram_bot.send_message_to_all(part1+part2+symbol + " "+ part3)
 
    #just check that bot is running
    def heartbeat_f(self):
        self.telegram_bot.send_message_to_all("Heart beat")



        
