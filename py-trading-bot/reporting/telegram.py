0#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 12 14:09:14 2022

@author: maxime
"""
import os
import numbers

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
from orders.models import Action, StockEx, Order, ActionCategory, Job,\
                          pf_retrieve_all,exchange_to_index_symbol,\
                          get_exchange_actions   
                 
from core import constants, presel

from trading_bot.settings import _settings
from reporting import telegram_sub #actually it is the file from vbt, I have it separately if some changes are needed.

from datetime import time, datetime, timedelta
'''
Contains the logic for:
 - Telegram bot
 - Sending alert if the market price variation exceeds a certain threshold
 - Triggering the report writting at regular hour
 - Send message after each order
'''
logging.basicConfig(level=logging.INFO)  

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)

if __version_info__ >= (20, 0, 0, "alpha", 1):
    raise RuntimeError(f"This example is not compatible with your current PTB version {TG_VER}")

'''
Start the bot in the background
'''    
def start():
    if settings.DEBUG: #
        with open('trading_bot/etc/TELEGRAM_TOKEN') as f:
            TELEGRAM_TOKEN = f.read().strip()
    else:
        TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN') 

    res=async_sched.delay(TELEGRAM_TOKEN)
    print("bot started, task id " + str(res.id))

@shared_task(bind=True)   
def async_sched(self,
                TELEGRAM_TOKEN: str=None
                ): 
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
        '''
        The scheduler contains at the same time the job scheduling and the telegram bot
        '''
        self.manager = vbt.ScheduleManager()
        self.telegram_bot=telegram_bot
        
        #Settings
        self.pf_check=_settings["PF_CHECK"]
        self.index_check=_settings["INDEX_CHECK"]
        self.report_17h=_settings["REPORT_17h"]
        self.report_22h=_settings["REPORT_22h"]
        self.heartbeat=_settings["HEARTBEAT"] # to test if telegram is working ok
        self.heartbeat_ib=_settings["HEARTBEAT_IB"]
        self.update_slow =_settings["UPDATE_SLOW_STRAT"]
        self.cleaning=True
        
        tz_Paris=ZoneInfo('Europe/Paris') #Berlin is as Paris
        tz_NY=ZoneInfo('US/Eastern') #does not seem to be at ease with multiple tz
                        
        if self.pf_check:
            self.manager.every(_settings["TIME_INTERVAL_CHECK"], 'minutes').do(self.check_pf)
            self.do_weekday(time(9,35,tzinfo=tz_Paris), self.check_pf, opening="9h")
            self.do_weekday(time(9,35,tzinfo=tz_NY), self.check_pf, opening="15h")
        if self.index_check:
            self.manager.every(_settings["TIME_INTERVAL_CHECK"], 'minutes').do(self.check_index)
            self.do_weekday(time(9,35,tzinfo=tz_Paris), self.check_index, opening="9h")
            self.do_weekday(time(9,35,tzinfo=tz_NY), self.check_index, opening="15h")       
        if self.report_17h: #round 15 min before closing
            self.do_weekday(time(17,15,tzinfo=tz_Paris),self.daily_report,short_name="17h",key="17h_stock_exchanges")
        if self.report_22h: #round 15 min before closing
            self.do_weekday(time(15,45,tzinfo=tz_NY),self.daily_report,short_name="22h",key="22h_stock_exchanges")
        if self.heartbeat:
            self.manager.every(10, 'seconds').do(self.heartbeat_f)
        if self.heartbeat_ib:
            self.manager.every(10, 'seconds').do(self.heartbeat_ib_f)
        if self.cleaning:
            self.do_weekday(time(16,2,tzinfo=tz_NY),self.cleaning_f)
        if self.update_slow:
            self.do_weekday(time(10,00,tzinfo=tz_Paris), self.update_slow_strat) #performed away from the opening

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
                           +"\n heartbeat IB " + str(self.heartbeat_ib)
                           +"\n cleaning " + str(self.cleaning) 
                           )   

    
    def do_weekday(self, 
                   strh: str, 
                   f, #function
                   **kwargs):
        '''
        Schedule a job for the working days, as there is no trade the weekend
        '''
        self.manager.every('monday', strh).do(f, **kwargs)
        self.manager.every('tuesday', strh).do(f, **kwargs)
        self.manager.every('wednesday', strh).do(f, **kwargs)
        self.manager.every('thursday', strh).do(f, **kwargs)
        self.manager.every('friday', strh).do(f, **kwargs)

    def cleaning_f(self):
        '''
        Deactivate the alert at the end of the day
        '''
        cleaning_sub()
    
    def check_stock_ex_open(self,action: Action)-> bool:
        '''
        Check if the stock exchange is open
        '''
        tz=ZoneInfo(action.stock_ex.timezone)
        now=datetime.now(tz).time() #wil compare the time in the local time to opening_time, also in the local time
        
        return (now >action.stock_ex.opening_time and\
                    now <action.stock_ex.closing_time)
    
    def check_change(self,
                     ratio: numbers.Number, 
                     action: Action,
                     short: bool,
                     opening: bool=False,
                     **kwargs):
        '''
        Check if the price variation for a product is within predefined borders
        Create an alert if it is not the case
        
        Arguments
       	----------
           ratio: present price variation in percent
           action: product concerned
           short: if the product is presently in a short direction
           opening: test at stock exchange opening (need to compare with the day before then)
        '''
        try:
            symbols_opportunity=constants.INDEXES+constants.RAW

            alerting_reco=False
            alerting=False
            alarming=False
            opportunity=False

            if self.check_stock_ex_open(action):
                if (short and ratio>_settings["ALERT_THRESHOLD"]) or (not short and ratio < -_settings["ALERT_THRESHOLD"]):
                    alerting=True
                    if (short and ratio>_settings["ALARM_THRESHOLD"]) or (not short and ratio<-_settings["ALARM_THRESHOLD"]):
                        alarming=True     
                    
                if (short and ratio<(_settings["ALERT_THRESHOLD"]-_settings["ALERT_HYST"])) or \
                    (not short and ratio > -(_settings["ALERT_THRESHOLD"]-_settings["ALERT_HYST"])):
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
                
                alerts=Alert.objects.filter(c1 & c2 & c3 & c4)
                
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
                        
                    else:
                        if not this_alert.alarm and alarming:
                            this_alert.alarm=alarming
                            this_alert.save()
                           
                            self.telegram_bot.send_message_to_all(
                                op_text+"Alarm, action: "+ action.name +"\npresent variation: " + str(round(ratio,2)) + " %")
                else:
                    if this_alert is not None and alerting_reco:
                        this_alert.active=False
                        this_alert.alarm=False
                        this_alert.recovery_date=timezone.now()
                        
                        this_alert.save()
                        self.telegram_bot.send_message_to_all( 
                                op_text+"Recovery, action: "+ action.name +"\npresent variation: " + str(round(ratio,2)) + " %")
                
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass

    def check_cours(self,
                    actions: list, 
                    short: bool,
                    **kwargs):
        '''
        Preliminary steps for verification of the price variation
        Replace the etf through their respective index    
        
        Arguments
       	----------
           actions: list of action to be checked for price variation
           short: if the products are presently in a short direction
        '''
        try:
            for action in actions: #otherwise issue with NaN
                #check ETF --> better to check the underlying
                indexes=None
                if action.category==ActionCategory.objects.get(short="ETFLONG"):
                    indexes=Action.objects.filter(etf_long=action)
                elif action.category==ActionCategory.objects.get(short="ETFSHORT"):
                    indexes=Action.objects.filter(etf_short=action)
               
                if indexes is not None and len(indexes)>0:
                    action=indexes[0]

                ratio=get_ratio(action,**kwargs)
                self.check_change(ratio, action,short,**kwargs)
                
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass   

    def check_index(self,
                    opening: str=None,
                    **kwargs):
        '''
        Check price variation for indexes , so independently from their belonging or not 
        
        Arguments
       	----------
           opening: test at stock exchange opening (need to compare with the day before then)
        '''
        try:
            print("check index")
            cat=ActionCategory.objects.get(short="IND")
            c3=Q(category=cat)
            if opening=="9h":
                c=None
                for exchange in _settings["17h_stock_exchanges"]:
                    c1 = Q(stock_ex=StockEx.objects.get(name=exchange))
                    if c is None:
                        c=c1
                    else:
                        c=c|c1
                indexes = Action.objects.filter(c&c3)
            elif opening=="15h":
                c=None
                for exchange in _settings["22h_stock_exchanges"]:
                    c1 = Q(stock_ex=StockEx.objects.get(name=exchange))
                    if c is None:
                        c=c1
                    else:
                        c=c|c1
                indexes = Action.objects.filter(c&c3)
            else:
                indexes = Action.objects.filter(c3)

            self.check_cours(indexes, False,index=True,**kwargs)
            self.check_cours(indexes, True,index=True,**kwargs)
            
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass
        
    def check_pf(self,**kwargs):
        '''
        Check price variation for portofolio, so products that we own
        ''' 
        try:
            actions=pf_retrieve_all(**kwargs)
            actions_short=pf_retrieve_all(short=True,**kwargs)
            ib_pf, ib_pf_short=retrieve_ib_pf()
            
            if ib_pf is not None:
                actions.extend(x for x in ib_pf if x not in actions)
                actions_short.extend(x for x in ib_pf_short if x not in actions_short)
            
            if len(actions)>0:
                self.check_sl(actions)
                self.check_cours(actions, False,**kwargs)
        
            if len(actions_short)>0:
                self.check_sl(actions_short)
                self.check_cours(actions_short, True,**kwargs)
                
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass

    def check_sl(self,
                 actions: list,
                 **kwargs):
        '''
        Check price variation for product that have a stop loss
        Trigger the selling if the limit is reached
        
        Arguments
       	----------
           actions: list of action to be checked for price variation
        '''  
        for action in actions:
            if self.check_stock_ex_open(action):
                c1 = Q(action=action)
                c2 = Q(active=True)
                order=Order.objects.filter(c1 & c2)
                auto=True
                today=timezone.now().strftime('%Y-%m-%d')
                
                if len(order)>0:
                    o=order[0]
                    e=o.entering_date.strftime('%Y-%m-%d')
                    if e<today: #avoid exiting order performed today
                        if o.sl_threshold is not None:
                            cours_pres=get_last_price(action)
                            if (not o.short and cours_pres<o.sl_threshold) or\
                            (o.short and cours_pres>o.sl_threshold):
                                
                                ex, auto=exit_order(action.symbol,
                                           o.pf.strategy.name, 
                                           o.pf.stock_ex.name,
                                           o.short,
                                           auto,
                                           **kwargs)
                                if ex:
                                    self.send_entry_exit_msg(action.symbol,False,False,auto,suffix="stop loss") 
                        
                        if o.daily_sl_threshold is not None:
                            ratio=get_ratio(action)
                            
                            if (not o.short and ratio<-o.daily_sl_threshold*100) or\
                            (o.short and ratio>o.daily_sl_threshold*100):
    
                                ex, auto=exit_order(action.symbol,
                                           o.pf.strategy.name, 
                                           o.pf.stock_ex.name,
                                           o.short,
                                           auto,
                                           **kwargs)
                                if ex:
                                    self.send_entry_exit_msg(action.symbol,False,False,auto,suffix="daily stop loss")                        
           
    def send_order(self,
                   report: Report
                   ):
        '''
        Send Telegram message if orders have been performed
        
        Arguments
       	----------
           report: report for which the calculation happened
        '''   
        for auto in [False, True]:
            for entry in [False, True]:
                for short in [False, True]:
                    try:
                        ent_ex_symbols=ListOfActions.objects.get(report=report,auto=auto,entry=entry,short=short)
                        for a in ent_ex_symbols.actions.all():
                            self.send_entry_exit_msg(a.symbol,entry,short,auto) 
                        self.telegram_bot.send_message_to_all(ent_ex_symbols.text)
                    except:
                        pass

        if report.text:
             self.telegram_bot.send_message_to_all(report.text)       
    
    def daily_report_sub(self,exchange:str,**kwargs):
        '''
        See daily report
        '''        
        report1=Report()
        report1.save()
        
        st=report1.daily_report(exchange=exchange,**kwargs)
        if st is None:
            raise ValueError("The creation of the strategy failed, report creation interrupted")
            
        report1.presel(st,exchange,**kwargs)
        report1.presel_wq(st,exchange,**kwargs)
        self.send_order(report1)
        
    def daily_report_index_sub(self,indexes: list):
        '''
        See daily report
        '''
        report3=Report()
        report3.save()    

        report3.daily_report(symbols=indexes,it_is_index=True) # "BZ=F" issue
        self.send_order(report3)
        
    def daily_report(self, 
                     short_name: str=None,
                     key: str=None,
                     **kwargs):
        '''
        Write report for an exchange and/or sector
        
        Arguments
       	----------
           report: report for which the calculation happened
        '''  
        try:
            print("writting daily report "+short_name)
            for exchange in _settings[key]:
                if exchange=="NYSE":
                    for s in _settings["NYSE_SECTOR_TO_SCAN"]:  
                        print("starting report " + s)
                        self.daily_report_sub("NYSE",sec=s)
                else:
                    self.daily_report_sub(exchange)

            indexes=[exchange_to_index_symbol(exchange)[1] for exchange in _settings[key]]
            self.daily_report_index_sub(indexes)
            
            self.telegram_bot.send_message_to_all("Daily report "+short_name+" ready")
            
        except ValueError as e:
            logger.error(e, stack_info=True, exc_info=True)  
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass

    def send_entry_exit_msg(self,
                            symbol:str,
                            entry: bool,
                            short: bool, 
                            auto: bool,
                            suffix: str=""
                            ):
        '''
        Define the message for the Telegram depending on the arguments
        
        Arguments
       	----------
           symbol: YF ticker of the product for which the order was performed
           entry: was it an entry or an exit
           short: direction of the order
           auto: was the order automatic or not
           suffix: some text that can be chosen
        '''  
        self.telegram_bot.send_message_to_all(send_entry_exit_txt(symbol, entry, short, auto, suffix=suffix))

    def heartbeat_f(self):
        '''
        Function to test if the bot is running
        '''
        self.telegram_bot.send_message_to_all("Heart beat")

    def heartbeat_ib_f(self):
        '''
        Function to test if the connection with IB is running
        '''
        a=Action.objects.get(symbol="AAPL")
        t=get_last_price(a)
        self.telegram_bot.send_message_to_all("Apple current price: " + str(t))

    def update_slow_strat(self):
        '''
        Update slow strategy candidates at regular periods
        '''
        jobs=Job.objects.all()
        today=timezone.now()
        
        for j in jobs:
            if today>(timedelta(days=j.frequency_days)+j.last_execution):
                actualize_job(j.strategy.name, j.period_year, j.stock_ex.name)
                j.last_execution=today
                j.save()
       
def actualize_job(
        strategy: str, 
        period_year: numbers.Number, 
        exchange:str
        ):
    '''
    Perform a job with long intervals between two executions
    ''' 
    use_IB, actions=get_exchange_actions(exchange)
    pr=presel.name_to_presel(
        constants.strategy_to_presel[strategy], 
        str(period_year)+"y",
        prd=True, 
        actions=actions,
        use_IB=use_IB,
        exchange=exchange) 
    pr.actualize()

def send_entry_exit_txt(
                symbol:str,
                entry: bool,
                short: bool, 
                auto: bool,
                suffix: str="",
                ) -> str:
    '''
    Define the message for the Telegram depending on the arguments
    
    Arguments
   	----------
       symbol: YF ticker of the product for which the order was performed
       entry: was it an entry or an exit
       short: direction of the order
       auto: was the order automatic or not
       suffix: some text that can be chosen
    '''  
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
    return part1+part2+symbol + " "+ part3+" " +suffix

def cleaning_sub():
    alerts=Alert.objects.filter(active=True)
    for alert in alerts:
        alert.active=False
        alert.save()
    
    