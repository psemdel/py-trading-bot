from core import indicators as ic
from core.common import VBTfunc
from core.macro import VBTMACROTREND, VBTMACROMODE, VBTMACROFILTER

import vectorbtpro as vbt
from vectorbtpro.utils.config import Config
import numpy as np
import gc
import copy
from core.constants import BEAR_PATTERNS, BULL_PATTERNS, mode_to_int
from core.common import remove_multi
import itertools
import pandas as pd
import math

import os

#Script to optimize the combination of patterns/signals used for a given strategy

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

def log(text,**kwargs):
    with open(os.path.join(os.path.dirname(__file__), "output/"+ kwargs.get("filename","strat")+".txt"), "a") as f:
        f.write("\n"+str(text))  
        
    if kwargs.get("pr",False):
        print(text)

class OptMain(VBTfunc):
    def __init__(self,period,**kwargs):
        self.indexes=["CAC40", "DAX", "NASDAQ","IT"]
        self.index=kwargs.get("index",False)
        
        #init
        for key in ["close","open","low","high","data"]:
            setattr(self,key+"_dic",{})
            
            for ind in self.indexes:
                getattr(self,key+"_dic")[ind]={}
        
        self.ratio_learn_train=kwargs.get("ratio_learn_train",80)
        self.split_learn_train=kwargs.get("split_learn_train","time")
        self.total_len={}

        for ind in self.indexes:
            super().__init__(ind,period)
            if self.index:
                self.suffix="_ind"
            else:
                self.suffix=""
            
            if self.split_learn_train=="time":
                self.total_len[ind]=len(getattr(self,"close"+self.suffix))
            else: #symbol
                self.total_len[ind]=len(getattr(self,"close"+self.suffix).columns)
            learn_len=int(math.floor(self.ratio_learn_train/100*self.total_len[ind]))
            test_len=self.total_len[ind]-learn_len
            self.test_window_start=kwargs.get("test_window_start",np.random.randint(0,learn_len))
            self.test_window_end=self.test_window_start+test_len
            log("random test start at index number " + ind + " for : "+str(self.test_window_start) +
                ", "+str(self.close.index[self.test_window_start]) +", "+\
                "until index number: "+str(self.test_window_end) + ", "+str(self.close.index[self.test_window_end])
                )
            for d in ["close","open","low","high"]:
                getattr(self,d+"_dic")[ind]["total"]=getattr(self,d+self.suffix) #ind already implicitely mentioned
                
                if self.split_learn_train=="time": 
                    getattr(self,d+"_dic")[ind]["test"]=getattr(self,d+self.suffix).iloc[self.test_window_start:self.test_window_end]
                    getattr(self,d+"_dic")[ind]["learn"]=pd.concat([getattr(self,d+self.suffix).iloc[0:self.test_window_start],
                                                   getattr(self,d+self.suffix).iloc[self.test_window_end:]])
                else: #symbol
                    getattr(self,d+"_dic")[ind]["test"]=getattr(self,d+self.suffix).iloc[:,self.test_window_start:self.test_window_end]
                    if self.test_window_start==0:
                        getattr(self,d+"_dic")[ind]["learn"]=getattr(self,d+self.suffix).iloc[:,self.test_window_end:]
                    elif self.test_window_end==np.shape(getattr(self,d+self.suffix))[1]:
                        getattr(self,d+"_dic")[ind]["learn"]=getattr(self,d+self.suffix).iloc[:,0:self.test_window_start]
                    else:
                        getattr(self,d+"_dic")[ind]["learn"]= pd.concat([getattr(self,d+self.suffix).iloc[:,0:self.test_window_start],
                                                    getattr(self,d+self.suffix).iloc[:,self.test_window_end:]])
        #data to be solved    
        #self.data.indexing_func(pd.DataFrame.iloc,index=getattr(self,d+"_dic")[ind]["learn"].index)                                      
        #voir vbt
        self.out={}
        
        #init
        self.init_threshold=-1000 
        
        self.confidence_threshold=60
        
        self.non_pattern_len=7
        self.len_ent=self.non_pattern_len+len(BULL_PATTERNS)
        self.len_ex=self.non_pattern_len+len(BEAR_PATTERNS)
        
        self.a_init={}
        for key in ["bull","bear","uncertain"]:
            self.a_init[key]=kwargs.get("a_"+key)
           
        self.nb_macro_modes=kwargs.get('nb_macro_modes',3)
        self.predefined=kwargs.get("predefined",False) #to start from a predefined point
        if self.predefined:
            self.arrs=self.predef()
            self.calc_arrs=copy.deepcopy(self.arrs)
            self.loops=1
        else:
            self.arrs=[] #arr of the last step, variation are performed afterwards
            self.calc_arr=[] #for calculation in pf
            self.loops=kwargs.get("loops",3)

        self.fees=kwargs.get("fees",0.0005)
        self.sl=kwargs.get("sl")
        self.tsl=kwargs.get("tsl")
        
        self.init_best_arr()
        
        #append used only once
        self.all_t_ents={}
        self.all_t_exs={}
        for ind in self.indexes:
            self.all_t_ents[ind]={}
            self.all_t_exs[ind]={}
        
        self.macro_trend={}
        self.macro_trend_mode={}
        self.macro_trend_dir={}
        
        if self.nb_macro_modes==3:
            for key in ["bull","bear","uncertain"]:
                self.macro_trend_dir[key]={}
                self.macro_trend_mode[key]=kwargs.get('macro_trend_'+key,'long')

            for ind in self.indexes:
                self.macro_trend[ind]={}
                for k in ["total","learn","test"]:
                    self.macro_trend[ind][k]=VBTMACROTREND.run(self.close_dic[ind][k]).macro_trend

        #all entries and exits for all patterns and signals are calculated once and for all here
        self.threshold=1
        self.defi_i("learn")
        
        self.shift=False
        print("init finished")
        
    def init_best_arr(self):
        self.tested_arrs=[]
        
        self.best_arrs=np.zeros((self.loops*1000,self.nb_macro_modes,self.len_ent+self.len_ex))
        self.best_arrs_ret=np.zeros(self.loops*1000)
        self.best_arrs_index=0
        
        self.best_end_arrs=np.zeros((self.loops*100,self.nb_macro_modes,self.len_ent+self.len_ex)) #final results
        self.best_end_arrs_ret=np.zeros(self.loops*100)
        self.best_end_arrs_index=0
        
        self.best_all=np.zeros(1)
        self.best_all_ret=self.init_threshold        
    
    def defi_i(self,key):
        for ind in self.indexes: #CAC, DAX, NASDAQ
            all_t_ent=[]
            all_t_ex=[]
            open_=self.open_dic[ind][key]
            high=self.high_dic[ind][key]
            low=self.low_dic[ind][key]
            close=self.close_dic[ind][key]
            
            t=ic.VBTMA.run(close)
            all_t_ent.append(t.entries)
            all_t_ex.append(t.exits)
            
            t=ic.VBTSTOCHKAMA.run(high,low,close)
            all_t_ent.append(t.entries_stoch)
            all_t_ex.append(t.exits_stoch)    

            all_t_ent.append(t.entries_kama)
            all_t_ex.append(t.exits_kama)   

            t=ic.VBTSUPERTREND.run(high,low,close)
            all_t_ent.append(t.entries)
            all_t_ex.append(t.exits)
                            
            t=vbt.BBANDS.run(close)
            all_t_ent.append(t.lower_above(close))
            all_t_ex.append(t.upper_below(close))

            t=vbt.RSI.run(close)
            all_t_ent.append(t.rsi_crossed_below(20))
            all_t_ex.append(t.rsi_crossed_above(80))
            
            all_t_ent.append(t.rsi_crossed_below(30))
            all_t_ex.append(t.rsi_crossed_above(70))

            for func_name in BULL_PATTERNS:
                t=ic.VBTPATTERNONE.run(open_,high,low,close,func_name, "ent").out
                all_t_ent.append(t)
                
            for func_name in BEAR_PATTERNS:
                t=ic.VBTPATTERNONE.run(open_,high,low,close,func_name, "ex").out
                all_t_ex.append(t)  

            self.all_t_ents[ind][key]=all_t_ent
            self.all_t_exs[ind][key]=all_t_ex
            
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
        
        l=["MA","STOCH","KAMA","SUPERTREND","BBANDS","RSI20","RSI30"]
        for _, k in enumerate(patterns):
            l.append(k)

        for ii in range(len(arr)):
            if arr[ii]:
                log(l[ii],pr=True)   
    
    #put the patterns/signals together (OR)
    #note: this is the time consuming operation
    def defi_ent(self,key):
        self.ents={}
        self.ents_short={}
        self.defi("ent",key)
    
    def defi_ex(self,key):
        self.exs={}
        self.exs_short={}
        self.defi("ex",key)
        
    def defi(self,ent_or_ex,key):
        try:
            for ind in self.indexes: #CAC, DAX, NASDAQ
                for nb_macro_mode in range(self.nb_macro_modes): #bull, bear, uncertain
                    ents_raw=None 
                    calc_arr=self.calc_arrs[nb_macro_mode]
                    
                    if ent_or_ex=="ent":
                        arr=calc_arr[0:self.len_ent] 
                    else:
                        arr=calc_arr[self.len_ent:self.len_ent+self.len_ex]  
                
                    s=np.full(np.shape(self.all_t_ents[ind][key][0]),0.0)
                    
                    for ii in range(len(arr)):
                        if ent_or_ex=="ent":
                            t=self.all_t_ents[ind][key][ii]
                        else:
                            t=self.all_t_exs[ind][key][ii]
                        
                        t2=ic.VBTSUM.run(t,arr=arr[ii]).out #equivalent to if arr[ii]: then consider self.all_t_ents[ind][key][ii]
                        t2=remove_multi(t2)
                        
                        if self.shift:
                            t_shift=ic.VBTSUM.run(t2.shift(periods=1, fill_value=0),self.shift_arr[0]).out
                            t_shift+=ic.VBTSUM.run(t2.shift(periods=2, fill_value=0),self.shift_arr[1]).out
                            s+=t_shift
                        s+=t2

                    ents_raw=(s>=self.threshold)
                       
                    if self.nb_macro_modes==1:
                        ent=ents_raw
                    else:
                        if nb_macro_mode==0:
                            ent=VBTMACROFILTER.run(ents_raw,self.macro_trend[ind][key],-1).out
                        elif nb_macro_mode==1:
                            ents_raw=VBTMACROFILTER.run(ents_raw,self.macro_trend[ind][key],1).out
                            ent=ic.VBTOR.run(ent, ents_raw).out
                        else:
                            ents_raw=VBTMACROFILTER.run(ents_raw,self.macro_trend[ind][key],0).out
                            ent=ic.VBTOR.run(ent, ents_raw).out   
                
                if ent_or_ex=="ent":
                    self.ents[ind]=ent
                else:
                    if "test" not in key:
                        ent.iloc[self.test_window_start-1,:]=True #exit all before the gap due to the exit
                    self.exs[ind]=ent
                    
            del t, arr
        except Exception as msg:
            import sys
            _, _, exc_tb = sys.exc_info()
            print("line " + str(exc_tb.tb_lineno))
            print(msg)
            print(ent)
        except ValueError:
            print("ents_raw was zero!")
        
    def macro_mode(self,key):
        try:
            if (self.nb_macro_modes ==1 or
               self.macro_trend_mode["bull"]=='long' and self.macro_trend_mode["bear"]=='long' 
               and self.macro_trend_mode["uncertain"]=='long'):
                for ind in self.indexes: 
                    self.ents_short[ind]=np.full(self.ents[ind].shape,False)
                    self.exs_short[ind]=np.full(self.ents[ind].shape,False)
            else:
                for ind in self.indexes: #CAC, DAX, NASDAQ
                    t=VBTMACROMODE.run(self.ents[ind],self.exs[ind], self.macro_trend[ind][key],\
                                       macro_trend_bull=self.macro_trend_mode["bull"],
                                       macro_trend_bear=self.macro_trend_mode["bear"],
                                       macro_trend_uncertain=self.macro_trend_mode["uncertain"])
                    self.ents[ind]=t.entries
                    self.exs[ind]=t.exits
                    self.ents_short[ind]=t.entries_short
                    self.exs_short[ind]=t.exits_short 
        except Exception as msg:      
            print(msg)
            print(self.macro_trend.__dir__())              

    def check_tested_arrs(self,**kwargs):
        #merge all list, it makes the rest more simple
        if self.nb_macro_modes==3:
            a=list(itertools.chain(self.calc_arrs[0],self.calc_arrs[1],self.calc_arrs[2]))
        else:
            a=list(self.calc_arrs[0])
                    
        if a in self.tested_arrs: #same combination
            return False
        else:
            if not kwargs.get("just_test",False):
                self.tested_arrs.append(a)
            return True

    def random(self):
        #choose randomly 0 and 1. All zeros is not accepted.
        arr=np.random.choice(2,self.len_ent+self.len_ex, p=[0.9, 0.1]) 
        
        while np.sum(arr[0:self.len_ent] )==0 or np.sum(arr[self.len_ent:self.len_ent+self.len_ex])==0:#entries or exits must not be full 0
            arr=np.random.choice(2,self.len_ent+self.len_ex, p=[0.9, 0.1]) 

        return arr
    
    def summarize_eq_ret(self,ret_arr):
        while np.std(ret_arr)>10:
            ii=np.argmax(ret_arr)
            ret_arr=np.delete(ret_arr,ii,0)
            
        return np.mean(ret_arr)
    
    #define here a predefined starting point
    def predef(self,**kwargs):
        if kwargs.get("dicho",False):
            d=self.a_dicho
        else:
            d=self.a_init
        
        if self.nb_macro_modes==1:
            return [np.array(d["bull"])]
        else:
            return [np.array(d["bull"]), np.array(d["bear"]), np.array(d["uncertain"])]
        
    #variates the array, if it is better, the new array is returned otherwise the original one
    def variate(self, best_arrs_ret,**kwargs):
        best_arrs_cand=[]
        best_ret_cand=self.init_threshold
            
        for nb_macro_mode in range(self.nb_macro_modes): 
            for ii in range(len(self.arrs[nb_macro_mode])):
                self.calc_arrs=copy.deepcopy(self.arrs)
                
                if self.arrs[nb_macro_mode][ii]==0:
                    self.calc_arrs[nb_macro_mode][ii]=1
                else:
                    self.calc_arrs[nb_macro_mode][ii]=0

                if np.sum(self.calc_arrs[nb_macro_mode][0:self.len_ent] )!=0 and np.sum(self.calc_arrs[nb_macro_mode][self.len_ent:self.len_ent+self.len_ex])!=0:
                    best_arrs_cand_temp, best_ret_cand_temp=self.calculate_pf(best_arrs_cand, best_ret_cand, best_arrs_ret,**kwargs)
                    ### To test confidence at each round --> turn out to exclude break the progresses
                    #if best_ret_cand_temp>best_ret_cand:
                    #    if self.test(verbose=0,**kwargs)>self.confidence_threshold:
                    best_arrs_cand=best_arrs_cand_temp
                    best_ret_cand=best_ret_cand_temp

        return best_arrs_cand, best_ret_cand                

    def perf(self,**kwargs):
        for jj in range(self.loops):
            log("loop " + str(jj),pr=True)
            
            #new start point
            if not self.predefined:
                self.arrs=[]
                ok=False
                while not ok:
                    arr=self.random()
                    for nb_macro_mode in range(self.nb_macro_modes):
                        self.arrs.append(arr.copy())
                    self.calc_arrs=copy.deepcopy(self.arrs)
                    ok=self.check_tested_arrs(just_test=True)
            
            best_arrs_cand, best_ret_cand=self.calculate_pf([],self.init_threshold,self.init_threshold,**kwargs) #reset 
            if best_ret_cand>self.init_threshold: #normally true
                self.best_arrs[self.best_arrs_index,:,:]= best_arrs_cand
                self.best_arrs_ret[self.best_arrs_index]=best_ret_cand
                self.best_arrs_index+=1
            
            #start variations
            calc=True
            
            while calc:
                print("next calc")
                best_arrs_cand, best_ret_cand=self.variate(best_ret_cand,**kwargs)
                if best_ret_cand>self.init_threshold:
                    self.best_arrs[self.best_arrs_index,:,:]= best_arrs_cand
                    self.best_arrs_ret[self.best_arrs_index]=best_ret_cand
                    self.best_arrs_index+=1
                    
                    #next step
                    self.arrs=best_arrs_cand
                    self.test(**kwargs)
                else:
                    calc=False
                    self.best_end_arrs[self.best_end_arrs_index,:]= self.best_arrs[self.best_arrs_index-1,:]
                    self.best_end_arrs_ret[self.best_end_arrs_index]=self.best_arrs_ret[self.best_arrs_index-1]
                    self.best_end_arrs_index+=1
    
                    if self.best_all_ret==self.init_threshold or self.best_arrs_ret[self.best_arrs_index-1]>self.best_all_ret:
                        self.best_all=self.best_arrs[self.best_arrs_index-1,:]
                        self.best_all_ret=self.best_arrs_ret[self.best_arrs_index-1]
                
            gc.collect()     
       
        if self.nb_macro_modes==3:
            keys=["bull","bear","uncertain"]
        else:
            keys=["bull"]
        log("algorithm completed")
 
        log("best of all")
        log({'arr':self.best_all})
        log("return : " + str(self.best_all_ret))
        
        log("ent",pr=True)

        for k in keys:
            if (self.nb_macro_modes==3 and k=="bull") or k!="bull":
                log(k,pr=True)
                self.interpret_ent(self.best_all[mode_to_int[k],:])

        log("ex",pr=True)
        for k in keys:
            if (self.nb_macro_modes==3 and k=="bull") or k!="bull":
                log(k,pr=True)
                self.interpret_ex(self.best_all[mode_to_int[k],:])
        self.test(verbose=2,**kwargs)
        
    def calculate_pf(self):
        print("calculate_pf not defined at OptMain, see child")
        pass
    
    #compare the performance of learn and test, try to avoid overfitting
    def test(self,**kwargs):
        dic=kwargs.get("dic","learn")
        dic_test=kwargs.get("dic_test","test")
        verbose=kwargs.get("verbose",1)
        if verbose>0:
            log("Starting tests " + dic)
        self.tested_arrs=[]
        ret_arr={}
        stats={}
        ret_pf_arr={}
        
        #recalculate the returns
        for d in [dic, dic_test]:
            ret_arr[d]={}
            self.defi_i(d)
            self.defi_ent(d)
            self.defi_ex(d)
            self.macro_mode(d)

            for ind in self.indexes: #CAC, DAX, NASDAQ
                stats[ind]={}
                pf=vbt.Portfolio.from_signals(self.close_dic[ind][d],  #use data for tsl or sl!!!!
                                              self.ents[ind],
                                              self.exs[ind],
                                              short_entries=self.ents_short[ind],
                                              short_exits=self.exs_short[ind],
                                              freq="1d",fees=self.fees,
                                              tsl_stop=self.tsl,
                                              sl_stop=self.sl,
                                              ) #stop_exit_price="close"
                self.tested_arrs=[]       

                ret_arr[d][ind]= self.get_ret(pf)
        _, ret_pf_arr[d]=self.calculate_pf([],self.init_threshold,self.init_threshold,dic=d)
        if verbose>0:
            log("Overall perf, "+d+": " + str(ret_pf_arr[d]),pr=True)
        return self.compare_learn_test(ret_arr,**kwargs)
        
    def compare_learn_test(self,ret_arr,**kwargs):
        #compare test and learn
        verbose=kwargs.get("verbose",1)
        for k in ret_arr:
            if "test" in k:
                test_key=k
            else:
                learn_key=k

        total_len=0
        confidence=0
        
        for ind in self.indexes:
            total_len+=len(ret_arr[test_key][ind])
            for ii in range(len(ret_arr[test_key][ind])):
                delta=ret_arr[test_key][ind][ii]-ret_arr[learn_key][ind][ii]
                t=str(self.close_dic[ind][test_key].columns[ii]) + " delta: "+str(delta)
                if delta>0 or ret_arr[test_key][ind][ii]>0: #test better than learning set or at least better than the benchmark
                    if verbose>1:
                        log(t+" OK",pr=True)
                    confidence+=1
                else:
                    if verbose>1:
                        log(t+" failed, learning ratio: " +  str(ret_arr[learn_key][ind][ii]) +\
                          " test ratio: " +  str(ret_arr[test_key][ind][ii]),pr=True) 
        
        if total_len!=0:
            confidence_ratio=100*round(confidence/total_len,2)
            if verbose>0:
                log("confidence_ratio: "+str(confidence_ratio) + "%",pr=True)    
        return confidence_ratio
    
            #stats[ind]["mean"]=np.mean(ret_arr[ind])
            #stats[ind]["min"]=np.min(ret_arr[ind])
            #stats[ind]["argmin"]=np.argmin(ret_arr[ind])
            #stats[ind]["max"]=np.max(ret_arr[ind])
            #stats[ind]["argmax"]=np.argmax(ret_arr[ind])
            #stats[ind]["std"]=np.std(ret_arr[ind])
        
        #df=pd.DataFrame(stats)
        #for k in ["mean","min","max","std"]:
            #df.loc[k,"all"]=np.mean(df.loc[k,:])
            
        #log(df)
        
    def filter_symbols(self,**kwargs):
        ###filter symbols
        symbols_to_keep = kwargs.get("symbols_to_keep")
        self.symbols={}
        
        for ind in self.indexes:
            self.symbols[ind]=[]
            
            if symbols_to_keep is not None:
                for s in symbols_to_keep:
                    if s in self.close_dic[ind]["total"].columns:
                        self.symbols[ind].append(s)
            else:
               self.symbols[ind]=self.close_dic[ind]["total"].columns 
        log(symbols_to_keep)
                  
    def split_in_part(self,**kwargs):
        self.number_of_parts=kwargs.get("number_of_parts",10)
        target_l={}
        
        self.selected_symbols=kwargs.get("sorted_symbols")
        if kwargs.get("split"):
            split=kwargs.get("split")
            for ind in self.indexes:
                if split=="time":
                    self.total_len[ind]=len(self.close_dic[ind]["total"])
                else: #symbol
                    self.total_len[ind]=len(self.close_dic[ind]["total"].columns)
        else:
            split=self.split_learn_train
        
        origin_dic=kwargs.get("origin_dic","total")
        if origin_dic!="total":
            prefix=origin_dic+"_"
        else:
            prefix=""

        for ind in self.indexes:
            target_l[ind]=int(math.floor(self.total_len[ind]/self.number_of_parts)) 
            
            for ii in range(self.number_of_parts):
                for d in ["close","open","low","high"]:
                    o=getattr(self,d+"_dic")[ind][origin_dic]
                    if split=="time": 
                        if ii==(self.number_of_parts-1):
                            t=o.iloc[ii*target_l[ind]:-1]
                        else:
                            t=o.iloc[ii*target_l[ind]:(ii+1)*target_l[ind]]
                    else: #symbol
                        if ii==(self.number_of_parts-1):
                            if self.selected_symbols is not None:
                                t=o[self.selected_symbols[ind][ii*target_l[ind]:-1]]
                            else:
                                t=o.iloc[:,ii*target_l[ind]:-1]
                        else:
                            if self.selected_symbols is not None:
                                t=o[self.selected_symbols[ind][ii*target_l[ind]:(ii+1)*target_l[ind]]]
                            else:
                                t=o.iloc[:,ii*target_l[ind]:(ii+1)*target_l[ind]]
                    getattr(self,d+"_dic")[ind][prefix+"part_"+str(ii)]=t
                
                o=self.macro_trend[ind][origin_dic]
                if split=="time": 
                    if ii==(self.number_of_parts-1):
                        t=o.iloc[ii*target_l[ind]:-1]
                    else:
                        t=o.iloc[ii*target_l[ind]:(ii+1)*target_l[ind]]
                else:
                    if ii==(self.number_of_parts-1):
                        if self.selected_symbols is not None:
                            t=o[self.selected_symbols[ind][ii*target_l[ind]:-1]]
                        else:
                            t=o.iloc[:,ii*target_l[ind]:-1]
                    else:
                        if self.selected_symbols is not None:
                            t=o[self.selected_symbols[ind][ii*target_l[ind]:(ii+1)*target_l[ind]]]
                        else:
                            t=o.iloc[:,ii*target_l[ind]:(ii+1)*target_l[ind]]
                self.macro_trend[ind][prefix+"part_"+str(ii)]=t
        
    def test_by_part(self, **kwargs):
        self.split_learn_train="time"
        self.split_in_part()
        
        self.filter_symbols()
        #filter input for next loop
        ret_arr={}
        stats={}
        
        for ii in range(self.number_of_parts):
            self.tested_arrs=[]
            
            self.defi_i("part_"+str(ii))
            self.defi_ent("part_"+str(ii))
            self.defi_ex("part_"+str(ii))
            self.macro_mode("part_"+str(ii))
            
            for ind in self.indexes: #CAC, DAX, NASDAQ
                stats[(ii, ind)]={}
                pf=vbt.Portfolio.from_signals(self.close_dic[ind]["part_"+str(ii)],  #use data for tsl or sl!!!!
                                              self.ents[ind],
                                              self.exs[ind],
                                              short_entries=self.ents_short[ind],
                                              short_exits=self.exs_short[ind],
                                              freq="1d",fees=self.fees,
                                              tsl_stop=self.tsl,
                                              sl_stop=self.sl,
                                              ) #stop_exit_price="close"

                ret_arr[ind]= self.get_ret(pf)
                stats[(ii, ind)]["mean"]=np.mean(ret_arr[ind])
                stats[(ii, ind)]["min"]=np.min(ret_arr[ind])
                stats[(ii, ind)]["argmin"]=np.argmin(ret_arr[ind])
                stats[(ii, ind)]["max"]=np.max(ret_arr[ind])
                stats[(ii, ind)]["argmax"]=np.argmax(ret_arr[ind])
                stats[(ii, ind)]["std"]=np.std(ret_arr[ind])

        df=pd.DataFrame(stats)
        
        df.loc["min",("all","all")] =np.min(df.loc["min",:])
        df.loc["max",("all","all")] =np.max(df.loc["max",:])
        df.loc["min_mean",("all","all")] =np.min(df.loc["mean",:])
        df.loc["max_mean",("all","all")] =np.max(df.loc["mean",:])
        df.loc["std_mean",("all","all")] =np.std(df.loc["mean",:])
        
        for k in ["mean","std"]:
            df.loc[k,("all","all")]=np.mean(df.loc[k,:])
        
        for ii in range(self.number_of_parts):
            for k in ["mean","std"]:
                df.loc[k,(ii,"all")]=np.mean(df.loc[k,(ii,slice(None))])
            df.loc["min",(ii,"all")]=np.min(df.loc["min",(ii,slice(None))]) 
            df.loc["max",(ii,"all")]=np.min(df.loc["max",(ii,slice(None))])     
        
        pd.set_option('display.max_columns', None)     
        log(df)
            
    def get_ret(self,pf):
        if self.index:
            rb=pf.total_market_return
            rr=pf.get_total_return()           
        else:
            rb=pf.total_market_return.values
            rr=pf.get_total_return().values
            
        arr=[]
        for ii in range(len(rb)):
            if abs(rb[ii])<0.1: #avoid division by zero
                p=(rr[ii])/ 0.1*np.sign(rb[ii])   
            else:
                p=(rr[ii]- rb[ii] )/ abs(rb[ii])
            arr.append(p)
        return arr            
            
        