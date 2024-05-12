#!/usr/bin/env python3
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

from reporting.models import Report, Alert, OrderExecutionMsg 
from telegram.ext import CommandHandler

from orders.ib import actualize_ss, get_last_price, get_ratio, get_VIX, update_VIX
from orders.models import Action, Strategy, StockEx, Order, ActionCategory, Job,\
                          pf_retrieve_all,exchange_to_index_symbol,\
                          get_exchange_actions, action_to_short, ActionSector,\
                          filter_intro_action
                 
from core import caller, data_manager

from trading_bot.settings import _settings
from reporting import telegram_sub #actually it is the file from vbt, I have it separately if some changes are needed.

from datetime import time, datetime, timedelta, date
'''
This file contains the logic for:
 - Telegram bot
 - Sending alert if the market price variation exceeds a certain threshold
 - Triggering the report writting at regular hour
 - Send message after each order
'''
logging.basicConfig(level=logging.INFO)  

class TelegramBotCustom(telegram_sub.TelegramBot):
    def __init__(self, giphy_kwargs= None, **kwargs) -> None:
        super().__init__(giphy_kwargs=giphy_kwargs,**kwargs)
            
    @property
    def custom_handlers(self):
        return (CommandHandler('test', self.send_message_to_all("test")),)

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
    bot=TelegramBotCustom(token=TELEGRAM_TOKEN)
    #bot = telegram_sub.TelegramBot(token=TELEGRAM_TOKEN) #normally vbt.TelegramBot should be sufficient
    bot.start(in_background=True)
    MyScheduler(bot)
    
def stop(bot, sched):
    bot.stop()
    sched.stop()    

class MyScheduler():
    def __init__(self, telegram_bot,**kwargs):
        '''
        The scheduler contains at the same time the job scheduling and the telegram bot
        
        Arguments
       	----------
           telegram_bot: instance of vbt TelegramBot
        '''
        self.manager = vbt.ScheduleManager()
        self.telegram_bot=telegram_bot
        #Settings
        self.update_ss=True
        self.cleaning=True
        
        for s_ex in StockEx.objects.all():
            start_check_time=self.shift_time(s_ex.opening_time,_settings["OPENING_CHECK_MINUTE_SHIFT"],s_ex.timezone) #perform the check 5 min after opening
            if _settings["PF_CHECK"]:
                self.do_weekday(start_check_time, self.check_pf, s_ex=s_ex, opening=True)
            if _settings["INDEX_CHECK"]:
                self.do_weekday(start_check_time, self.check_pf, it_is_index=True,s_ex=s_ex, opening=True)
            if _settings["REPORT"] and s_ex.calc_report:
                report_time=self.shift_time(s_ex.closing_time,-_settings["DAILY_REPORT_MINUTE_SHIFT"],s_ex.timezone) #write report 15 min before closing, so we have 15 min to calculate and pass the orders
                self.do_weekday(report_time,self.daily_report,s_ex=s_ex) 
            if _settings["INTRADAY"]:
                self.manager.every(_settings["TIME_INTERVAL_INTRADAY"], 'minutes').do(self.daily_report,s_ex=s_ex,intraday=True)
            if _settings["CHECK_DELISTED"]:
                report_time=self.shift_time(s_ex.closing_time,-(_settings["DAILY_REPORT_MINUTE_SHIFT"]+5),s_ex.timezone) #5 minutes before writting report
                self.do_weekday(report_time,self.check_nan,s_ex=s_ex) 
                
        if _settings["PF_CHECK"]:
            self.manager.every(_settings["TIME_INTERVAL_CHECK"], 'minutes').do(self.check_pf)
        if _settings["INDEX_CHECK"]:
            self.manager.every(_settings["TIME_INTERVAL_CHECK"], 'minutes').do(self.check_pf,it_is_index=True)
        if _settings["CHECK_VIX"]:
            self.manager.every(_settings["TIME_INTERVAL_CHECK"], 'minutes').do(self.check_VIX)
            
        if _settings["HEARTBEAT"]: # to test if telegram is working ok
            self.manager.every(10, 'seconds').do(self.heartbeat_f)
        if _settings["HEARTBEAT_IB"]:
            self.manager.every(10, 'seconds').do(self.heartbeat_ib_f)
        if self.cleaning:
            self.do_weekday(time(16,2,tzinfo=ZoneInfo('US/Eastern')),self.cleaning_f) #after end of the day
        if _settings["UPDATE_SLOW_STRAT"]:
            self.do_weekday(time(10,00,tzinfo=ZoneInfo('Europe/Paris')), self.update_slow_strat) #performed away from the opening
        if self.update_ss:
            self.manager.every(_settings["TIME_INTERVAL_UPDATE"], 'minutes').do(actualize_ss)

        #the "background is created by celery"
        #OOTB vbt start_in_background does not seem to be compatible with django
        if not kwargs.get("test",False):
            self.manager.start() 
        self.telegram_bot.send_message_to_all("Scheduler started in background")   
        
    def do_weekday(self, 
                   strh: str, 
                   f,
                   **kwargs):
        '''
        Schedule a job for the working days, as there is no trade the weekend
        
        Arguments
       	----------
           strh: time in the day when it should be performed
           f: function to be performed
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

    def check_stock_ex_open_from_action(self,action: Action)-> bool:
        '''
        Check if the stock exchange is open
        
        Arguments
       	----------
           action: product concerned
        '''
        return self.check_stock_ex_open(action.stock_ex)

    def check_stock_ex_open(self,s_ex: StockEx)-> bool:
        '''
        Check if the stock exchange is open
        
        Arguments
       	----------
           s_ex: stock exchange
        '''
        if s_ex is None:
            return True
        else:
            tz=ZoneInfo(s_ex.timezone)
            now=datetime.now(tz).time() #wil compare the time in the local time to opening_time, also in the local time
            
            return (now >s_ex.opening_time and now <s_ex.closing_time)
            
    def check_change(self,
                     ratio: numbers.Number, 
                     action: Action,
                     short: bool,
                     opening: bool=False,
                     opportunity: bool=False
                     ):
        '''
        Check if the price variation for a product is within predefined borders
        Create an alert if it is not the case
        
        Arguments
       	----------
           ratio: present price variation in percent
           action: product concerned
           short: if the product is presently in a short direction
           opening: test at stock exchange opening (need to compare with the day before then)
           opportunity: also alert when there is an opportunity
        '''
        try:
            alerting_reco=False
            alerting=False
            alarming=False
            opportunity=False
            if ratio is None:
                print("ratio is None for "+action.symbol)

            if self.check_stock_ex_open_from_action(action) and ratio is not None:
                if (short and ratio>_settings["ALERT_THRESHOLD"]) or (not short and ratio < -_settings["ALERT_THRESHOLD"]):
                    alerting=True
                    if (short and ratio>_settings["ALARM_THRESHOLD"]) or (not short and ratio<-_settings["ALARM_THRESHOLD"]):
                        alarming=True     
                    
                if (short and ratio<(_settings["ALERT_THRESHOLD"]-_settings["ALERT_HYST"])) or \
                    (not short and ratio > -(_settings["ALERT_THRESHOLD"]-_settings["ALERT_HYST"])):
                    alerting_reco=True    
                    
                if (opportunity and not short and ratio>_settings["ALERT_THRESHOLD"]):
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
                    both:bool=False,
                    opening: bool=False,
                    ):
        '''
        Preliminary steps for verification of the price variation
        Replace the etf through their respective index    
        
        Arguments
       	----------
           actions: list of action to be checked for price variation
        '''
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

                ratio=get_ratio(action)
                short=action_to_short(action)
                
                self.check_change(ratio, action,short,opening=opening, opportunity=both)

        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass           
     
    def check_pf(
            self,
            opening: bool=False,
            s_ex: StockEx=None,
            it_is_index:bool=False
            ):
        '''
        Check price variation for portofolio, so products that we own
        
        Arguments
       	----------
           opening: test at stock exchange opening (need to compare with the day before then)
           s_ex: stock exchange from which the stocks need to be covered
        ''' 
        try:
            actions=pf_retrieve_all(s_ex=s_ex,opening=opening)
            if len(actions)>0:
                self.check_sl(actions)
                self.check_cours(actions, both=it_is_index, opening=opening)
                
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass        

    def check_sl(self,
                 actions: list,
                 ):
        '''
        Check price variation for product that have a stop loss
        Trigger the selling if the limit is reached
        
        Arguments
       	----------
           actions: list of action to be checked for price variation
        '''  
        for action in actions:
            if self.check_stock_ex_open_from_action(action):
                c1 = Q(action=action)
                c2 = Q(active=True)
                orders=Order.objects.filter(c1 & c2)
                auto=True
                today=timezone.now().strftime('%Y-%m-%d')
                
                if len(orders)>0:
                    if auto:
                        txt="Sell order sent for "+action.symbol
                    else:
                        txt="Manual sell order requested for "+action.symbol
                    o=orders[0]
                    e=o.entering_date.strftime('%Y-%m-%d')
                    if e<today: #avoid exiting order performed today
                        if o.sl_threshold is not None:
                            cours_pres=get_last_price(action)
                            if (not o.short and cours_pres<o.sl_threshold) or\
                            (o.short and cours_pres>o.sl_threshold):

                                r=Report.objects.create()
                                r.ss_m.add_target_quantity(action.symbol, o.strategy, 0)
                                r.ss_m.resolve()
                                self.telegram_bot.send_message_to_all(txt+", stop loss")
                        
                        if o.daily_sl_threshold is not None:
                            ratio=get_ratio(action)
                            
                            if (not o.short and ratio<-o.daily_sl_threshold*100) or\
                            (o.short and ratio>o.daily_sl_threshold*100):
    
                                r=Report.objects.create()
                                r.ss_m.add_target_quantity(action.symbol, o.strategy, 0)
                                r.ss_m.resolve()
                                self.telegram_bot.send_message_to_all(txt+", daily stop loss")
                                
    def check_VIX(self):
        try:
            update_VIX()
            a=Action.objects.get(symbol="^VIX")
            c1 = Q(action=a)
            c2 = Q(active=True)
            alerts=Alert.objects.filter(c1 & c2)
            alerting=False
            if get_VIX()>_settings["VIX_ALERT_THRESHOLD"]:
                alerting=True
                
            if len(alerts)==0:
                if alerting:
                    alert=Alert(action=a,alarm=True, short=False,\
                                trigger_date=timezone.now(),\
                                opportunity=False)
                    alert.save()
                    self.telegram_bot.send_message_to_all("VIX index exceeds "+str(_settings["VIX_ALERT_THRESHOLD"])+"! There may be a crash")
            else:
                if not alerting:
                    this_alert=alerts[0]
                    this_alert.active=False
                    this_alert.alarm=False
                    this_alert.recovery_date=timezone.now()
                    this_alert.save()
                    self.telegram_bot.send_message_to_all("Recovery, VIX index")
  
            if get_VIX()>_settings["VIX_SELL_ALL_THRESHOLD"]:
                self.telegram_bot.send_message_to_all("VIX index exceeds "+str(_settings["VIX_SELL_ALL_THRESHOLD"])+"! All positions will be closed.")
                self.sell_all()
    
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass
        
    def sell_all(self):
        '''
        Sell all stocks
        '''
        r=Report.objects.create()
        actions=pf_retrieve_all()
        for a in actions:
            c1 = Q(action=a)
            c2 = Q(active=True)
            orders=Order.objects.filter(c1 & c2)            
            if len(orders)>0:
                o=orders[0]
                strategy=o.strategy
            else:
                print("no order found fallback on none")
                strategy="none"
            
            r.ss_m.add_target_quantity(a.symbol, strategy, 0)
        r.ss_m.resolve()
    
    def send_order(self,
                   report: Report
                   ):
        '''
        Send Telegram message if orders have been performed
        
        Arguments
       	----------
           report: report for which the calculation happened
        '''   
        oems=OrderExecutionMsg.objects.filter(report=report)
        for oem in oems:
            self.telegram_bot.send_message_to_all(oem.text)
        if report.text:
             self.telegram_bot.send_message_to_all(report.text)       
    
    def daily_report_sub(
            self,
            exchange:str,
            it_is_index:bool=False,
            sec:str=None,
            **kwargs):
        '''
        See daily report
        
        Arguments
       	----------
           exchange: name of the stock exchange
           sec: sector of the stocks for which we write the report
        '''  
        if exchange is not None:
            s_ex=StockEx.objects.get(name=exchange)
            report1=Report.objects.create(stock_ex=s_ex)
        else:
            report1=Report.objects.create()
        report1.daily_report(exchange=exchange,it_is_index=it_is_index,sec=sec,**kwargs)
        self.send_order(report1)
        
    def daily_report(self, 
                     s_ex: StockEx,
                     intraday: bool=False,
                     **kwargs):
        '''
        Write report for an exchange and/or sector
        
        Arguments
       	----------
           s_ex: stock exchange from which the stocks need to be covered
           intraday: is it a report at the end of the day or during it
        '''  
        try:
            if self.check_stock_ex_open(s_ex):
                print("writting daily report "+s_ex.name)
                if intraday:
                    a="strategies_in_use_intraday"
                else:
                    a="strategies_in_use"
    
                if s_ex.presel_at_sector_level:
                    for sec in ActionSector.objects.all():
                        strats=getattr(sec,a).all()
                        if len(strats)!=0: #some strategy is activated for this sector
                            print("starting report " + sec.name)
                            self.daily_report_sub(s_ex.name,sec=sec)
                else:
                    strats=getattr(s_ex,a).all()
                    if len(strats)!=0: 
                        self.daily_report_sub(s_ex.name)
                    
                if not intraday:
                    self.daily_report_sub(exchange=None,symbols=[exchange_to_index_symbol(s_ex.name)[1]],it_is_index=True)
                
                self.telegram_bot.send_message_to_all("Daily report "+s_ex.name+" ready")
            
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass

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
                actions=get_exchange_actions(j.stock_ex.name)
                st=Strategy.objects.get(name=j.strategy.name)
                pr=caller.name_to_ust_or_presel(
                    st.class_name, 
                    st.ml_model_name,
                    str(j.period_year)+"y",
                    prd=True, 
                    actions=actions,
                    exchange=j.stock_ex.name,
                    st=st
                    ) 
                pr.actualize()   
                j.last_execution=today
                j.save()

    def shift_time(
            self, 
            d: datetime, 
            m: int,
            tz: str
            )->datetime:
        '''
        Shift the datetime from some minutes
        
        Arguments
       	----------
        d: original datetime
        m: delta in minutes
        tz: name of the timezone
        '''
        return (datetime.combine(date(1,1,1),d)+timedelta(minutes=m)).time().replace(tzinfo=ZoneInfo(tz))

    def check_nan(
            self,
            s_ex: StockEx,
            **kwargs):
            '''
            Check if symbol have been delisted
            
            Arguments
           	----------
               s_ex: stock exchange from which the stocks need to be covered
            '''  
            exchange=s_ex.name

            if exchange is not None:
                s_ex=StockEx.objects.get(name=exchange)
                actions=get_exchange_actions(exchange)
                actions=filter_intro_action(actions,_settings["DAILY_REPORT_PERIOD"])
                actions_list=[a.symbol for a in actions]
                
                if s_ex.main_index is not None:
                    problem_txt=data_manager.retrieve_debug( 
                        actions_list,
                        s_ex.main_index.symbol,
                        "3y")
                    
                    if problem_txt!="":
                        self.telegram_bot.send_message_to_all(problem_txt)

def cleaning_sub():
    alerts=Alert.objects.filter(active=True)
    for alert in alerts:
        alert.active=False
        alert.save()

 
    