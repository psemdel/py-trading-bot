from django.db import models

import math

from trading_bot.settings import _settings

from core import stratP, btP
from core import indicators as ic
import warnings
import logging
logger = logging.getLogger(__name__)
logger_trade = logging.getLogger('trade')

from orders.ib import exit_order, entry_order, reverse_order

from orders.models import Action, get_pf, get_candidates,\
                          get_exchange_actions,\
                          StratCandidates, StockEx, Strategy, ActionSector,\
                          check_ib_permission, filter_intro_action
      
##Temporary storage for the telegram to message the orders at the end of the reporting.
##Difficulty is that the telegram bot is async, so it is not possible to just make send_msg() in the order execution function
class ListOfActions(models.Model):
    report=models.ForeignKey('Report',on_delete=models.CASCADE)
    entry=models.BooleanField(blank=False,default=False) #otherwise exit
    short=models.BooleanField(blank=False,default=False)
    auto=models.BooleanField(blank=False,default=False)
    actions=models.ManyToManyField(Action,blank=True,related_name="symbols") 

class Report(models.Model):
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

    def daily_report_index(self,symbols):
        use_IB=False
        if _settings["USE_IB_FOR_DATA"]:
            use_IB=check_ib_permission(symbols)
        actions=[]
        
        for symbol in symbols:
            actions.append(Action.objects.get(symbol=symbol))
        
        return self.daily_report(actions,None,use_IB,index=True)  #exchange is none
        
    def daily_report_action(self,exchange,**kwargs):
        use_IB, actions=get_exchange_actions(exchange,**kwargs)
        return self.daily_report(actions,exchange,use_IB,**kwargs) 

### Logic for buying and selling actions preselected with retard strategy
    def candidates_to_YF(self,symbols_to_YF, candidates):
        candidates_YF=[]
        for c in candidates:
            candidates_YF.append(symbols_to_YF[c])
        return candidates_YF

    def retard(self,presel,exchange,st,**kwargs):
        #key="retard"+"_"+exchange
        if _settings["RETARD_MACRO"]:
            presel.call_strat("preselect_retard_macro")
        else:
            presel.call_strat("preselect_retard")
        
        candidates, candidates_short=presel.get_candidates()
        
        if presel.last_short:
            direction="short"
        else:
            direction="long"

        self.concat("Retard, " + "direction " + direction + ", stockex: " + exchange +\
                    ", action duration: " +str(presel.out))
        
        short=False
        if len(candidates)==0:
            short=True
            candidates=candidates_short
            
        auto=True
        self.order_nosubstrat(self.candidates_to_YF(st.symbols_to_YF,candidates), exchange, "retard", short, auto,**kwargs) #retard can be automatized

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
                ex, auto=exit_order(symbol,key, exchange,short, auto,**kwargs)
                self.order_nosubstrat_sub(symbol, short, ex, auto)

        #sell
        pf=get_pf(key,exchange,short,**kwargs)
        for symbol in pf.retrieve():
            if symbol not in candidates:
                if kwargs.get("keep",False):
                    action=Action.objects.get(symbol=symbol)
                    pf_keep.append(action) #move the symbol from retard to keep pf
                    pf.remove(action)
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
        for nb in range(102):
            key="wq"+str(nb)
            DIC_PRESEL=_settings["DIC_PRESEL"]
            if key in DIC_PRESEL[exchange]:
                to_calculate=True
        
        if to_calculate:
            wq=btP.WQPRD(st.use_IB,st=st,exchange=exchange)
            
            for nb in range(102):
                key="wq"+str(nb)
                if key in DIC_PRESEL[exchange]:
                    wq.call_wqa(nb)
                    wq.def_cand()
                    candidates=wq.get_candidates()
                    
                    self.order_nosubstrat(self.candidates_to_YF(st.symbols_to_YF,candidates), exchange, key,False,auto,**kwargs) #fees are too high on IB for wq strategy
            logger.info("Presel wq done for "+exchange)  
            
### Preselected actions strategy    
    def presel_sub(self,use_IB,l,st, exchange,**kwargs):
        if len([v for v in ["retard","macd_vol","divergence", "retard_keep"] if v in l])!=0:
            presel=btP.Presel(use_IB,st=st,exchange=exchange)
            #hist slow does not need code here
            if "retard" in l:   #auto is handled by DIC_PERFORM_ORDER in settings
                self.retard(presel,exchange,st,**kwargs)
            if "retard_keep" in l:
                self.retard(presel,exchange,st,keep=True,**kwargs)
            if "divergence" in l:    
                if _settings["DIVERGENCE_MACRO"]:
                    presel.call_strat("preselect_divergence_blocked")
                else:
                    presel.call_strat("preselect_divergence")
                
                candidates, _=presel.get_candidates()
                self.order_only_exit_substrat(self.candidates_to_YF(st.symbols_to_YF,candidates), exchange, "divergence", False,**kwargs)
            if "macd_vol" in l:
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
        #NYSE needs to be subdivided
        if exchange=="NYSE":
            DIC_PRESEL_SECTOR=_settings["DIC_PRESEL_SECTOR"]
            if 'sec' in kwargs:
                self.presel_sub(st.use_IB,DIC_PRESEL_SECTOR[kwargs['sec']],st,exchange,**kwargs)
            else:    
                for e in DIC_PRESEL_SECTOR: #try for each sector
                    self.presel_sub(st.use_IB,DIC_PRESEL_SECTOR[e],st,exchange,sec=e,**kwargs)
        else:
            DIC_PRESEL=_settings["DIC_PRESEL"]
            DICS=[DIC_PRESEL[exchange]]
            for l in DICS:
                self.presel_sub(st.use_IB,l,st,exchange,**kwargs)
                           
#all symbols should be from same stock exchange

    def define_ent_ex(self,entries,exits,entries_short,exits_short,symbol, 
                      strategy, exchange, **kwargs):
        ent=False
        ex=False
        auto=False
        short=False
        
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
            
        action=Action.objects.get(symbol=symbol)
        if ent or ex:
            logger_trade.info("define_ent_ex, Order executed short: " + str(short) + " symbol: " + symbol + " strategy: " + strategy)
            ent_ex_symbols, _=ListOfActions.objects.get_or_create(
                report=self,
                entry=ent,
                short=short,
                auto=auto
                )
            ent_ex_symbols.actions.add(action)
            
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
        
        
    def display_last_decision(self,symbol,stnormal):
        symbol_complex_ent_normal=stnormal.symbols_simple_to_complex(symbol,"ent")
        symbol_complex_ex_normal=stnormal.symbols_simple_to_complex(symbol,"ex")
        decision=stnormal.get_last_decision(symbol_complex_ent_normal,symbol_complex_ex_normal)
        if decision==1:
            self.concat(symbol + " present decision : sell")
        elif decision==-1:
            self.concat(symbol + " present decision : buy")
        return symbol_complex_ent_normal, symbol_complex_ex_normal
            
    #for a group of predefined actions, determine the signals    
    def perform_normal_strat(self,symbols, stnormal, exchange, **kwargs):
        if self.it_is_index:
            stnormal.stratIndexB()
        else:
            stnormal.stratG()
        
        normal_strat, _=Strategy.objects.get_or_create(name="normal")
        normal_strat_act, _=StratCandidates.objects.get_or_create(name="normal",strategy=normal_strat)  #.id
        normal_strat_symbols=normal_strat_act.retrieve()
        
        for symbol in symbols:
            if symbol in normal_strat_symbols:
                if math.isnan(stnormal.vol[symbol].values[-1]):
                    self.concat("symbol " + symbol + " no data")
                else:
                    symbol_complex_ent_normal, symbol_complex_ex_normal=self.display_last_decision(symbol,stnormal)
                    
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
            stnormal.stratIndexSL()
        else:
            stnormal.stratSL()
        
        sl_strat, _=Strategy.objects.get_or_create(name="sl")
        sl_strat_act, _=StratCandidates.objects.get_or_create(name="sl",strategy=sl_strat) 
        sl_strat_symbols=sl_strat_act.retrieve()
        
        for symbol in symbols:
            if symbol in sl_strat_symbols:
                if math.isnan(stnormal.vol[symbol].values[-1]):
                    self.concat("symbol " + symbol + " no data")
                else:
                    symbol_complex_ent_normal, symbol_complex_ex_normal=self.display_last_decision(symbol,stnormal)
                    
                    #list present status
                    self.define_ent_ex(
                        stnormal.entries[symbol_complex_ent_normal].values[-1],
                        stnormal.exits[symbol_complex_ex_normal].values[-1],
                        stnormal.entries_short[symbol_complex_ex_normal].values[-1],
                        stnormal.exits_short[symbol_complex_ent_normal].values[-1],
                        stnormal.symbols_to_YF[symbol], 
                        "normal",
                        exchange,
                        sl=0.005,
                        **kwargs)   
                    
        if self.it_is_index:
            stnormal.stratIndexTSL()
        else:
            stnormal.stratTSL()
        
        tsl_strat, _=Strategy.objects.get_or_create(name="tsl")
        tsl_strat_act, _=StratCandidates.objects.get_or_create(name="tsl",strategy=tsl_strat) 
        tsl_strat_symbols=tsl_strat_act.retrieve()
        
        for symbol in symbols:
            if symbol in tsl_strat_symbols:
                if math.isnan(stnormal.vol[symbol].values[-1]):
                    self.concat("symbol " + symbol + " no data")
                else:
                    symbol_complex_ent_normal, symbol_complex_ex_normal=self.display_last_decision(symbol,stnormal)
                    
                    #list present status
                    self.define_ent_ex(
                        stnormal.entries[symbol_complex_ent_normal].values[-1],
                        stnormal.exits[symbol_complex_ex_normal].values[-1],
                        stnormal.entries_short[symbol_complex_ex_normal].values[-1],
                        stnormal.exits_short[symbol_complex_ent_normal].values[-1],
                        stnormal.symbols_to_YF[symbol], 
                        "normal",
                        exchange,
                        daily_sl=0.005,
                        **kwargs)                       

    def perform_keep_strat(self,symbols, stnormal, exchange, **kwargs):
        if not self.it_is_index:
            #stnormal.stratF()
            
            pf_keep=get_pf("retard_keep",exchange,False,**kwargs)
            pf_short_keep=get_pf("retard_keep",exchange,True,**kwargs)
            
            for symbol in symbols:
                if symbol in pf_keep.retrieve():
                    self.concat("symbol presently in keep: "+symbol)
                    symbol_complex_ent_normal, symbol_complex_ex_normal=self.display_last_decision(symbol,stnormal)

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
                    symbol_complex_ent_normal, symbol_complex_ex_normal=self.display_last_decision(symbol,stnormal)
                    self.define_ent_ex(
                        False, #only exit
                        False,
                        False,
                        stnormal.exits_short[symbol_complex_ent_normal].values[-1],
                        stnormal.symbols_to_YF[symbol], 
                        "retard_keep",
                        exchange,
                        **kwargs)
                        
    def perform_slow_strats(self, symbols, DICS, exchange, st, **kwargs):   
        # Slow candidates
        slow_strats=["hist_slow", "realmadrid"] #only those in use
        slow_strats_active=[]
        slow_cands={}
        
        #=intersection(DICS,slow_strats) 
        for DIC in DICS:
            if DIC in slow_strats:
                slow_strats_active.append(DIC)
                if not self.it_is_index and exchange is not None: 
                    cand=get_candidates(DIC,exchange)
                    slow_cands[DIC]=cand.retrieve()
                else:
                    slow_cands[DIC]=[]   
                 
        ##Change underlying strategy
        st.call_strat("strat_kama_stoch_matrend_bbands")             
        for symbol in symbols:
            symbol_complex_ent=st.symbols_simple_to_complex(symbol,"ent")                            
            
            for DIC in slow_strats_active:
                if st.symbols_to_YF[symbol] in slow_cands[DIC]: #list of candidates
                    self.define_ent_ex(
                        st.entries[symbol_complex_ent].values[-1],
                        st.exits[symbol_complex_ent].values[-1],
                        False, #both strategy use only long
                        False,
                        st.symbols_to_YF[symbol], 
                        DIC,
                        exchange,
                        **kwargs)
                        
    def perform_divergence(self,symbols,exchange, st, DIC_PRESEL, DICS, **kwargs):
        
        if exchange is not None and "divergence" in DIC_PRESEL[exchange]: 
            pf_div=get_pf("divergence",exchange,False,**kwargs)
            self.concat("symbols in divergence: " +str(pf_div.retrieve()))
        ##Change underlying strategy
        st.call_strat("stratDiv")
        ##only_exit_substrat

        for symbol in symbols:
            symbol_complex_ent=st.symbols_simple_to_complex(symbol,"ent")                            
            
            if "divergence" in DICS and exchange is not None and\
                    st.symbols_to_YF[symbol] in pf_div.retrieve(): 
                    logger_trade.info("Divergence exit " + str(st.exits[symbol_complex_ent].values[-1]))    
                        
                    self.define_ent_ex(
                        False,
                        st.exits[symbol_complex_ent].values[-1],
                        False,
                        False,
                        st.symbols_to_YF[symbol], 
                        "divergence",
                        exchange,
                        **kwargs)
    
    def daily_report(self,actions,exchange,use_IB,**kwargs): #for one exchange and one sector
        try: 
            sec=kwargs.get("sec")
            self.it_is_index=kwargs.get("index",False)
            if exchange is not None:
                self.stock_ex=StockEx.objects.get(name=exchange)
                if exchange=="NYSE":
                    DIC_PRESEL_SECTOR=_settings["DIC_PRESEL_SECTOR"]
                    if kwargs.get("sec"):
                        try:
                            #sector=ActionSector.objects.get(name=) 
                            DICS=DIC_PRESEL_SECTOR[kwargs.get("sec")]
                        except:
                            logger.warning("sector not found: " + str(kwargs.get("sec")))
                            pass
                else:
                    DIC_PRESEL=_settings["DIC_PRESEL"]
                    DICS=[DIC_PRESEL[exchange]]
            else:
                self.stock_ex=StockEx.objects.get(name="Paris") #convention
                DICS=[]
  
            if len(actions)!=0:
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
                self.perform_keep_strat(stnormal.symbols, stnormal, exchange, **kwargs)
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
                                        open_ind=stnormal.open_ind,
                                        high_ind=stnormal.high_ind,
                                        low_ind=stnormal.low_ind,
                                        close_ind=stnormal.close_ind, 
                                        volume_ind=stnormal.volume_ind,
                                       **kwargs)

                if _settings["CALCULATE_TREND"]:
                    st.call_strat("strat_kama_stoch_matrend_macdbb_macro") #for the trend
                
                self.populate_report(stnormal.symbols, stnormal.symbols_to_YF, stnormal,st, sk, sma, sp)
                logger.info("Strat daily report written " +(exchange or ""))
                
                
                self.perform_sl_strat(stnormal.symbols, stnormal, exchange, **kwargs)

                ##Perform strategies that rely on the regular preselection of a candidate
                self.perform_slow_strats(stnormal.symbols, DICS, exchange, st, **kwargs)
                
                ##Perform the strategy divergence, the exit to be precise, the entry are performed by presel
                self.perform_divergence(stnormal.symbols,exchange, st, _settings["DIC_PRESEL"], DICS, **kwargs)

                logger.info("Slow strategy proceeded") 
                if sec is not None:
                    self.sector=ActionSector.objects.get(name=sec) 
                self.save()
                return st

        except ValueError as e:
            logger.error(e, stack_info=True, exc_info=True)
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            pass 
    
class ActionReport(models.Model):
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

