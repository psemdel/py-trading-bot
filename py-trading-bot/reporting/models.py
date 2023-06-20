from django.db import models

import math

from trading_bot.settings import _settings

from core import stratP, preselP
from core import indicators as ic
from core.common import intersection
import warnings
import logging
logger = logging.getLogger(__name__)
logger_trade = logging.getLogger('trade')

from django.db.models import Q
from orders.ib import exit_order, entry_order, reverse_order

from orders.models import Action, Order, get_pf, get_candidates,\
                          get_exchange_actions,\
                          StratCandidates, StockEx, Strategy, ActionSector,\
                          check_ib_permission, filter_intro_action
      
class ListOfActions(models.Model):
    """
    Temporary storage for the telegram to message the orders at the end of the reporting.
    Difficulty is that the telegram bot is async, so it is not possible to just make send_msg() in the order execution function
    """
    report=models.ForeignKey('Report',on_delete=models.CASCADE)
    entry=models.BooleanField(blank=False,default=False) #otherwise exit
    short=models.BooleanField(blank=False,default=False)
    auto=models.BooleanField(blank=False,default=False)
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
    sector=models.ForeignKey('orders.ActionSector',on_delete=models.CASCADE,blank=True,default=1)
    
    def __str__(self):
        return str(self.date)
    
    class Meta:
        ordering = ['-date', 'stock_ex']
    
    def concat(self,text):
        print(text)     
        self.text+=text +"\n"
        self.save()

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

    def retard(self,presel,exchange,st,**kwargs):
        #key="retard"+"_"+exchange
        if _settings["RETARD_MACRO"]:
            presel.call_strat("preselect_retard_macro",**kwargs) #for sec
        else:
            presel.call_strat("preselect_retard",**kwargs) #for sec
        
        candidates, candidates_short=presel.get_candidates()
        
        if presel.last_short:
            direction="short"
            candidates=candidates_short
        else:
            direction="long"

        self.concat("Retard, " + "direction " + direction + ", stockex: " + exchange +\
                    ", action duration: " +str(presel.out))
  
        auto=True
        self.order_nosubstrat(self.candidates_to_YF(st.symbols_to_YF,candidates), exchange, "retard", presel.last_short, auto,**kwargs) #retard can be automatized

    #YF symbol expected here
    def order_only_exit_substrat(self,candidates, exchange, key, short,**kwargs):
        auto=True
        if len(candidates)==0:
            self.concat(key +" no candidates")        
        else:
            #buy without condition
            for symbol in candidates:
                self.concat(key +" candidates " + symbol)
                ent, auto=entry_order(symbol,key, exchange,short, auto,**kwargs)
                
                if ent:
                    action=Action.objects.get(symbol=symbol)
                    ent_symbols, _=ListOfActions.objects.get_or_create(
                        report=self,
                        entry=True,
                        short=short,
                        auto=auto
                        )
                    ent_symbols.actions.add(action)
                    
    #YF symbol expected here
    def order_nosubstrat_sub(self,symbol, short, ex, auto):
        if ex:
            action=Action.objects.get(symbol=symbol)
            ex_symbols, _=ListOfActions.objects.get_or_create(
                report=self,
                entry=False,
                short=short,
                auto=auto
                )
            
            ex_symbols.actions.add(action)
            
    #YF symbol expected here
    def order_nosubstrat(self,candidates, exchange, key, short,auto,**kwargs):
        #if there is a reversal the opposite pf needs to emptied
        pf_inv=get_pf(key,exchange,not short,**kwargs)
        
        if kwargs.get("keep",False):
            pf_keep=get_pf("retard_keep",exchange,short,**kwargs)

        for symbol in pf_inv.retrieve(): 
            if symbol not in candidates:
                ex, auto=exit_order(symbol,key, exchange,short, auto,**kwargs) #not short?
                self.order_nosubstrat_sub(symbol, short, ex, auto)

        #sell
        pf=get_pf(key,exchange,short,**kwargs)
        for symbol in pf.retrieve():
            if symbol not in candidates:
                if kwargs.get("keep",False):
                    action=Action.objects.get(symbol=symbol)
                    pf_keep.append(action) #move the symbol from retard to keep pf
                    pf.remove(action)
                    logger_trade.info(symbol + " moved from retard to retard_keep portfolio")
                    
                    #tsl part
                    c1 = Q(action=action)
                    c2 = Q(active=True)
                    order=Order.objects.filter(c1 & c2)
                    
                    if len(order)>0:
                        order[0].pf=pf_keep
                        order[0].save()
                else:
                    ex, auto=exit_order(symbol,key, exchange,short,auto, **kwargs)
                    self.order_nosubstrat_sub(symbol, short, ex, auto)
        
        if len(candidates)==0:
            self.concat(key +" no candidates")
        
        #buy
        for symbol in candidates:
            self.concat(key +" candidates " + symbol)
            
            ent, auto=entry_order(symbol,key, exchange,short,auto, **kwargs)
            if ent:
                action=Action.objects.get(symbol=symbol)
                ent_symbols, _=ListOfActions.objects.get_or_create(
                    report=self,
                    entry=True,
                    short=short,
                    auto=auto
                    )
                ent_symbols.actions.add(action)
      
### Preselected actions strategy, using 101 Formulaic Alphas
    def presel_wq(self,st,exchange,**kwargs):
        to_calculate=False
        auto=kwargs.get("autok",True)
        stock_ex=StockEx.objects.get(name=exchange)
        
        for nb in range(102):
            key="wq"+str(nb)
            strat=Strategy.objects.filter(name=key)
            if len(strat)>0:
                if strat[0] in stock_ex.strategies_in_use.all():
                    to_calculate=True
        
        if to_calculate:
            wq=preselP.WQPRD(st.use_IB,st=st,exchange=exchange)
            
            for nb in range(102):
                key="wq"+str(nb)
                strat=Strategy.objects.filter(name=key)
                if len(strat)>0:
                    if strat[0] in stock_ex.strategies_in_use.all():
                        wq.call_wqa(nb)
                        wq.def_cand()
                        candidates=wq.get_candidates()
                        
                        self.order_nosubstrat(self.candidates_to_YF(st.symbols_to_YF,candidates), exchange, key,False,auto,**kwargs) #fees are too high on IB for wq strategy
            logger.info("Presel wq done for "+exchange)  
            
### Preselected actions strategy    
    def presel_sub(self,use_IB,l,st, exchange,**kwargs):
        if len(l)!=0:
            presel=preselP.PreselPRD(use_IB,st=st,exchange=exchange)
            #hist slow does not need code here
            if Strategy.objects.get(name="retard") in l: 
                self.retard(presel,exchange,st,**kwargs)
            if Strategy.objects.get(name="retard_keep") in l:
                self.retard(presel,exchange,st,keep=True,**kwargs)
            if Strategy.objects.get(name="divergence") in l:    
                if _settings["DIVERGENCE_MACRO"]:
                    presel.call_strat("preselect_divergence_blocked")
                else:
                    presel.call_strat("preselect_divergence")
                
                candidates, _=presel.get_candidates()
                self.order_only_exit_substrat(self.candidates_to_YF(st.symbols_to_YF,candidates), exchange, "divergence", False,**kwargs)
            if Strategy.objects.get(name="macd_vol") in l:
                presel.call_strat("preselect_macd_vol_macro")
                candidates, candidates_short=presel.get_candidates()
                
                if len(candidates)==0:
                    short=True
                    cand=candidates_short
                else:
                    short=False
                    cand=candidates
                    
                for symbol in cand:
                    symbol_complex=presel.st.symbols_simple_to_complex(symbol,"ent")
                    if short:
                        self.define_ent_ex(
                            False,
                            False,
                            presel.st.exits[symbol_complex].values[-1],
                            presel.st.entries[symbol_complex].values[-1],
                            presel.st.symbols_to_YF[symbol], 
                            "macd_vol",
                            exchange,
                            **kwargs
                            )
                    else:
                        self.define_ent_ex(
                            presel.st.entries[symbol_complex].values[-1],
                            presel.st.exits[symbol_complex].values[-1],
                            False,
                            False,
                            presel.st.symbols_to_YF[symbol], 
                            "macd_vol",
                            exchange,
                            **kwargs
                            ) 
  
            logger.info("Presel done for "+exchange)    

    def presel(self,st,exchange,**kwargs): #comes after daily report
        stock_ex=StockEx.objects.get(name=exchange)
        
        if stock_ex.presel_at_sector_level:
            if 'sec' in kwargs:
                sector=ActionSector.objects.get(name=kwargs.get("sec"))
                self.presel_sub(st.use_IB,sector.strategies_in_use.all(),st,exchange,**kwargs)
            else:    
                for s in ActionSector.objects.all(): #try for each sector
                    self.presel_sub(st.use_IB,s.strategies_in_use.all(),st,exchange,sec=s,**kwargs)
        else:
            self.presel_sub(st.use_IB,stock_ex.strategies_in_use.all(),st,exchange,**kwargs)
                           
#all symbols should be from same stock exchange

    def define_ent_ex(self,entries,exits,entries_short,exits_short,symbol, 
                      strategy, exchange, **kwargs):
        try:
            ent=False
            ex=False
            auto=False
            short=False
            action=Action.objects.get(symbol=symbol)
            if exchange is None: #for index
                exchange=action.stock_ex.name
            
            if entries and exits_short:
                ent, auto=reverse_order(symbol,strategy, exchange,short,True,**kwargs)
            elif entries_short and exits:
                short=True
                ex, auto=reverse_order(symbol,strategy, exchange,short,True,**kwargs)
            else:   
                if (entries_short and not exits_short) or (exits_short and not entries_short):
                    short=True
                #ent/ex and auto need to be re-evaluated: we want an entry in auto, but maybe there are limitation that will stop the execution or impose manual execution for instance
                if (entries and not exits) or (entries_short and not exits_short):
                    ent, auto=entry_order(symbol,strategy, exchange,short,True,**kwargs) #YF symbol expected here
                if (exits and not entries) or (exits_short and not entries_short):  
                    ex, auto=exit_order(symbol,strategy, exchange,short,True, **kwargs) #YF symbol expected here
                
            if ent or ex:
                logger_trade.info("define_ent_ex, Order executed short: " + str(short) + " symbol: " + symbol + " strategy: " + strategy)
                ent_ex_symbols, _=ListOfActions.objects.get_or_create(
                    report=self,
                    entry=ent,
                    short=short,
                    auto=auto
                    )
                ent_ex_symbols.actions.add(action)
                ent_ex_symbols.concat("define_ent_ex, Order executed short: " + str(short) + " symbol: " + symbol + " strategy: " + strategy)
        except Exception as e:
            print(e)
            logger.error(e, stack_info=True, exc_info=True)    
            
    def populate_report(self, symbols, symbols_to_YF,stnormal, st, sk, sma, sp):
        for symbol in symbols:
            if math.isnan(st.vol[symbol].values[-1]):
                self.concat("symbol " + symbol + " no data")
                
            else:
                with warnings.catch_warnings():
                    #Necessary because of the presence of NaN
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    ar=ActionReport(
                        action=Action.objects.get(symbol=symbols_to_YF[symbol]), 
                        report=Report.objects.get(pk=self.pk))
        
                    symbol_complex_ent_normal=stnormal.symbols_simple_to_complex(symbol,"ent")
                    symbol_complex_ex_normal=stnormal.symbols_simple_to_complex(symbol,"ex")
                    decision=stnormal.get_last_decision(symbol_complex_ent_normal,symbol_complex_ex_normal)
                    if decision==1:
                        ar.last_decision="sell"
                    elif decision==-1:
                        ar.last_decision="buy"

                    grow_past50_raw=st.grow_past(50, False)
                    grow_past50_ma=st.grow_past(50, True)
                    grow_past20_raw=st.grow_past(20, False)
                    grow_past20_ma=st.grow_past(20, True)
                    ar.date=st.date()
                    ar.vol=st.vol[symbol].values[-1]
                    
                    if _settings["CALCULATE_TREND"]:
                        symbol_complex_ent=st.symbols_simple_to_complex(symbol,"ent")
                        
                        ar.bbands_bandwith=st.bb_bw[symbol_complex_ent].values[-1]
                        ar.trend=float(st.trend[symbol_complex_ent].values[-1])
                        ar.macro_trend=float(st.macro_trend[symbol_complex_ent].values[-1])
                    
                    ar.three_mo_evol=grow_past50_raw[(50,False,symbol)].values[-1]
                    ar.three_mo_evol_sm=grow_past50_ma[(50,True,symbol)].values[-1]
                    ar.one_mo_evol=grow_past20_raw[(20,False,symbol)].values[-1]
                    ar.one_mo_evol_sm=grow_past20_ma[(20,True,symbol)].values[-1]
                    
                    
                    ar.kama_ent=sk.entries_kama[symbol].values[-1]
                    ar.kama_ex=sk.exits_kama[symbol].values[-1]
                    ar.kama_dir=float(sk.direction[symbol].values[-1])
            
                    ar.stoch_ent=sk.entries_stoch[symbol].values[-1]
                    ar.stoch_ex=sk.exits_stoch[symbol].values[-1]
                    
                    if math.isnan(sk.stoch[symbol].values[-1]):
                        ar.stoch=0
                    else:
                        ar.stoch=sk.stoch[symbol].values[-1]
                    
                    ar.ma_ent=sma.entries[symbol].values[-1]
                    ar.ma_ex=sma.exits[symbol].values[-1]
            
                    if _settings["CALCULATE_PATTERN"]:
                        ar.pattern_light_ent=sp.entries[(True, symbol)].values[-1] or\
                                             sp.entries[(True, symbol)].values[-2]
                                             
                        ar.pattern_light_ex=sp.exits[(True, symbol)].values[-1] or\
                                            sp.exits[(True, symbol)].values[-2]
            
                    if self.it_is_index:
                        if ar.kama_ent:
                            self.concat(" Index " + symbol + " KAMA bottom detected!")
                        if ar.kama_ex:
                            self.concat(" Index " + symbol + " KAMA top detected!")
                        if _settings["CALCULATE_TREND"]:    
                            if st.max_ind[symbol_complex_ent][-1]!=0:
                                self.concat(" Index " + symbol + " V maximum detected!")
                            if st.min_ind[symbol_complex_ent][-1]!=0:
                                self.concat(" Index " + symbol + " V minimum detected!")                            
                    ar.save()  
  
        
    def display_last_decision(self,symbol,stnormal, key):
        symbol_complex_ent_normal=stnormal.symbols_simple_to_complex(symbol,"ent")
        symbol_complex_ex_normal=stnormal.symbols_simple_to_complex(symbol,"ex")
        decision=stnormal.get_last_decision(symbol_complex_ent_normal,symbol_complex_ex_normal)
        if decision==1:
            self.concat(symbol + " present decision for "+str(key)+" strategy : sell")
        elif decision==-1:
            self.concat(symbol + " present decision for "+str(key)+" strategy : buy")
        return symbol_complex_ent_normal, symbol_complex_ex_normal
            
    #for a group of predefined actions, determine the signals    
    def perform_normal_strat(self,symbols, stnormal, exchange, **kwargs):
        if self.it_is_index:
            stnormal.call_strat(_settings["STRATEGY_NORMAL_INDEX"])
        else:
            stnormal.call_strat(_settings["STRATEGY_NORMAL_STOCKS"])
        
        normal_strat, _=Strategy.objects.get_or_create(name="normal")
        normal_strat_act, _=StratCandidates.objects.get_or_create(strategy=normal_strat)  #.id
        normal_strat_symbols=normal_strat_act.retrieve()
        
        for symbol in intersection(symbols,normal_strat_symbols):
            if math.isnan(stnormal.vol[symbol].values[-1]):
                self.concat("symbol " + symbol + " no data")
            else:
                symbol_complex_ent_normal, symbol_complex_ex_normal=self.display_last_decision(symbol,stnormal, "normal")
                
                #list present status
                self.define_ent_ex(
                    stnormal.entries[symbol_complex_ent_normal].values[-1],
                    stnormal.exits[symbol_complex_ex_normal].values[-1],
                    stnormal.entries_short[symbol_complex_ex_normal].values[-1],
                    stnormal.exits_short[symbol_complex_ent_normal].values[-1],
                    stnormal.symbols_to_YF[symbol], 
                    "normal",
                    exchange,
                    **kwargs)
                    
    def perform_sl_strat(self,symbols, stnormal, exchange, **kwargs):
        if self.it_is_index:
            stnormal.call_strat(_settings["STRATEGY_SL_INDEX"])
        else:
            stnormal.call_strat(_settings["STRATEGY_SL_STOCKS"])
        
        sl_strat, _=Strategy.objects.get_or_create(name="sl")
        sl_strat_act, _=StratCandidates.objects.get_or_create(strategy=sl_strat) 
        sl_strat_symbols=sl_strat_act.retrieve()
        
        for symbol in intersection(symbols,sl_strat_symbols):
            if math.isnan(stnormal.vol[symbol].values[-1]):
                self.concat("symbol " + symbol + " no data")
            else:
                symbol_complex_ent_normal, symbol_complex_ex_normal=self.display_last_decision(symbol,stnormal,"sl")
                
                #list present status
                self.define_ent_ex(
                    stnormal.entries[symbol_complex_ent_normal].values[-1],
                    stnormal.exits[symbol_complex_ex_normal].values[-1],
                    stnormal.entries_short[symbol_complex_ex_normal].values[-1],
                    stnormal.exits_short[symbol_complex_ent_normal].values[-1],
                    stnormal.symbols_to_YF[symbol], 
                    "sl",
                    exchange,
                    sl=0.005,
                    **kwargs)   
                    
        if self.it_is_index:
            stnormal.call_strat(_settings["STRATEGY_TSL_INDEX"])
        else:
            stnormal.call_strat(_settings["STRATEGY_TSL_STOCKS"])
        
        tsl_strat, _=Strategy.objects.get_or_create(name="tsl")
        tsl_strat_act, _=StratCandidates.objects.get_or_create(strategy=tsl_strat) 
        tsl_strat_symbols=tsl_strat_act.retrieve()
        
        for symbol in intersection(symbols,tsl_strat_symbols):
            if math.isnan(stnormal.vol[symbol].values[-1]):
                self.concat("symbol " + symbol + " no data")
            else:
                symbol_complex_ent_normal, symbol_complex_ex_normal=self.display_last_decision(symbol,stnormal,"tsl")
                
                #list present status
                self.define_ent_ex(
                    stnormal.entries[symbol_complex_ent_normal].values[-1],
                    stnormal.exits[symbol_complex_ex_normal].values[-1],
                    stnormal.entries_short[symbol_complex_ex_normal].values[-1],
                    stnormal.exits_short[symbol_complex_ent_normal].values[-1],
                    stnormal.symbols_to_YF[symbol], 
                    "tsl",
                    exchange,
                    daily_sl=0.005,
                    **kwargs)                       

    def perform_keep_strat(self,symbols, stnormal, exchange, **kwargs):
        if not self.it_is_index:
            stnormal.call_strat(_settings["STRATEGY_RETARD_KEEP"])

            pf_keep=get_pf("retard_keep",exchange,False,**kwargs)
            pf_short_keep=get_pf("retard_keep",exchange,True,**kwargs)
            
            for symbol in symbols:
                if symbol in pf_keep.retrieve():
                    self.concat("symbol presently in keep: "+symbol)
                    symbol_complex_ent_normal, symbol_complex_ex_normal=self.display_last_decision(symbol,stnormal,"keep")

                    self.define_ent_ex(
                        False, #only exit
                        stnormal.exits[symbol_complex_ex_normal].values[-1],
                        False,
                        False,
                        stnormal.symbols_to_YF[symbol], 
                        "retard_keep",
                        exchange,
                        **kwargs)
                if symbol in pf_short_keep.retrieve(): 
                    self.concat("symbol presently in keep short: "+symbol)
                    symbol_complex_ent_normal, symbol_complex_ex_normal=self.display_last_decision(symbol,stnormal,"keep")
                    self.define_ent_ex(
                        False, #only exit
                        False,
                        False,
                        stnormal.exits_short[symbol_complex_ent_normal].values[-1],
                        stnormal.symbols_to_YF[symbol], 
                        "retard_keep",
                        exchange,
                        **kwargs)
                        
    def perform_slow_strats(self, symbols, strats, exchange, st, **kwargs):   
        # Slow candidates
        try:
            slow_strats=[Strategy.objects.get(name="hist_slow"),\
                         Strategy.objects.get(name="realmadrid")] #only those in use
            slow_strats_active=[]
            slow_cands={}
            
            for s in intersection(strats,slow_strats):
                slow_strats_active.append(s)
                if not self.it_is_index and exchange is not None: 
                    cand=get_candidates(s.name,exchange)
                    slow_cands[s.name]=cand.retrieve()
                else:
                    slow_cands[s.name]=[]   
                     
            ##Change underlying strategy
            st.call_strat("strat_kama_stoch_matrend_bbands")             
            for symbol in symbols:
                symbol_complex_ent=st.symbols_simple_to_complex(symbol,"ent")                            
                
                for s in slow_strats_active:
                    if st.symbols_to_YF[symbol] in slow_cands[s.name]: #list of candidates
                        self.define_ent_ex(
                            st.entries[symbol_complex_ent].values[-1],
                            st.exits[symbol_complex_ent].values[-1],
                            False, #both strategy use only long
                            False,
                            st.symbols_to_YF[symbol], 
                            s.name,
                            exchange,
                            **kwargs)
        except:
            print("check that hist_slow and realmadrid strategies are created")                
                        
    def perform_divergence(self,symbols,exchange, st, strats, **kwargs):
        try:
            s=Strategy.objects.get(name="divergence")
        except:
            print("check that divergence strategy is created") 
            pass
        
        try: 
            if not self.it_is_index and exchange is not None: #index
                #even if divergence is not anymore used, we should be able to exit
                pf_div=get_pf("divergence",exchange,False,**kwargs)
                self.concat("symbols in divergence: " +str(pf_div.retrieve()))
                ##Change underlying strategy
                st.call_strat("stratDiv")
                st.entries.columns.values
                
                ##only_exit_substrat
                if len(pf_div.retrieve())>0:
                    for symbol in symbols:
                        symbol_complex_ent=st.symbols_simple_to_complex(symbol,"ent")  
                        
                        if s in strats and\
                                st.symbols_to_YF[symbol] in pf_div.retrieve() and st.exits[symbol_complex_ent].values[-1]: 
    
                                logger_trade.info("Divergence exit " + str(st.exits[symbol_complex_ent].values[-1]))    
 
                                self.define_ent_ex(
                                    False,
                                    st.exits[symbol_complex_ent].values[-1],
                                    False,
                                    False,
                                    st.symbols_to_YF[symbol], 
                                    s.name,
                                    exchange,
                                    **kwargs)
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
    
    	Optional arguments
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
                #symbols=kwargs.get("symbols",[])
                use_IB=False
                if _settings["USE_IB_FOR_DATA"]["reporting"]:
                    use_IB=check_ib_permission(symbols)
                actions=[Action.objects.get(symbol=symbol) for symbol in symbols]
            else: #actions, exchange is provided
                use_IB, actions=get_exchange_actions(exchange,**kwargs)
            
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
                    
                #load the data and
                #calculats everything used afterwards
                #also used for "normal strat"
                stnormal=stratP.StratPRD(use_IB,actions1=actions,period1=str(_settings["DAILY_REPORT_PERIOD"])+"y",**kwargs)
                
                ##Perform a single strategy on predefined actions
                self.perform_normal_strat(stnormal.symbols, stnormal, exchange, **kwargs)
                
                ##Populate a report with different statistics
                sk=ic.VBTSTOCHKAMA.run(stnormal.high,stnormal.low,stnormal.close)
                sma=ic.VBTMA.run(stnormal.close)

                sp=None
                if _settings["CALCULATE_PATTERN"]:
                    sp=ic.VBTPATTERN.run(stnormal.open,stnormal.high,stnormal.low,stnormal.close,light=True)
                
                st=stratP.StratPRD(use_IB,
                                        actions1=actions,
                                        open_=stnormal.open,
                                        high=stnormal.high,
                                        low=stnormal.low,
                                        close=stnormal.close,
                                        volume=stnormal.volume,
                                        data=stnormal.data,
                                        open_ind=stnormal.open_ind,
                                        high_ind=stnormal.high_ind,
                                        low_ind=stnormal.low_ind,
                                        close_ind=stnormal.close_ind, 
                                        volume_ind=stnormal.volume_ind,
                                        data_ind=stnormal.data_ind,
                                        **kwargs)

                if _settings["CALCULATE_TREND"]:
                    st.call_strat("strat_kama_stoch_matrend_macdbb_macro") #for the trend

                self.populate_report(stnormal.symbols, stnormal.symbols_to_YF, stnormal,st, sk, sma, sp)
                logger.info("Strat daily report written " +(exchange or ""))

                self.perform_sl_strat(stnormal.symbols, stnormal, exchange, **kwargs)
                #using tsl strategy
                self.perform_keep_strat(stnormal.symbols, stnormal, exchange, **kwargs)
                ##Perform strategies that rely on the regular preselection of a candidate
                self.perform_slow_strats(stnormal.symbols, strats, exchange, st, **kwargs)
                
                ##Perform the strategy divergence, the exit to be precise, the entry are performed by presel
                self.perform_divergence(stnormal.symbols,exchange, st, strats, **kwargs)

                logger.info("Slow strategy proceeded") 
                if sec is not None:
                    self.sector=ActionSector.objects.get(name=sec) 
                self.save()
                return st

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

