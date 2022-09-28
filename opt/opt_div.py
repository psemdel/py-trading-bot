from core import indicators as ic
from core.common import VBTfunc
from core.macro import VBTMACROTREND, VBTMACROMODE, VBTMACROFILTER
from core import bt

import vectorbtpro as vbt
from vectorbtpro.utils.config import Config
import numpy as np
import gc
import copy
from core.constants import BEAR_PATTERNS, BULL_PATTERNS

#Script to optimize the underlying combination of patterns/signals used for a given preselection strategy
#Divergence use only exit signal from the underlying strategies, no need to variate the entry strategy

#The optimization takes place on the actions from CAC40, DAX and Nasdaq
#Parameters very good on some actions but very bad for others should not be selected

#The optimization algorithm calculates one point, look for the points around it and select the best one
#As it can obviously lead to local maximum, the starting point is selected in a random manner

vbt.settings['caching']=Config(
    disable=True,
    disable_whitelist=True,
    disable_machinery=True,
    silence_warnings=False,
    register_lazily=True,
    ignore_args=[
        'jitted',
        'chunked'
    ],
    use_cached_accessors=True
)

def log(text):
    filename="div.txt"
    #print(text)
    with open("opt/output/"+filename, "a") as f:
        f.write("\n"+str(text))  

class Opt(VBTfunc):
    def __init__(self,period,**kwargs):
        
        self.close_dic={}
        self.open_dic={}
        self.low_dic={}
        self.high_dic={}
        self.bti={}
        self.indexes=["CAC40", "DAX", "NASDAQ", "IT","FIN"] #
        #
       
        #self.indexes=["CAC40", "DAX", "NASDAQ", "IT","REALESTATE","INDUSTRY","STAPLES", #"COM"
        #              "HEALTHCARE","CONSUMER","FIN","COM","ENERGY","UTILITIES"]
        
        for ind in self.indexes:
            self.bti[ind]=bt.BT(ind,period,"test","long")
            self.close_dic[ind]=self.bti[ind].close
            self.open_dic[ind]=self.bti[ind].open
            self.low_dic[ind]=self.bti[ind].low
            self.high_dic[ind]=self.bti[ind].high    
            
        self.out={}
        
        #init
        self.init_threshold=-1000 
        
        self.len_ent=7+len(BULL_PATTERNS)
        self.len_ex=7+len(BEAR_PATTERNS)
        self.arr=[] #arr of the last step, variation are performed afterwards
        self.calc_arr=[] #for calculation in pf

        self.predefined=kwargs.get("predefined",False) #to start from a predefined point
        self.a_bull_init=kwargs.get("a_bull")
        self.a_bear_init=kwargs.get("a_bear")
        self.a_uncertain_init=kwargs.get("a_uncertain")
        
        if self.predefined:
            self.loops=1
        else:
            self.loops=kwargs.get("loops",3)
        
        self.tested_arrs=None
        self.nb_macro_modes=kwargs.get('nb_macro_modes',3)
        
        self.fees=kwargs.get("fees",0.0005)
        
        self.best_arrs=np.zeros((self.loops*40,self.nb_macro_modes,self.len_ent+self.len_ex))
        self.best_arrs_ret=np.zeros(self.loops*40)
        self.best_arrs_index=0
        
        self.best_end_arrs=np.zeros((self.loops*2,self.nb_macro_modes,self.len_ent+self.len_ex)) #final results
        self.best_end_arrs_ret=np.zeros(self.loops*2)
        self.best_end_arrs_index=0
        
        self.best_all=np.zeros(1)
        self.best_all_ret=self.init_threshold
        
        #append used only once
        self.all_t_ents={}
        self.all_t_exs={}
        
        self.arrs=[]
        self.tested_arrs={}
        
        if self.nb_macro_modes==3:
            self.macro_trend_bull={}
            self.macro_trend_bear={}
            self.macro_trend_uncertain={}
            self.macro_trend={}
            
            self.macro_trend_bull_mode=kwargs.get('macro_trend_bull','long')
            self.macro_trend_bear_mode=kwargs.get('macro_trend_bear','long')
            self.macro_trend_uncertain_mode=kwargs.get('macro_trend_uncertain','long')
            
            for ind in self.indexes:
                t=VBTMACROTREND.run(self.close_dic[ind])
                self.macro_trend[ind]=t.macro_trend
        
        #all entries and exits for all patterns and signals are calculated once and for all here
        self.defi_i()
        print("init finished")
    
    def defi_i(self):
        for ind in self.indexes: #CAC, DAX, NASDAQ
            all_t_ex=[]
            open_=self.open_dic[ind]
            high=self.high_dic[ind]
            low=self.low_dic[ind]
            close=self.close_dic[ind]
            
            t=ic.VBTMA.run(close)
            all_t_ex.append(t.exits)
            
            t=ic.VBTSTOCHKAMA.run(high,low,close)
            all_t_ex.append(t.exits_stoch)    

            all_t_ex.append(t.exits_kama)   

            t=ic.VBTSUPERTREND.run(high,low,close)
            all_t_ex.append(t.exits)
                            
            t=vbt.BBANDS.run(close)
            all_t_ex.append(t.upper_below(close))

            t=vbt.RSI.run(close)
            all_t_ex.append(t.rsi_crossed_above(80))
            
            all_t_ex.append(t.rsi_crossed_above(70))
                
            for func_name in BEAR_PATTERNS:
                t=ic.VBTPATTERNONE.run(open_,high,low,close,func_name, "ex").out
                all_t_ex.append(t)  
              
            self.all_t_exs[ind]=all_t_ex
            
        del t
        gc.collect()        
    #to translate the binary array in human readable information
    def interpret_ent(self,arr_input):
        self.interpret(arr_input, "ent")
 
    def interpret_ex(self,arr_input):
        self.interpret(arr_input, "ex")

    def interpret(self,arr_input,ent_or_ex):
        if ent_or_ex=="ent":
            arr=arr_input[0:self.len_ent] 
            patterns=BULL_PATTERNS
        else:
            arr=arr_input[self.len_ent:self.len_ent+self.len_ex]  
            patterns=BEAR_PATTERNS
        
        l=["MA","STOCH","KAMA","STOCHKAMA","BBANDS","RSI20","RSI30"]
        for _, k in enumerate(patterns):
            l.append(k)

        for ii in range(len(arr)):
            if arr[ii]:
                print(l[ii])   
                log(l[ii])   
    
    #put the patterns/signals together (OR)
    #note: this is the time consuming operation
   
    def defi_ex(self):
        self.exs={}
        self.exs_short={}
        self.defi("ex")
    
    def defi(self,ent_or_ex):
        try:
            for ind in self.indexes: #CAC, DAX, NASDAQ
                ents_raw=None 
                
                for nb_macro_mode in range(self.nb_macro_modes): #bull, bear, uncertain
                    calc_arr=self.calc_arrs[nb_macro_mode]
    
                    arr=calc_arr[self.len_ent:self.len_ent+self.len_ex]  
                
                    for ii in range(len(arr)):
                        if arr[ii]:
                            t=self.all_t_exs[ind][ii]
                        
                            if ents_raw is None:
                                ents_raw=t
                            else:
                                ents_raw=ic.VBTOR.run(ents_raw,t).out
                                
                    if ents_raw is None:
                        raise ValueError
                    
                    if self.nb_macro_modes==1:
                        ent=ents_raw
                    else:
                        if nb_macro_mode==0:
                            ent=VBTMACROFILTER.run(ents_raw,self.macro_trend[ind],-1).out
                        elif nb_macro_mode==1:
                            ents_raw=VBTMACROFILTER.run(ents_raw,self.macro_trend[ind],1).out
                            ent=ic.VBTOR.run(ent, ents_raw).out
                        else:
                            ents_raw=VBTMACROFILTER.run(ents_raw,self.macro_trend[ind],0).out
                            ent=ic.VBTOR.run(ent, ents_raw).out                    
                
                if ent_or_ex=="ent":
                    self.ents[ind]=ent
                else:
                    self.exs[ind]=ent
                    
            del t, arr
        except ValueError:
            print("ents_raw was zero!")
    

    def calculate_eq_ret(self,pf):
        m_rb=pf.total_market_return
        m_rr=pf.get_total_return()
        
        if abs(m_rb)<0.1: #avoid division by zero
            p=(m_rr)/ 0.1*np.sign(m_rb)   
        else:
            p=(m_rr- m_rb )/ abs(m_rb)

        return 4*p*(p<0) + p*(p>0) #wrong direction for the return are penalyzed
    
    def summarize_eq_ret(self,ret_arr):
        while np.std(ret_arr)>10:
            ii=np.argmax(ret_arr)
            ret_arr=np.delete(ret_arr,ii,0)
            
        return np.mean(ret_arr)
        
  
    def manual_calculate_pf(self,ind,*args): #the order is bull/bear/uncertain
        self.calc_arrs=[]
        for arr in args:
            self.calc_arrs.append(arr)
        
        self.defi_ent()
        self.defi_ex()
        pf=vbt.Portfolio.from_signals(self.close_dic[ind], self.ents[ind],self.exs[ind],
                                      freq="1d",fees=self.fees)

        print("equivalent return " + str(self.calculate_eq_ret(pf)))
        return pf #for display for instance
    
    def calculate_pf(self, best_arrs_cand, best_ret_cand, best_arrs_ret):
        found=0
        
        for nb_macro_mode in range(self.nb_macro_modes):
            if nb_macro_mode in self.tested_arrs:
                if any((self.tested_arrs[nb_macro_mode][:]==self.calc_arrs[nb_macro_mode]).all(1)): #in np.array
                    found+=1
    
        if found==self.nb_macro_modes: #same combination
            return best_arrs_cand, best_ret_cand
        elif nb_macro_mode in self.tested_arrs:
            self.tested_arrs[nb_macro_mode]=np.append(self.tested_arrs[nb_macro_mode], [self.calc_arrs[nb_macro_mode]],axis=0)
        else:
            self.tested_arrs[nb_macro_mode]=[self.calc_arrs[nb_macro_mode]]

        #create the underlying strategy
        self.defi_ex()
            
        ret=0
        ret_arr=[]

        for ind in self.indexes: #CAC, DAX, NASDAQ
            self.bti[ind].overwrite_ex_strat11(self.exs[ind])
            self.bti[ind].preselect_divergence()

            pf=vbt.Portfolio.from_signals(self.bti[ind].close, 
                                          self.bti[ind].entries,
                                          self.bti[ind].exits,
                                          #short_entries=self.bti[ind].entries_short,
                                          #short_exits=self.bti[ind].exits_short,
                                          freq="1d",fees=self.fees,
                                          call_seq='auto',cash_sharing=True,)
            
            ret_arr.append(self.calculate_eq_ret(pf))

        ret=self.summarize_eq_ret(ret_arr)
        trades =len(pf.get_trades().records_arr)
        del pf
        
        if ret> best_arrs_ret and ret>best_ret_cand and trades>50:
            return self.calc_arrs, ret
        
        return best_arrs_cand, best_ret_cand

    def random(self):
        #choose randomly 0 and 1. All zeros is not accepted.
        arr=np.zeros(self.len_ent+self.len_ex)
        
        while np.sum(arr[0:self.len_ent] )==0 or np.sum(arr[self.len_ent:self.len_ent+self.len_ex])==0:
            for ii in range(len(arr)):
               arr[ii]=np.random.choice(np.arange(0, 2), p=[0.9, 0.1])   
        return arr
    
    #define here a predefined starting point
    def predef(self):
        arr=[]
        arr.append(np.array(self.a_bull_init))
        arr.append(np.array(self.a_bear_init))
        arr.append(np.array(self.a_uncertain_init))
        return arr
        
    #variates the array, if it is better, the new array is returned otherwise the original one
    def variate(self, best_arrs_ret):
        best_arrs_cand=[]
        best_ret_cand=self.init_threshold
            
        for nb_macro_mode in range(self.nb_macro_modes): 
            for ii in range(self.len_ent,len(self.arrs[nb_macro_mode])): #variates only the exit
                self.calc_arrs=copy.deepcopy(self.arrs)
                
                if self.arrs[nb_macro_mode][ii]==0:
                    self.calc_arrs[nb_macro_mode][ii]=1
                else:
                    self.calc_arrs[nb_macro_mode][ii]=0

                if np.sum(self.calc_arrs[nb_macro_mode][0:self.len_ent] )!=0 and np.sum(self.calc_arrs[nb_macro_mode][self.len_ent:self.len_ent+self.len_ex])!=0:
                    best_arrs_cand, best_ret_cand=self.calculate_pf(best_arrs_cand, best_ret_cand, best_arrs_ret)

        return best_arrs_cand, best_ret_cand
        
    def perf(self):
        for jj in range(self.loops):
            print("loop " + str(jj))
            log("loop " + str(jj))
            self.arrs=[]
            
            #new start point
            found=self.nb_macro_modes
            
            if self.predefined:
                self.arrs=self.predef()
                self.arrs=self.arrs[0:self.nb_macro_modes]
                
            else:
                while found==self.nb_macro_modes:
                    found=0
    
                    arr=self.random()
                    for nb_macro_mode in range(self.nb_macro_modes):
                        if nb_macro_mode in self.tested_arrs:
                            if any((self.tested_arrs[nb_macro_mode][:]==arr).all(1)):
                                found+=1
                                        
                for nb_macro_mode in range(self.nb_macro_modes):
                    self.arrs.append(arr.copy())

            self.calc_arrs=copy.deepcopy(self.arrs)

            best_arrs_cand, best_ret_cand=self.calculate_pf([],self.init_threshold,self.init_threshold) #reset 
            if best_ret_cand>self.init_threshold: #normally true
                self.best_arrs[self.best_arrs_index,:,:]= best_arrs_cand
                self.best_arrs_ret[self.best_arrs_index]=best_ret_cand
                self.best_arrs_index+=1
            
            #start divergence
            calc=True
            
            while calc:
                print("next calc")
                best_arrs_cand, best_ret_cand=self.variate(best_ret_cand)
                
                if best_ret_cand>self.init_threshold:
                    self.best_arrs[self.best_arrs_index,:,:]= best_arrs_cand
                    self.best_arrs_ret[self.best_arrs_index]=best_ret_cand
                    self.best_arrs_index+=1
                    log(best_arrs_cand)
                    log(best_ret_cand)
                    
                    #next step
                    self.arrs=best_arrs_cand
                else:
                    calc=False
                    self.best_end_arrs[self.best_end_arrs_index,:]= self.best_arrs[self.best_arrs_index-1,:]
                    self.best_end_arrs_ret[self.best_end_arrs_index]=self.best_arrs_ret[self.best_arrs_index-1]
                    self.best_end_arrs_index+=1

                    if self.best_all_ret==self.init_threshold or self.best_arrs_ret[self.best_arrs_index-1]>self.best_all_ret:
                        self.best_all=self.best_arrs[self.best_arrs_index-1,:]
                        self.best_all_ret=self.best_arrs_ret[self.best_arrs_index-1]
            gc.collect()     
       
        log("algorithm completed")
              
        log("best of all")
        log({'arr':self.best_all})
        log("return : " + str(self.best_all_ret))
        log("ent")
        print("ent")
        if self.nb_macro_modes==3:
            print("bull")
            log("bull")
        self.interpret_ent(self.best_all[0,:])
        
        if self.nb_macro_modes==3:
            print("bear")
            log("bear")
            self.interpret_ent(self.best_all[1,:])
            print("uncertain")
            log("uncertain")
            self.interpret_ent(self.best_all[2,:])
        log("ex")
        print("ex")
        if self.nb_macro_modes==3:
            print("bull")
            log("bull")
        self.interpret_ex(self.best_all[0,:])
        
        if self.nb_macro_modes==3:
            print("bear")
            log("bear")
            self.interpret_ex(self.best_all[1,:])
            print("uncertain")
            log("uncertain")
            self.interpret_ex(self.best_all[2,:])

     