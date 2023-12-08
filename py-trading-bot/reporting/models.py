from django.db import models

import math

from trading_bot.settings import _settings

from core.caller import name_to_ust_or_presel
from core import indicators as ic
import warnings
import logging
logger = logging.getLogger(__name__)
logger_trade = logging.getLogger('trade')

from orders.models import Action, get_exchange_actions, StockEx,  ActionSector,\
                          check_ib_permission, filter_intro_action
from orders.ss_manager import StockStatusManager

class OrderExecutionMsg(models.Model):
    """
    Temporary storage for the telegram to message the orders at the end of the reporting.
    Difficulty is that the telegram bot is async, so it is not possible to just make send_msg() in the order execution function
  
    Attributes
   	----------
         report: Report that generated this list.
         action: stock traded
         text: free text to be displayed in the Telegram message    
    """
    report=models.ForeignKey('Report',on_delete=models.CASCADE)
    action=models.ForeignKey('orders.Action',on_delete=models.CASCADE)
    text=models.TextField(blank=True)

    def concat(self,text):
        print(text)     
        self.text+=text +"\n"
        self.save() 
        
class Report(models.Model):
    """
    Periodically, a report is written. It performs calculation to decide if products need to be bought or sold.
    It also fill ActionReports which saves human readable indicators
    
    Note: a report can cover only one stock exchange.
    
    Attributes
   	----------
         date: Date when the report was generated
         text: free text to be displayed in the Telegram message and in the report 
         stock_ex: corresponding stock exchange
         it_is_index: are the products covered by the report indexes?
         sector: sector of the products covered by the report
    """
    date=models.DateTimeField(null=False, blank=False, auto_now_add=True)   #) default=timezone.now()
    text=models.TextField(blank=True)
    stock_ex=models.ForeignKey('orders.StockEx',on_delete=models.CASCADE,null=True)
    it_is_index=models.BooleanField(blank=False,default=False)
    sector=models.ForeignKey('orders.ActionSector',on_delete=models.CASCADE,blank=True,null=True)
    target_ss_by_st=models.TextField(blank=True,null=True)
    
    def __str__(self):
        return str(self.date)
    
    class Meta:
        ordering = ['-date', 'stock_ex']
        
    def save(self, *args, testing:bool=False,**kwargs):
        '''
        Save the model
        
        Arguments
       	----------
           testing: set to True to perform unittest on the function
        '''
        if "ss_m" not in self.__dir__():
            if self.stock_ex is None:
                self.ss_m=StockStatusManager(self,None,testing=testing)
            else:
                self.ss_m=StockStatusManager(self,self.stock_ex.name,testing=testing)
        super().save(*args, **kwargs)  
            
    def concat(self,text: str):
        '''
        Add text to the report
        
        Arguments
       	----------
           text: text to be added to the report
        '''
        print(text)     
        self.text+=text +"\n"
        self.save()

    def handle_OrderExecutionMsg(
            self, 
            action: Action, 
            used_api: str, 
            buy: bool, 
            strategy: str,
            ):
        '''
        Create a list of action and edit it after an order
        
        Arguments
       	----------
           action: stock where an order was performed
           used_api: API used to perform the trade
           buy: was the order a buy order
           auto: was the order automatic or not
           strategy: name of the strategy which decided of this order        
        '''
        buy_sell_txt={True:"buying ", False: "selling "}
        if used_api!="YF":
            txt=buy_sell_txt[buy].capitalize()+"order executed, symbol: " +action.symbol +" strategy: " + strategy
        else:
            txt="Manual " + buy_sell_txt[buy].lower()+"order request, symbol: " +action.symbol +" strategy: " + strategy
        logger_trade.info(txt)
        OrderExecutionMsg.objects.create(
            report=self,
            action=action,
            text=txt
            )

### Preselected actions strategy    
    def perform_sub(
            self,
            strats,
            ust, 
            exchange: str,
            it_is_index:bool=False,
            sec:str=None
            ):
        '''
        Sub-function for perform_sub
        '''
        try:
            for st in strats:
                if st.class_name is None:
                    print("define class_name for strategy "+str(st.name))
                else:
                    ust_or_pr=name_to_ust_or_presel(
                        st.class_name,
                        ust.period,
                        input_ust=ust,
                        prd=True,
                        it_is_index=it_is_index,
                        st=st
                        )  
                    if ust_or_pr is not None: #presel with it_is_index
                        if st.class_name in ["PreselRetard","PreselRetardMacro"]:
                            keep=False
                            for st1 in strats: #if retard_keep is also active, keep.
                                if st1.name=="retard_keep":
                                    keep=True
                            ust_or_pr.perform(self, st_name=st.name,keep=keep)
                        else:
                            ust_or_pr.perform(self, st_name=st.name)
                    
        except Exception as e:
              import sys
              _, e_, exc_tb = sys.exc_info()
              print(e)
              print("line " + str(exc_tb.tb_lineno) + " for strategy: "+str(st.name))
      
    def perform(
            self,
            ust,
            sec:str=None,
            intraday:bool=False,
            it_is_index:bool=False,
            ):
        '''
        Perform all strategies and there related trades for a given set of symbols
        
        Arguments
       	----------
          ust: underlying strategy
          sec: sector of the stocks for which we write the report
          intraday: is it a report at the end of the day or during it
          it_is_index: is it indexes that are provided 
        '''
        try:
            if ust.exchange is None: #for indexes
                stock_exs=[a.stock_ex for a in ust.actions]
            else:
                stock_exs=[StockEx.objects.get(name=ust.exchange)]
                
            if intraday:
                a="strategies_in_use_intraday"
            else:
                a="strategies_in_use"
            
            for stock_ex in stock_exs: #sector is already in ust
                strats=getattr(stock_ex,a).all()
                self.perform_sub(strats,ust,ust.exchange,it_is_index=it_is_index)
        except Exception as e:
             import sys
             _, e_, exc_tb = sys.exc_info()
             print(e)
             print("line " + str(exc_tb.tb_lineno))
        
    def populate_report(
            self, 
            symbols: list, 
            symbols_to_YF: dict,
            ust_hold,
            ust_trend,
            ust_kama,
            ust_ma):
        '''
        Fill the report with result of the calculations
        
        Arguments
       	----------
           symbols: list of YF ticker
           symbols_to_YF: dictionary that converts a YF or IB ticker into a YF ticker
           ust_hold, ust_trend, ust_kama, ust_ma: underlying strategies containing some calculation results 
           exchange: name of the stock exchange
        '''
        for symbol in symbols:
            if math.isnan(ust_hold.vol[symbol].values[-1]):
                self.concat("symbol " + symbol + " no data")
                
            else:
                with warnings.catch_warnings():
                    #Necessary because of the presence of NaN
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    ar=ActionReport(
                        action=Action.objects.get(symbol=symbols_to_YF[symbol]), 
                        report=Report.objects.get(pk=self.pk))

                    if ust_trend is not None:
                        grow_past50_raw=ust_trend.grow_past(50, False)
                        grow_past50_ma=ust_trend.grow_past(50, True)
                        grow_past20_raw=ust_trend.grow_past(20, False)
                        grow_past20_ma=ust_trend.grow_past(20, True)
                        ar.vol=ust_trend.vol[symbol].values[-1]

                        symbol_complex_ent=ust_trend.symbols_simple_to_complex(symbol,"ent")
                        
                        ar.bbands_bandwith=ust_trend.bb_bw[symbol_complex_ent].values[-1]
                        ar.trend=float(ust_trend.trend[symbol_complex_ent].values[-1])
                        ar.macro_trend=float(ust_trend.macro_trend[symbol_complex_ent].values[-1])
                    
                    ar.three_mo_evol=grow_past50_raw[(50,False,symbol)].values[-1]
                    ar.three_mo_evol_sm=grow_past50_ma[(50,True,symbol)].values[-1]
                    ar.one_mo_evol=grow_past20_raw[(20,False,symbol)].values[-1]
                    ar.one_mo_evol_sm=grow_past20_ma[(20,True,symbol)].values[-1]
                    
                    ar.kama_ent=ust_kama.entries_kama[symbol].values[-1]
                    ar.kama_ex=ust_kama.exits_kama[symbol].values[-1]
                    ar.kama_dir=float(ust_kama.direction[symbol].values[-1])
            
                    ar.stoch_ent=ust_kama.entries_stoch[symbol].values[-1]
                    ar.stoch_ex=ust_kama.exits_stoch[symbol].values[-1]
                    
                    if math.isnan(ust_kama.stoch[symbol].values[-1]):
                        ar.stoch=0
                    else:
                        ar.stoch=ust_kama.stoch[symbol].values[-1]
                    
                    ar.ma_ent=ust_ma.entries[symbol].values[-1]
                    ar.ma_ex=ust_ma.exits[symbol].values[-1]
            
                    if self.it_is_index:
                        if ar.kama_ent:
                            self.concat(" Index " + symbol + " KAMA bottom detected!")
                        if ar.kama_ex:
                            self.concat(" Index " + symbol + " KAMA top detected!")
                        if ust_trend is not None:   
                            if ust_trend.max_ind[symbol_complex_ent][-1]!=0:
                                self.concat(" Index " + symbol + " V maximum detected!")
                            if ust_trend.min_ind[symbol_complex_ent][-1]!=0:
                                self.concat(" Index " + symbol + " V minimum detected!")                            
                    ar.save()  
        
    def display_last_decision(
            self,
            symbol: str,
            target_order: int, 
            strategy: str):
        '''
        Display the present direction expected for a stock
        
        Arguments
       	----------
        symbol: YF ticker
        target_order: which desired state (-1, 0, 1) is wanted   
        strategy: name of the strategy
        '''
        if target_order==-1:
            self.concat(symbol + " present decision for "+str(strategy)+" strategy : sell")
        elif target_order==1:
            self.concat(symbol + " present decision for "+str(strategy)+" strategy : buy")
            
    def init_ust(
            self,
            actions, 
            exchange,
            it_is_index:bool=False             
            ):
        '''
        An underlying strategy is a convenient to use object to contains most important information
        It avoid downloading the prices several times
        Hold is used as it does not involve much calculation
        
        Arguments
       	----------
        actions: list of action 
        exchange: name of the stock exchange
        it_is_index: is it indexes that are provided
        '''
        return name_to_ust_or_presel(
                "StratHold",
                str(_settings["DAILY_REPORT_PERIOD"])+"y",
                prd=True,
                actions=actions,
                exchange=exchange,
                it_is_index=it_is_index
                )  
                                   
    def daily_report(self,
        it_is_index: bool=False,
        exchange: str=None,
        sec: str=None,
        symbols: list=[],    
        intraday: bool=False,
        testing:bool=False,
        **kwargs): #for one exchange and one sector
        """
    	Method that write the report itself
    
    	Arguments
    	----------
        it_is_index: is it indexes that are provided
        exchange: name of the stock exchange
        sec: sector of the stocks for which we write the report
        symbols: list of YF symbols
        sec: sector of the stocks for which we write the report
        intraday: is it a report at the end of the day or during it
        testing: set to True to perform unittest on the function
    	"""     
        try: 
            ##preprocessing
            self.it_is_index=it_is_index
            if self.it_is_index:
                check_ib_permission(symbols)
                actions=[Action.objects.get(symbol=symbol) for symbol in symbols]
            else: #actions, exchange is provided
                actions=get_exchange_actions(exchange,sec=sec) #-> sec is considered here

            if exchange is not None:
                self.stock_ex=StockEx.objects.get(name=exchange)
            
            if len(actions)==0:
                print("No actions found for exchange: "+str(exchange))
                logger.info("No actions found for exchange: "+str(exchange))
                return None
            else:
                if self.pk is None:
                    self.save(testing=testing)
                    
                #clean the symbols
                actions=filter_intro_action(actions,_settings["DAILY_REPORT_PERIOD"])
                ##Perform a single strategy on predefined actions
                #Uses afterward as source for the data to avoid loading them several times
                ust_hold=self.init_ust(actions, exchange,it_is_index=it_is_index, **kwargs)

                if not intraday:
                    ##Populate a report with different statistics
                    ust_kama=ic.VBTSTOCHKAMA.run(ust_hold.high,ust_hold.low,ust_hold.close)
                    ust_ma=ic.VBTMA.run(ust_hold.close)
    
                    ust_trend=None
                    if _settings["CALCULATE_TREND"]:
                        ust_trend=name_to_ust_or_presel(
                            "StratKamaStochMatrendMacdbbMacro",
                            ust_hold.period,
                            input_ust=ust_hold,
                            prd=True
                            )    
    
                    self.populate_report(ust_hold.symbols, ust_hold.symbols_to_YF, ust_hold,ust_trend, ust_kama, ust_ma)
                    logger.info("Strat daily report written " +(exchange or ""))
              
                if sec is not None:
                    self.sector=ActionSector.objects.get(name=sec) 
                self.save(testing=testing)
                
                self.perform(
                        ust_hold,
                        sec=sec,
                        intraday=intraday,
                        it_is_index=it_is_index,
                        **kwargs)

                self.ss_m.resolve()
                self.target_ss_by_st=self.ss_m.display_target_ss_by_st(it_is_index=it_is_index)
                self.save(testing=testing)

        except ValueError as e:
            logger.error(e, stack_info=True, exc_info=True)
        except Exception as e:
            import sys
            _, e_, exc_tb = sys.exc_info()
            print(e)
            print("line " + str(exc_tb.tb_lineno))
            import traceback
            print(traceback.format_exc())
            logger.error("line " + str(exc_tb.tb_lineno), stack_info=True, exc_info=True)
            logger.error(e, stack_info=True, exc_info=True)
            self.concat("daily_report, exchange: "+str(exchange) + " crashed, check the logs")
            pass 
 
class ActionReport(models.Model):
    """
    Contain human readable indicators for one product and one report
    
    Attributes
   	----------
    report: Report related to this action report
    action: product covered by this action report
    vol: volativity
    bbands_bandwidth: bandwidth of the Bollinger bands
    trend: figure between -10 and 10. It is a fast trend evaluated with help of the bband and the MACD. 
          It can change quickly. trend>0 means bear here, <0 bull. 
    macro_trend: a slow trend evaluated by determining the extrema of a smoothed price curve.
                 macro_trend>0 means bear, <0 bull, =0 means that it is unclear.
    kama_dir: is the smoothed (kama) price increasing (then =-1) or decreasing (then =1)?           
    three_mo_evol: price change over the past 3 months
    three_mo_evol_sm: smoothed price change over the past 3 months
    one_mo_evol: price change over the past month
    one_mo_evol_sm: smoothed price change over the past month
    
    stoch: Stochastic Oscillator. figure between 0 and 100, 
    pattern_ent: was one pattern of the BULL_PATTERNS (see constants.py) detected?
    pattern_ex: was one pattern of the BEAR_PATTERNS (see constants.py) detected?
    kama_ent: indicates a minimum on the smoothed price (kama)
    kama_ex: indicates a maximum on the smoothed price (kama)
    stoch_ent: was an entry signal created by the Stochastic Oscillator. Typically if its value crosses 80.
    stoch_ex: was an exit signal created by the Stochastic Oscillator. Typically if its value crosses 20.
    ma_ent: was an entry signal created by the moving average strategy, when the fast window price becomes higher 
           than the slow window price.
    ma_ent: was an exit signal created by the moving average strategy, when the fast window price becomes lower 
           than the slow window price.    
    """   
    report=models.ForeignKey('Report',on_delete=models.CASCADE)
    action=models.ForeignKey('orders.Action',on_delete=models.CASCADE, null=True,default=None)
    #for Trend
    vol=models.FloatField(default=0.0)
    bbands_bandwidth=models.FloatField( default=0.0)
    trend=models.FloatField( default=0.0)
    macro_trend=models.FloatField( default=0.0)
    
    kama_dir=models.FloatField( default=0.0)
    
    three_mo_evol=models.FloatField( default=0.0)
    three_mo_evol_sm=models.FloatField( default=0.0)
    one_mo_evol=models.FloatField( default=0.0)
    one_mo_evol_sm=models.FloatField( default=0.0)
    
    #for Decision
    stoch=models.FloatField(default=0.0)
    pattern_ent=models.BooleanField(blank=False,default=False) #not used
    pattern_ex=models.BooleanField(blank=False,default=False) #not used
    pattern_light_ent=models.BooleanField(blank=False,default=False) #not used
    pattern_light_ex=models.BooleanField(blank=False,default=False)  #not used
    kama_ent=models.BooleanField(blank=False,default=False)
    kama_ex=models.BooleanField(blank=False,default=False)
    
    stoch_ent=models.BooleanField(blank=False,default=False)
    stoch_ex=models.BooleanField(blank=False,default=False)
    ma_ent=models.BooleanField(blank=False,default=False)
    ma_ex=models.BooleanField(blank=False,default=False) 
    
    def __str__(self):
        if self.action is not None:
            return self.action.name + " " + str(self.report.date)
        else:
            return "none" + " " + str(self.report.date)

class Alert(models.Model):
    """
    Performance alert for one product, if the price variation exceeds a certain threshold
    Related to the sending of a message in Telegram
    
    Attributes
   	----------
    active: indicate if the alert is active, so still present
    opportunity: type of alert which is more for information and don't relate to a potential loss for stocks in our portfolio
    opening: was the alert create at stock opening?
    alarm: was the price variation very high, 5% by default?
    short: does it concerns a stock in short direction?
    trigger_date: when did the alert start?
    recovery_date: when did the alert end?
    action: product related to the alert    
    """  
    active=models.BooleanField(blank=False,default=True)
    opportunity=models.BooleanField(blank=False,default=False)
    opening=models.BooleanField(blank=False,default=False)
    alarm=models.BooleanField(blank=False,default=False)
    short=models.BooleanField(blank=False,default=False)
    trigger_date=models.DateTimeField(null=False, blank=False)
    recovery_date=models.DateTimeField(null=True, blank=True)
    action=models.ForeignKey('orders.Action',on_delete=models.CASCADE,null=True)

    def __str__(self):
        if self.action is not None:
            return self.action.name   + " " + str(self.trigger_date)
        else:
            return "none" + " " + str(self.trigger_date)

