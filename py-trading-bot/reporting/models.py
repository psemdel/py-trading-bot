from django.db import models

import math

from trading_bot.settings import _settings

from core import strat, presel
from core.presel import name_to_ust
from core import indicators as ic
from core.common import intersection
import warnings
import logging
logger = logging.getLogger(__name__)
logger_trade = logging.getLogger('trade')

from orders.models import Action, get_pf, get_candidates,\
                          get_exchange_actions,\
                          StratCandidates, StockEx, Strategy, ActionSector,\
                          check_ib_permission, filter_intro_action
from orders.ss_manager import StockStatusManager

      
class ListOfActions(models.Model):
    """
    Temporary storage for the telegram to message the orders at the end of the reporting.
    Difficulty is that the telegram bot is async, so it is not possible to just make send_msg() in the order execution function
    """
    report=models.ForeignKey('Report',on_delete=models.CASCADE)
    entry=models.BooleanField(blank=False,default=False) #otherwise exit
    buy=models.BooleanField(blank=False,default=False)
    reverse=models.BooleanField(blank=False,default=False,null=True) 
    used_api=models.CharField(max_length=100, blank=False, default="YF")
    actions=models.ManyToManyField(Action,blank=True,related_name="symbols") 
    text=models.TextField(blank=True)
    
    def concat(self,text):
        print(text)     
        self.text+=text +"\n"
        self.save() 

class Report(models.Model):
    """
    Periodically, a report is written. It performs calculation to decide if products need to be bought or sold.
    It also fill ActionReports which saves human readable indicators
    """
    date=models.DateTimeField(null=False, blank=False, auto_now_add=True)   #) default=timezone.now()
    text=models.TextField(blank=True)
    stock_ex=models.ForeignKey('orders.StockEx',on_delete=models.CASCADE,null=True)
    it_is_index=models.BooleanField(blank=False,default=False)
    sector=models.ForeignKey('orders.ActionSector',on_delete=models.CASCADE,blank=True,null=True)
    
    def __str__(self):
        return str(self.date)
    
    class Meta:
        ordering = ['-date', 'stock_ex']
        
    def save(self, *args, testing:bool=False,**kwargs):
        if "ss_m" not in self.__dir__():
            self.ss_m=StockStatusManager(self,testing=testing)
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

    def handle_listOfActions(
            self, 
            action: Action, 
            entry: bool, 
            used_api: str, 
            buy: bool, 
            strategy: str,
            reverse: bool=None, 
            ):
        '''
        Create a list of action and edit it after an order
        
        Arguments
       	----------
           action: stock where an order was performed
           ent: was the order an entry
           reverse: was the order a reversion (from short to long or the other way around)
           buy: was the order a buy order
           auto: was the order automatic or not
           strategy: name of the strategy which decided of this order        
        '''
        buy_sell_txt={True:"buying ", False: "selling "}
        txt=buy_sell_txt[buy]+"Order executed, symbol: " +action.symbol +" strategy: " + strategy
        logger_trade.info(txt)
        ent_ex_symbols, _=ListOfActions.objects.get_or_create(
            report=self,
            entry=entry,
            reverse=reverse,
            buy=buy,
            used_api=used_api
            )
        ent_ex_symbols.actions.add(action)
        ent_ex_symbols.concat(txt)    

### Logic for buying and selling actions preselected with retard strategy
    def candidates_to_YF(self,
                         symbols_to_YF: dict=None, 
                         candidates: list=[]
                         ) -> list:
        """
       	Convert a list of tickers to list of YF tickers
           
        Arguments
       	----------
           symbols_to_YF: dictionary that converts a YF or IB ticker into a YF ticker
           candidates: list of product symbols, that can be either YF or IB tickers
       	""" 
        return [symbols_to_YF[c] for c in candidates]

    def retard(
            self,
            exchange: str,
            ust,
            **kwargs):
        """
       	Perform the retard strategy order 
        Note: to be replace through a Retard method      
           
        Arguments
       	----------
           exchange: name of the stock exchange
           ust: underlying strategy 
       	""" 
        if _settings["RETARD_MACRO"]:
            pr=presel.name_to_presel("PreselRetardMacro", ust.period,prd=True, input_ust=ust,exchange=exchange) 
        else:
            pr=presel.name_to_presel("PreselRetard", ust.period,prd=True,input_ust=ust,exchange=exchange) 
        
        candidates, candidates_short=pr.get_candidates()
        
        if pr.last_short:
            direction="short"
            candidates=candidates_short
        else:
            direction="long"

        self.concat("Retard, " + "direction " + direction + ", stockex: " + exchange +\
                    ", action duration: " +str(pr.out))
  
        self.ss_m.order_nosubstrat(self.candidates_to_YF(ust.symbols_to_YF,candidates), exchange, "retard", pr.last_short, **kwargs)
      
    def presel_wq(
            self,
            ust,
            exchange: str,
            **kwargs):
        '''
        Preselected actions strategy, using 101 Formulaic Alphas
        
        Arguments
       	----------
           ust: underlying strategy 
           exchange: name of the stock exchange
        '''
        to_calculate=False
        stock_ex=StockEx.objects.get(name=exchange)
        
        for nb in range(102):
            strategy="wq"+str(nb)
            strats=Strategy.objects.filter(name=strategy)
            if len(strats)>0:
                if strats[0] in stock_ex.strategies_in_use.all():
                    to_calculate=True
        
        if to_calculate:
            wq=presel.WQ(ust.period, prd=True, input_ust=ust,exchange=exchange)
            
            for nb in range(102):
                strategy="wq"+str(nb)
                strats=Strategy.objects.filter(name=strategy) #normally there should be only one
                if len(strats)>0:
                    if strats[0] in stock_ex.strategies_in_use.all():
                        wq.call_wqa(nb=nb)
                        wq.def_cand()
                        candidates=wq.get_candidates()
                        
                        self.ss_m.order_nosubstrat(self.candidates_to_YF(ust.symbols_to_YF,candidates), exchange, strategy,False,**kwargs)
            logger.info("Presel wq done for "+exchange)  
            
### Preselected actions strategy    
    def presel_sub(self,l,ust, exchange,**kwargs):
        if len(l)!=0:
            #hist slow does not need code here
            if Strategy.objects.get(name="retard") in l:
                self.retard(exchange,ust,**kwargs)
            if Strategy.objects.get(name="retard_keep") in l:
                self.retard(exchange,ust,keep=True,**kwargs)
            if Strategy.objects.get(name="divergence") in l:    
                if _settings["DIVERGENCE_MACRO"]:
                    pr=presel.name_to_presel("PreselDivergenceBlocked", ust.period,prd=True,input_ust=ust,exchange=exchange)
                else:
                    pr=presel.name_to_presel("PreselDivergence", ust.period,prd=True,input_ust=ust,exchange=exchange)
                candidates, _=pr.get_candidates()
                self.ss_m.order_only_exit_substrat(self.candidates_to_YF(ust.symbols_to_YF,candidates), "divergence", False,**kwargs)
            if Strategy.objects.get(name="macd_vol") in l:
                pr=presel.name_to_presel("PreselMacdVolMacro", ust.period,prd=True,input_ust=ust,exchange=exchange)
                candidates, candidates_short=pr.get_candidates()
                
                if len(candidates)==0:
                    short=True
                    cand=candidates_short
                else:
                    short=False
                    cand=candidates
                    
                for symbol in cand:
                    symbol_complex=pr.ust.symbols_simple_to_complex(symbol,"ent")
                    if short:
                        self.ss_m.ex_ent_to_target(
                            False,
                            False,
                            pr.ust.exits[symbol_complex].values[-1],
                            pr.ust.entries[symbol_complex].values[-1],
                            pr.ust.symbols_to_YF[symbol], 
                            "macd_vol"
                            )
                    else:
                        self.ss_m.ex_ent_to_target(
                            pr.ust.entries[symbol_complex].values[-1],
                            pr.ust.exits[symbol_complex].values[-1],
                            False,
                            False,
                            pr.ust.symbols_to_YF[symbol], 
                            "macd_vol"
                            )
  
            logger.info("Presel done for "+exchange)    

    def presel(self,ust,exchange,**kwargs): #comes after daily report
        stock_ex=StockEx.objects.get(name=exchange)
        
        if stock_ex.presel_at_sector_level:
            if 'sec' in kwargs:
                sector=ActionSector.objects.get(name=kwargs.get("sec"))
                self.presel_sub(sector.strategies_in_use.all(),ust,exchange,**kwargs)
            else:    
                for s in ActionSector.objects.all(): #try for each sector
                    self.presel_sub(s.strategies_in_use.all(),ust,exchange,sec=s,**kwargs)
        else:
            self.presel_sub(stock_ex.strategies_in_use.all(),ust,exchange,**kwargs)
  
    def populate_report(
            self, 
            symbols: list, 
            symbols_to_YF: dict,
            ust_normal,
            ust_trend,
            ust_kama,
            ust_ma,
            ust_pattern):
        '''
        Fill the report with result of the calculations
        
        Arguments
       	----------
           symbols: list of YF ticker
           symbols_to_YF: dictionary that converts a YF or IB ticker into a YF ticker
           ust_normal, ust_trend, ust_kama, ust_ma, ust_pattern: underlying strategies containing some calculation results 
           exchange: name of the stock exchange
        '''
        for symbol in symbols:
            if math.isnan(ust_normal.vol[symbol].values[-1]):
                self.concat("symbol " + symbol + " no data")
                
            else:
                with warnings.catch_warnings():
                    #Necessary because of the presence of NaN
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    ar=ActionReport(
                        action=Action.objects.get(symbol=symbols_to_YF[symbol]), 
                        report=Report.objects.get(pk=self.pk))
        
                    symbol_complex_ent_normal=ust_normal.symbols_simple_to_complex(symbol,"ent")
                    symbol_complex_ex_normal=ust_normal.symbols_simple_to_complex(symbol,"ex")
                    decision=ust_normal.get_last_decision(symbol_complex_ent_normal,symbol_complex_ex_normal)
                    if decision==1:
                        ar.last_decision="sell"
                    elif decision==-1:
                        ar.last_decision="buy"

                    if ust_trend is not None:
                        grow_past50_raw=ust_trend.grow_past(50, False)
                        grow_past50_ma=ust_trend.grow_past(50, True)
                        grow_past20_raw=ust_trend.grow_past(20, False)
                        grow_past20_ma=ust_trend.grow_past(20, True)
                        ar.date=ust_trend.date()
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
            
                    if ust_pattern is not None:
                        ar.pattern_light_ent=ust_pattern.entries[(True, symbol)].values[-1] or\
                                             ust_pattern.entries[(True, symbol)].values[-2]
                                             
                        ar.pattern_light_ex=ust_pattern.exits[(True, symbol)].values[-1] or\
                                            ust_pattern.exits[(True, symbol)].values[-2]
            
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
            ust_normal, 
            strategy: str):
        '''
        Display the present direction expected for a stock
        Note: to be replaced with SS_manager        
        '''
        symbol_complex_ent_normal=ust_normal.symbols_simple_to_complex(symbol,"ent")
        symbol_complex_ex_normal=ust_normal.symbols_simple_to_complex(symbol,"ex")
        decision=ust_normal.get_last_decision(symbol_complex_ent_normal,symbol_complex_ex_normal)
        if decision==1:
            self.concat(symbol + " present decision for "+str(strategy)+" strategy : sell")
        elif decision==-1:
            self.concat(symbol + " present decision for "+str(strategy)+" strategy : buy")
        return symbol_complex_ent_normal, symbol_complex_ex_normal
            
    #for a group of predefined actions, determine the signals    
    def perform_normal_strat(
            self,
            actions, 
            exchange,
            it_is_index:bool=False, 
            **kwargs):
        '''
        Perform the strategy called "normal"
        
        Arguments
       	----------
        actions: list of action 
        exchange: name of the stock exchange
        it_is_index: is it indexes that are provided
        '''
        try:
            if self.it_is_index:
                ust_name=_settings["STRATEGY_NORMAL_INDEX"]
            else:
                ust_name=_settings["STRATEGY_NORMAL_STOCKS"]
                
            ust_normal=name_to_ust(
                ust_name,
                str(_settings["DAILY_REPORT_PERIOD"])+"y",
                prd=True,
                actions=actions,
                exchange=exchange,
                it_is_index=it_is_index
                )  
            
            normal_strat, _=Strategy.objects.get_or_create(name="normal")
            normal_strat_act, _=StratCandidates.objects.get_or_create(strategy=normal_strat)  #.id
            normal_strat_symbols=normal_strat_act.retrieve()
            
            for symbol in intersection(ust_normal.symbols,normal_strat_symbols):
                if math.isnan(ust_normal.vol[symbol].values[-1]):
                    self.concat("symbol " + symbol + " no data")
                else:
                    symbol_complex_ent_normal, symbol_complex_ex_normal=self.display_last_decision(symbol,ust_normal, "normal")
                    
                    #list present status
                    self.ss_m.ex_ent_to_target(
                        ust_normal.entries[symbol_complex_ent_normal].values[-1],
                        ust_normal.exits[symbol_complex_ex_normal].values[-1],
                        ust_normal.entries_short[symbol_complex_ex_normal].values[-1],
                        ust_normal.exits_short[symbol_complex_ent_normal].values[-1],
                        ust_normal.symbols_to_YF[symbol], 
                        "normal"
                        )
            return ust_normal
        except Exception as e:
            import sys
            _, e_, exc_tb = sys.exc_info()
            print(e)
            print("line " + str(exc_tb.tb_lineno))  
                                         
    def perform_keep_strat(
            self,
            ust_normal, 
            **kwargs):
        '''
        Perform the strategy called "retard keep"
        
        Arguments
       	----------
        ust_normal: underlying strategy containing most of the needed information
        '''        
        if not self.it_is_index:
            ust_keep=name_to_ust(
                _settings["STRATEGY_RETARD_KEEP"],
                ust_normal.period,
                input_ust=ust_normal,
                prd=True
                ) 

            pf_keep=get_pf("retard_keep",ust_keep.exchange,False)
            pf_short_keep=get_pf("retard_keep",ust_keep.exchange,True)
            
            for symbol in ust_keep.symbols:
                if symbol in pf_keep:
                    self.concat("symbol presently in keep: "+symbol)
                    symbol_complex_ent_normal, symbol_complex_ex_normal=self.display_last_decision(symbol,ust_keep,"keep")

                    self.ss_m.ex_ent_to_target(
                        False, #only exit
                        ust_normal.exits[symbol_complex_ex_normal].values[-1],
                        False,
                        False,
                        ust_normal.symbols_to_YF[symbol], 
                        "retard_keep",
                        )
                if symbol in pf_short_keep: 
                    self.concat("symbol presently in keep short: "+symbol)
                    symbol_complex_ent_normal, symbol_complex_ex_normal=self.display_last_decision(symbol,ust_keep,"keep")
                    self.ss_m.ex_ent_to_target(
                        False, #only exit
                        False,
                        False,
                        ust_normal.exits_short[symbol_complex_ent_normal].values[-1],
                        ust_normal.symbols_to_YF[symbol], 
                        "retard_keep",
                        )
                                  
    def perform_slow_strats(
            self, 
            ust_normal, 
            strats, 
            **kwargs):
        '''
        Slow candidates
        
        Arguments
       	----------
        ust_normal: underlying strategy containing most of the needed information
        strats: list of strategy names
        '''    
        try:
            slow_strats=[Strategy.objects.get(name="hist_slow"),\
                         Strategy.objects.get(name="realmadrid")] #only those in use
            slow_strats_active=[]
            slow_cands={}
            
            for s in intersection(strats,slow_strats):
                slow_strats_active.append(s)
                if not self.it_is_index and ust_normal.exchange is not None: 
                    cand=get_candidates(s.name,ust_normal.exchange)
                    slow_cands[s.name]=cand.retrieve()
                else:
                    slow_cands[s.name]=[]   
                     
            ##Change underlying strategy
            ust_slow=name_to_ust(
                "StratKamaStochMatrendBbands",
                ust_normal.period,
                input_ust=ust_normal,
                prd=True
                ) 
            
            for symbol in ust_slow.symbols:
                symbol_complex_ent=ust_slow.symbols_simple_to_complex(symbol,"ent")                            
                
                for st in slow_strats_active:
                    if ust_slow.symbols_to_YF[symbol] in slow_cands[s.name]: #list of candidates
                        self.ss_m.ex_ent_to_target(
                            ust_slow.entries[symbol_complex_ent].values[-1],
                            ust_slow.exits[symbol_complex_ent].values[-1],
                            False, #both strategy use only long
                            False,
                            ust_slow.symbols_to_YF[symbol], 
                            st.name,
                            )
        except:
            print("check that hist_slow and realmadrid strategies are created")                
                        
    def perform_divergence(self,ust_normal, strats, **kwargs):
        try:
            st=Strategy.objects.get(name="divergence")
        except:
            print("check that divergence strategy is created") 
            pass
        
        try: 
            if not self.it_is_index and ust_normal.exchange is not None: #index
                #even if divergence is not anymore used, we should be able to exit
                pf_div=get_pf("divergence",ust_normal.exchange,False)
                self.concat("symbols in divergence: " +str(pf_div))
                ##Change underlying strategy
                ust_div=name_to_ust(
                    "StratDiv",
                    ust_normal.period,
                    input_ust=ust_normal,
                    prd=True
                    ) 
                
                ##only_exit_substrat
                if len(pf_div)>0:
                    for symbol in ust_div.symbols:
                        symbol_complex_ent=ust_div.symbols_simple_to_complex(symbol,"ent")  
                        
                        if st in strats and\
                                ust_div.symbols_to_YF[symbol] in pf_div and ust_div.exits[symbol_complex_ent].values[-1]: 
    
                                logger_trade.info("Divergence exit " + str(ust_div.exits[symbol_complex_ent].values[-1]))    
 
                                self.ss_m.ex_ent_to_target(
                                     False,
                                     ust_div.exits[symbol_complex_ent].values[-1],
                                     False,
                                     False,
                                     ust_div.symbols_to_YF[symbol], 
                                     st.name,
                                     )   
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass   
        
    def daily_report(self,
        it_is_index: bool=False,
        exchange: str=None,
        sec: str=None,
        symbols: list=[],        
        **kwargs): #for one exchange and one sector
        """
    	Method that write the report itself
    
    	Arguments
    	----------
        it_is_index: is it indexes that are provided
        exchange: name of the stock exchange
        symbols: list of YF symbols
        sec: sector of the stocks for which we write the report
    	"""     
        try: 
            ##preprocessing
            self.it_is_index=it_is_index
            if self.it_is_index:
                check_ib_permission(symbols)
                actions=[Action.objects.get(symbol=symbol) for symbol in symbols]
            else: #actions, exchange is provided
                actions=get_exchange_actions(exchange,**kwargs)
            
            ##handle the sectors
            if exchange is not None:
                self.stock_ex=StockEx.objects.get(name=exchange)
                if self.stock_ex.presel_at_sector_level:
                    if sec:
                        try:
                            sector=ActionSector.objects.get(name=sec)
                            strats=sector.strategies_in_use.all()
                        except:
                            logger.warning("sector not found: " + str(sec))
                            pass
                else:
                    strats=self.stock_ex.strategies_in_use.all()
            else:
                self.stock_ex=StockEx.objects.get(name="Paris") #convention
                strats=[]
  
            if len(actions)==0:
                print("No actions found for exchange: "+str(exchange))
                logger.info("No actions found for exchange: "+str(exchange))
                return None
            else:
                if self.pk is None:
                    self.save()
                    
                #clean the symbols
                actions=filter_intro_action(actions,_settings["DAILY_REPORT_PERIOD"])
                ##Perform a single strategy on predefined actions
                #Uses afterward as source for the data to avoid loading them several times
                ust_normal=self.perform_normal_strat(actions, exchange,it_is_index=it_is_index, **kwargs)
                ##Populate a report with different statistics
                ust_kama=ic.VBTSTOCHKAMA.run(ust_normal.high,ust_normal.low,ust_normal.close)
                ust_ma=ic.VBTMA.run(ust_normal.close)

                ust_pattern=None
                if _settings["CALCULATE_PATTERN"]:
                    ust_pattern=ic.VBTPATTERN.run(ust_normal.open,ust_normal.high,ust_normal.low,ust_normal.close,light=True)
                ust_trend=None
                if _settings["CALCULATE_TREND"]:
                    ust_trend=name_to_ust(
                        "StratKamaStochMatrendMacdbbMacro",
                        ust_normal.period,
                        input_ust=ust_normal,
                        prd=True
                        )    

                self.populate_report(ust_normal.symbols, ust_normal.symbols_to_YF, ust_normal,ust_trend, ust_kama, ust_ma, ust_pattern)
                logger.info("Strat daily report written " +(exchange or ""))

                self.perform_keep_strat(ust_normal, **kwargs)
                ##Perform strategies that rely on the regular preselection of a candidate
                self.perform_slow_strats(ust_normal, strats, **kwargs)
                
                ##Perform the strategy divergence, the exit to be precise, the entry are performed by presel
                self.perform_divergence(ust_normal, strats, **kwargs)

                logger.info("Slow strategy proceeded") 
                if sec is not None:
                    self.sector=ActionSector.objects.get(name=sec) 
                self.save()
                self.ss_m.resolve()
                return ust_normal

        except ValueError as e:
            logger.error(e, stack_info=True, exc_info=True)
        except Exception as e:
            import sys
            _, e_, exc_tb = sys.exc_info()
            print(e)
            print("line " + str(exc_tb.tb_lineno))
            logger.error("line " + str(exc_tb.tb_lineno), stack_info=True, exc_info=True)
            logger.error(e, stack_info=True, exc_info=True)
            self.concat("daily_report, exchange: "+exchange + " crashed, check the logs")
            pass 
 
class ActionReport(models.Model):
    """
    Contain human readable indicators for one product and one report
    """   
    report=models.ForeignKey('Report',on_delete=models.CASCADE)
    action=models.ForeignKey('orders.Action',on_delete=models.CASCADE, null=True,default=None)
    
    date=models.CharField(max_length=100, blank=True)
  
    last_decision=models.CharField(max_length=100, blank=True)
    #for Trend
    vol=models.DecimalField(max_digits=100, decimal_places=5, default=0.0)
    bbands_bandwith=models.DecimalField(max_digits=100, decimal_places=5, default=0.0)
    trend=models.DecimalField(max_digits=100, decimal_places=5, default=0.0)
    macro_trend=models.DecimalField(max_digits=100, decimal_places=5, default=0.0)
    
    kama_dir=models.DecimalField(max_digits=100, decimal_places=5, default=0.0)
    
    three_mo_evol=models.DecimalField(max_digits=100, decimal_places=5, default=0.0)
    three_mo_evol_sm=models.DecimalField(max_digits=100, decimal_places=5, default=0.0)
    one_mo_evol=models.DecimalField(max_digits=100, decimal_places=5, default=0.0)
    one_mo_evol_sm=models.DecimalField(max_digits=100, decimal_places=5, default=0.0)
    
    #for Decision
    stoch=models.DecimalField(max_digits=100, decimal_places=5, default=0.0)
    pattern_ent=models.BooleanField(blank=False,default=False) #not used
    pattern_ex=models.BooleanField(blank=False,default=False) #not used
    pattern_light_ent=models.BooleanField(blank=False,default=False)
    pattern_light_ex=models.BooleanField(blank=False,default=False) 
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
    Performance alert for one product
    Related to the sending of a message in Telegram
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

