from django.db import models
from django.contrib.postgres.fields import ArrayField

import sys
import math

from trading_bot.settings import (DIC_PRESEL, DIC_PRESEL_SECTOR, DIVERGENCE_MACRO, RETARD_MACRO,
                                 DAILY_REPORT_PERIOD)

from core import stratP, btP
from core import indicators as ic
import warnings
from datetime import datetime

from core.constants import INTRO

from orders.models import Action, entry_order,\
                          exit_order, Index, get_pf, get_candidates,\
                          get_exchange_actions,\
                          StratCandidates, StockEx, Strategy, ActionSector
                     

#which strategy to use for which stockexchange

class Report(models.Model):
    date=models.DateTimeField(null=False, blank=False, auto_now_add=True)   #default=timezone.now())
    text=models.TextField(blank=True)
    ent_symbols=ArrayField(models.CharField(max_length=200), blank=True, null=True,default=list)
    ex_symbols=ArrayField(models.CharField(max_length=200), blank=True, null=True,default=list)
    ent_symbols_short=ArrayField(models.CharField(max_length=200), blank=True, null=True,default=list)
    ex_symbols_short=ArrayField(models.CharField(max_length=200), blank=True, null=True,default=list)
    ent_symbols_manual=ArrayField(models.CharField(max_length=200), blank=True, null=True,default=list)
    ex_symbols_manual=ArrayField(models.CharField(max_length=200), blank=True, null=True,default=list)
    ent_symbols_short_manual=ArrayField(models.CharField(max_length=200), blank=True, null=True,default=list)
    ex_symbols_short_manual=ArrayField(models.CharField(max_length=200), blank=True, null=True,default=list)

    stock_ex=models.ForeignKey('orders.StockEx',on_delete=models.CASCADE,null=True)
    it_is_index=models.BooleanField(blank=False,default=False)
    sector=models.ForeignKey('orders.ActionSector',on_delete=models.CASCADE,blank=True,default=10)
    
    def __str__(self):
        return str(self.date)
    
    class Meta:
        ordering = ['-date', 'stock_ex']
    
    def get_ent_ex_symbols(self):
        return self.ent_symbols, self.ex_symbols, self.ent_symbols_short, self.ex_symbols_short,\
               self.ent_symbols_manual, self.ex_symbols_manual, self.ent_symbols_short_manual,\
                   self.ex_symbols_short_manual
    
    def concat(self,text):
        print(text)     
        self.text+=text +"\n"
        self.save()

    def daily_report_index(self,symbols):
        return self.daily_report(symbols,None,index=True)  #exchange is none
        
    def daily_report_action(self,exchange,**kwargs):
        symbols=get_exchange_actions(exchange,**kwargs)
        return self.daily_report(symbols,exchange,**kwargs) 

### Logic for buying and selling actions preselected with retard strategy
    def retard(self,presel,exchange,**kwargs):
        #key="retard"+"_"+exchange
        if RETARD_MACRO:
            presel.call_strat("preselect_retard_macro")
        else:
            presel.call_strat("preselect_retard")
            
        auto=kwargs.get("auto",True)
        candidates, candidates_short=presel.get_candidates()
        
        if presel.last_short:
            direction="short"
        else:
            direction="long"

        self.concat("Retard, " + "direction " + direction + ", stockex: " + exchange +\
                    ", action duration: " +str(presel.res))
        
        short=False
        if len(candidates)==0:
            short=True
            candidates=candidates_short
        
        self.order_nostrat11(candidates, exchange, "retard", short, auto) #retard can be automatized

    def order_only_exit_strat11(self,candidates, exchange, key, short,**kwargs):
        auto=kwargs.get("auto",True)
        if len(candidates)==0:
            self.concat(key +" no candidates")        
        
        #buy without condition
        for symbol in candidates:
            self.concat(key +" candidates " + symbol)
            ent, auto=entry_order(symbol,key, exchange,short, auto,**kwargs)

            if ent:
                if auto:
                    if short:
                        self.ent_symbols_short.append(symbol)
                    else:
                        self.ent_symbols.append(symbol)
                else:
                    if short:
                        self.ent_symbols_short_manual.append(symbol)
                    else:
                        self.ent_symbols_manual.append(symbol)          

    def order_nostrat11_sub(self,symbol, short, ex, auto):
        if ex:
            if auto:
                if short:
                    self.ex_symbols_short.append(symbol)
                else:
                    self.ex_symbols.append(symbol)
            else:
                if short:
                    self.ex_symbols_short_manual.append(symbol)
                else:
                    self.ex_symbols_manual.append(symbol)         
        

    def order_nostrat11(self,candidates, exchange, key, short,auto,**kwargs):
        #if there is a reversal the opposite pf needs to emptied
        pf_inv=get_pf(key,exchange,not short)
        for symbol in pf_inv.retrieve():
            if symbol not in candidates:
                ex, auto=exit_order(symbol,key, exchange,short, auto,**kwargs)
                self.order_nostrat11_sub(symbol, short, ex, auto)
        
        #sell
        pf=get_pf(key,exchange,short)
        for symbol in pf.retrieve():
            if symbol not in candidates:
                ex, auto=exit_order(symbol,key, exchange,short,auto, **kwargs)
                self.order_nostrat11_sub(symbol, short, ex, auto)
        
        if len(candidates)==0:
            self.concat(key +" no candidates")
        
        #buy
        for symbol in candidates:
            self.concat(key +" candidates " + symbol)
            
            ent, auto=entry_order(symbol,key, exchange,short,auto, **kwargs)
            if ent:
                if auto:
                    if short:
                        self.ent_symbols_short.append(symbol)
                    else:
                        self.ent_symbols.append(symbol)
                else:
                    if short:
                        self.ent_symbols_short_manual.append(symbol)
                    else:
                        self.ent_symbols_manual.append(symbol)                    
         
### Preselected actions strategy, using 101 Formulaic Alphas
    def presel_wq(self,st,exchange,**kwargs):
        to_calculate=False
        auto=kwargs.get("auto",True)
        for nb in range(102):
            key="wq"+str(nb)
            if key in DIC_PRESEL[exchange]:
                to_calculate=True
         
        if to_calculate:
            wq=btP.WQPRD(st=st,exchange=exchange)
            
            for nb in range(102):
                key="wq"+str(nb)
                if key in DIC_PRESEL[exchange]:
                    wq.call_wqa(nb)
                    wq.def_cand()
                    candidates=wq.get_candidates()
                    self.order_nostrat11(candidates, exchange, key,False,auto) #fees are too high on IB for wq strategy
            print("Presel wq done for "+exchange)  
            
### Preselected actions strategy    
    def presel(self,st,exchange,**kwargs): #comes after daily report
        #NYSE needs to be subdivided
        if exchange=="NYSE":
            DICS=DIC_PRESEL_SECTOR
        else:
            DICS=[DIC_PRESEL[exchange]]
            
        for DIC in DICS:
            if len([v for v in ["retard","macd_vol","divergence","retard_manual"] if v in DIC])!=0:
                presel=btP.Presel(st=st,exchange=exchange)
                #hist slow does not need code here
                if "retard" in DIC:  
                    self.retard(presel,exchange)
                if "retard_manual" in DIC:
                    self.retard(presel,exchange,auto=False)
                if "divergence" in DIC:     
                    if DIVERGENCE_MACRO:
                        presel.call_strat("preselect_divergence_blocked")
                    else:
                        presel.call_strat("preselect_divergence")
                    
                    candidates, _=presel.get_candidates()
                    self.order_only_exit_strat11(candidates, exchange, "divergence", False,**kwargs)
                if "macd_vol" in DIC:
                    presel.call_strat("preselect_macd_vol_macro")
                    candidates, candidates_short=presel.get_candidates()
                    
                    if len(candidates)==0:
                        short=True
                        cand=candidates_short
                    else:
                        short=False
                        cand=candidates
                        
                    for symbol in cand:
                        symbol_complex=st.symbols_simple_to_complex(symbol)
                        if short:
                            #only entries and exits is populated
                            self.define_ent_ex(
                                st.exits_short[symbol_complex].values[-1],
                                st.entries_short[symbol_complex].values[-1],
                                st.exits[symbol_complex].values[-1],
                                st.entries[symbol_complex].values[-1],
                                symbol, 
                                "macd_vol",
                                exchange,
                                )
                        else:
                            self.define_ent_ex(
                                st.entries[symbol_complex].values[-1],
                                st.exits[symbol_complex].values[-1],
                                st.entries_short[symbol_complex].values[-1],
                                st.exits_short[symbol_complex].values[-1],
                                symbol, 
                                "macd_vol",
                                exchange,
                                ) 
      
                print("Presel done for "+exchange)                    
                    
#all symbols should be from same stock exchange
    def define_ent_ex(self,entries,exits,entries_short,exits_short,symbol, 
                      strategy, exchange, **kwargs):
        ent=False
        ex=False
        ent_short=False
        ex_short=False
        auto=False
       
        if entries and not exits:
            ent, auto=entry_order(symbol,strategy, exchange,False,True,**kwargs)
        if exits and not entries:
            ex, auto=exit_order(symbol,strategy, exchange,False,True, **kwargs)  
        if entries_short and not exits_short:
            ent_short, auto=entry_order(symbol,strategy, exchange,True,True,**kwargs)
        if exits_short and not entries_short:
            ex_short, auto=exit_order(symbol,strategy, exchange,True,True,**kwargs)
            
        if auto:
            if ent:
                self.ent_symbols.append(symbol)
            if ex:
                self.ex_symbols.append(symbol) 
            if ent_short:
                self.ent_symbols_short.append(symbol)
            if ex_short:
                self.ex_symbols_short.append(symbol) 
        else:
            if ent:
                self.ent_symbols_manual.append(symbol)
            if ex:
                self.ex_symbols_manual.append(symbol) 
            if ent_short:
                self.ent_symbols_short_manual.append(symbol)
            if ex_short:
                self.ex_symbols_short_manual.append(symbol) 
                
    def daily_report(self,input_symbols,exchange,**kwargs):
        try: 
            self.it_is_index=kwargs.get("index",False)
            if exchange is not None:
                self.stock_ex=StockEx.objects.get(name=exchange)
                if exchange=="NYSE":
                    DICS=DIC_PRESEL_SECTOR
                    if kwargs.get("sector"):
                        try:
                            self.sector=ActionSector.objects.get(name=kwargs.get("sector")) 
                        except:
                            print("sector not found")
                            pass
                else:
                    DICS=[DIC_PRESEL[exchange]]
            else:
                self.stock_ex=StockEx.objects.get(name="Paris") #convention
                DICS=[]
  
            if input_symbols!=[]:
                if self.pk is None:
                    self.save()
                    
                #clean the symbols
                symbols=[]
                td=datetime.today()
                min_y=td.year-DAILY_REPORT_PERIOD
                limit_date=str(min_y)+"-" + str(td.month) + "-" + str(td.day)
                
                for s in input_symbols:
                    if s in INTRO: #should come from database
                        if INTRO[s]<limit_date:
                            symbols.append(s)
                    else:
                        symbols.append(s)
                
                st=stratP.StratPRD(symbols,str(DAILY_REPORT_PERIOD)+"y",**kwargs)
                st.call_strat("strat_kama_stoch_matrend_macdbb_macro") #for the trend
                
                #calculates everything used afterwards
                #also used for "normal strat"
                stnormal=stratP.StratPRD(symbols,str(DAILY_REPORT_PERIOD)+"y",
                                        open_=st.open,
                                        high=st.high,
                                        low=st.low,
                                        close=st.close,
                                        open_ind=st.open_ind,
                                        high_ind=st.high_ind,
                                        low_ind=st.low_ind,
                                        close_ind=st.close_ind,                                        
                                         **kwargs)
                if self.it_is_index:
                    stnormal.stratIndex()
                else:
                    stnormal.stratF()
                
                sk=ic.VBTSTOCHKAMA.run(st.high,st.low,st.close)
                sma=ic.VBTMA.run(st.close)
                sp=ic.VBTPATTERN.run(st.open,st.high,st.low,st.close,light=True)
                
                grow_past50_raw=st.grow_past(50, False)
                grow_past50_ma=st.grow_past(50, True)
                grow_past20_raw=st.grow_past(20, False)
                grow_past20_ma=st.grow_past(20, True)
                normal_strat_act=StratCandidates.objects.get(strategy=Strategy.objects.get(name="normal")) 
                normal_strat_symbols=normal_strat_act.retrieve()
                
                # Slow candidates
                slow_strats=["hist_slow", "realmadrid"] #only those in use
                slow_cands={}
                
                for DIC in DICS:
                    for slow_strat in slow_strats:
                        if not self.it_is_index and exchange is not None and slow_strat in DIC: 
                            cand=get_candidates(slow_strat,exchange)
                            slow_cands[slow_strat]=cand.retrieve()
                        else:
                            slow_cands[slow_strat]=[]   

                if exchange is not None and "divergence" in DIC_PRESEL[exchange]: 
                    pf_div=get_pf("divergence",exchange,False)
                
                for symbol in symbols:
                    symbol_complex_ent=st.symbols_simple_to_complex(symbol,"ent")
                    #symbol_complex_ex=st.symbols_simple_to_complex(symbol,"ex")
                    
                    with warnings.catch_warnings():
                        #Necessary because of the presence of NaN
                        warnings.simplefilter("ignore", category=RuntimeWarning)
                        
                        if self.it_is_index:
                            action=Index.objects.get(symbol=symbol)
                            ar=ActionReport(index=action, 
                                                   report=Report.objects.get(pk=self.pk))
                        else:
                            action=Action.objects.get(symbol=symbol)
                            ar=ActionReport(action=action, 
                                                   report=Report.objects.get(pk=self.pk))
                        
                        ar.date=st.date()
                        ar.vol=st.vol[symbol].values[-1]
                        
                        ar.bbands_bandwith=st.bb_bw[symbol_complex_ent].values[-1]
                        
                        ar.three_mo_evol=grow_past50_raw[(50,False,symbol)].values[-1]
                        ar.three_mo_evol_sm=grow_past50_ma[(50,True,symbol)].values[-1]
                        ar.one_mo_evol=grow_past20_raw[(20,False,symbol)].values[-1]
                        ar.one_mo_evol_sm=grow_past20_ma[(20,True,symbol)].values[-1]
                        ar.trend=float(st.trend[symbol_complex_ent].values[-1])
                        ar.macro_trend=float(st.macro_trend[symbol_complex_ent].values[-1])
                        
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

                        ar.pattern_light_ent=sp.entries[(True, symbol)].values[-1] or\
                                             sp.entries[(True, symbol)].values[-2]
                                             
                        ar.pattern_light_ex=sp.exits[(True, symbol)].values[-1] or\
                                            sp.exits[(True, symbol)].values[-2]

                        if self.it_is_index:
                            if ar.kama_ent:
                                self.concat(" Index " + symbol + " KAMA bottom detected!")
                            if ar.kama_ex:
                                self.concat(" Index " + symbol + " KAMA top detected!")
                            if st.max_ind[symbol_complex_ent][-1]!=0:
                                self.concat(" Index " + symbol + " V maximum detected!")
                            if st.min_ind[symbol_complex_ent][-1]!=0:
                                self.concat(" Index " + symbol + " V minimum detected!")                            

                        ar.save()  
                        
                        if symbol in normal_strat_symbols:
                            symbol_complex_ent_normal=stnormal.symbols_simple_to_complex(symbol,"ent")
                            symbol_complex_ex_normal=stnormal.symbols_simple_to_complex(symbol,"ex")
                            
                            #list present status
                            
                            self.define_ent_ex(
                                stnormal.entries[symbol_complex_ent_normal].values[-1],
                                stnormal.exits[symbol_complex_ex_normal].values[-1],
                                stnormal.entries_short[symbol_complex_ex_normal].values[-1],
                                stnormal.exits_short[symbol_complex_ent_normal].values[-1],
                                symbol, 
                                "normal",
                                exchange,
                                **kwargs)
                            decision=stnormal.get_last_decision(symbol_complex_ent_normal,symbol_complex_ex_normal)
                            if decision==1:
                                self.concat(symbol + " present decision : sell")
                            elif decision==-1:
                                self.concat(symbol + " present decision : buy")
                print("Strat daily report written " +(exchange or ""))
                            
                ##Change underlying strategy
                st.call_strat("strat_kama_stoch_matrend_bbands")             
                for symbol in symbols:
                    symbol_complex_ent=st.symbols_simple_to_complex(symbol,"ent")                            
                    
                    for DIC in DICS:
                        for slow_strat in slow_strats:
                            if symbol in slow_cands[slow_strat]:
                                self.define_ent_ex(
                                    st.entries[symbol_complex_ent].values[-1],
                                    st.exits[symbol_complex_ent].values[-1],
                                    st.entries_short[symbol_complex_ent].values[-1],
                                    st.exits_short[symbol_complex_ent].values[-1],
                                    symbol, 
                                    slow_strat,
                                    exchange,
                                    **kwargs)
                        
                        ##only_exit_strat11
                        if exchange is not None and "divergence" in DIC and\
                            symbol in pf_div.retrieve(): 
                            self.define_ent_ex(
                                False,
                                st.exits[symbol_complex_ent].values[-1],
                                False,
                                st.exits_short[symbol_complex_ent].values[-1],
                                symbol, 
                                "divergence",
                                exchange,
                                **kwargs)
                print("Slow strategy proceeded") 
                self.save()
                return st
                
        except Exception as msg:
            print("exception in " + __name__)
            print(msg)
            _, e_, exc_tb = sys.exc_info()
            print("line " + str(exc_tb.tb_lineno))
            pass 
    
class ActionReport(models.Model):
    report=models.ForeignKey('Report',on_delete=models.CASCADE)
    action=models.ForeignKey('orders.Action',on_delete=models.CASCADE, null=True,default=None)
    index=models.ForeignKey('orders.Index',on_delete=models.CASCADE, null=True,default=None)
    
    date=models.CharField(max_length=100, blank=True)
 
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
        elif self.index is not None:
            return self.index.name + " " + str(self.report.date)
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
    index=models.ForeignKey('orders.Index',on_delete=models.CASCADE,null=True,default=None)

    def __str__(self):
        if self.action is not None:
            return self.action.name   + " " + str(self.trigger_date)
        elif self.index is not None:
            return self.index.name  + " " + str(self.trigger_date)
        else:
            return "none" + " " + str(self.trigger_date)

