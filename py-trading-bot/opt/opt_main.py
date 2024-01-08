import numbers
from core import indicators as ic
from core.macro import VBTMACROTREND, VBTMACROMODE, VBTMACROFILTER

from core.data_manager import retrieve_data_offline 
import vectorbtpro as vbt
from vectorbtpro.utils.config import Config
import numpy as np
import gc
import copy
from core.constants import BEAR_PATTERNS, BULL_PATTERNS, COL_DIC, bull_bear_to_int
from core.common import remove_multi
import pandas as pd
import math

import os

'''
Script to optimize the combination of patterns/signals used for a given strategy

The optimization takes place on the actions from CAC40, DAX and Nasdaq
Parameters very good on some actions but very bad for others should not be selected

The optimization algorithm calculates one point, look for the points around it and select the best one
As it can obviously lead to local maximum, the starting point is selected in a random manner
'''
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

class OptMain():
    def __init__(
            self,
            period: str,
            ratio_learn_train: int=80,
            split_learn_train: str="time",
            indexes: list=["CAC40", "DAX", "NASDAQ","IT"],
            it_is_index: bool=False,
            nb_macro_modes:int=3,
            loops:int=3,
            fees: numbers.Number=0.0005,
            dir_bull: str="long",
            dir_bear: str="long",
            dir_uncertain: str="long",
            test_window_start_init: int=None,
            sl: numbers.Number=None,
            tsl: numbers.Number=None,
            strat_arr: dict=None,
            filename: str="main",
            testing: bool=False,
            opt_only_exit: bool=False,
            proba_one: float=0.05,
            minimum_trades: int=50
            ):
        '''
        Optimisation main class
        
        Note: the split train/test can also be performed with @vbt.cv_split()

        Arguments
        ----------
           period: period of time in year for which we shall retrieve the data
           ratio_learn_train: which proportion of the total set should be reserved for learning and testing
           split_learn_train: if time, the learning and testing set will be splited according to time. So 2007-2008: learning, 2009: testing
                              if symbols, the learning and testing set will be splited according to symbols. So ["AAPL","AMZN"]: learning, ["MSFT"]: testing
           indexes: main indexes used to download local data
           it_is_index: if True, it will select only the index to make the optimization
           nb_macro_modes: if set to 1, no trend is considered, normally 3 (bull/bear/uncertain)
           loops: maximum number of loops to be performed (to limit the total computing time before having a result)
           fees: fees in pu
           dir_bull: direction to use during bull trend
           dir_bear: direction to use during bear trend
           dir_uncertain: direction to use during uncertain trend   
           test_window_start_init: index where the test window should start, random otherwise
           sl: stop loss threshold
           tsl: daily stop loss threshold
           strat_arr: array of the strategy combination to use, if defined then the loop will start from this arr
           testing: set to True to perform unittest on the function
           filename: name of the file where to solve the result
           opt_only_exit: optimize only the exits as the entries are fixed by another mechanism
           proba_one: in the random array probability of having a 1 (other values are 0) in pu
           minimum_trades: minimum number of trades for a strategy to be eligible. "Hold" strategies are not of interest
        '''
        for k in ["ratio_learn_train","split_learn_train", "indexes", "it_is_index","nb_macro_modes",
                  "strat_arr","fees", "sl", "tsl", "filename","testing","opt_only_exit","proba_one",
                  "minimum_trades"]:
            setattr(self,k,locals()[k])
        #init
        for key in ["close","open","low","high","data","volume"]:
            setattr(self,key+"_dic",{})
            
            for ind in self.indexes:
                getattr(self,key+"_dic")[ind]={}

        ind_str=""
        for ind in self.indexes:
            ind_str+=ind+"_"

        text_it_is_index= "index_" if it_is_index else ""

        self.test_arrs_path=os.path.join(os.path.dirname(__file__), "tested_arrs/"+ind_str+ period+"_"+ 
                                         text_it_is_index+ self.filename+".csv")
        try:
            self.test_arrs=pd.read_csv(self.test_arrs_path,index_col=0)
        except:
            self.test_arrs=None

        self.row={}
        self.total_len={}
        self.test_window_start={}
        
        for ind in self.indexes:
            retrieve_data_offline(self,ind,period)
            self.suffix="_ind" if self.it_is_index else ""
            
            if self.split_learn_train=="time":
                self.total_len[ind]=len(getattr(self,"close"+self.suffix))
            else: #symbol
                self.total_len[ind]=len(getattr(self,"close"+self.suffix).columns)
            learn_len=int(math.floor(self.ratio_learn_train/100*self.total_len[ind]))
            
            test_len=self.total_len[ind]-learn_len
            
            if test_window_start_init is None:
                self.test_window_start[ind]=np.random.randint(0,learn_len)
            else:
                self.test_window_start[ind]=test_window_start_init
            self.test_window_end=self.test_window_start[ind]+test_len
            
            self.log("random test start at index number " + ind + " for : "+str(self.test_window_start[ind]) +
                ", "+str(self.close.index[self.test_window_start[ind]]) +", "+\
                "until index number: "+str(self.test_window_end) + ", "+str(self.close.index[self.test_window_end])
                )
            
            self.data_dic[ind]["total"]=getattr(self,"data"+self.suffix)
            learn_range=[i for i in range(0,self.test_window_start[ind])]+[i for i in range(self.test_window_end,self.total_len[ind])]
            
            if self.split_learn_train=="time": 
                self.data_dic[ind]["test"]=getattr(self,"data"+self.suffix).iloc[self.test_window_start[ind]:self.test_window_end]
                self.data_dic[ind]["learn"]=getattr(self,"data"+self.suffix).iloc[learn_range]
            else: #symbol
                self.data_dic[ind]["test"]=getattr(self,"data"+self.suffix).select(list(self.close.columns[self.test_window_start[ind]:self.test_window_end]))
                self.data_dic[ind]["learn"]=getattr(self,"data"+self.suffix).select(list(self.close.columns[learn_range]))
                
            for d in ["Close","Open","Low","High","Volume"]:
                for k in ["test","learn","total"]:
                    getattr(self,d.lower()+"_dic")[ind][k]=self.data_dic[ind][k].get(d)
        self.out={}
        
        #init
        self.init_threshold=-1000 
        self.confidence_threshold=60
        
        if self.strat_arr is not None:
            self.predef=True
            self.deinterpret_all()
            self.loops=1
            self.nb_macro_modes=len(self.strat_arr)
        else:
            self.predef=False
            self.loops=loops
            self.calc_arr=None
            if self.nb_macro_modes==3:
                self.arr={"bull":{"ent":[],"ex":[]},"bear":{"ent":[],"ex":[]},"uncertain":{"ent":[],"ex":[]}}
            else:
                self.arr={"simple":{"ent":[],"ex":[]}}
        self.calc_arr=copy.deepcopy(self.arr)
        #append used only once
        self.all_t={}
        self.macro_trend={}
        for ind in self.indexes:
            self.all_t[ind]={}
            self.macro_trend[ind]={}

        self.macro_trend_mode={}
        if self.nb_macro_modes==3:
            for key in self.arr:
                self.macro_trend_mode[key]=locals()['dir_'+key]

        #all entries and exits for all patterns and signals are calculated once and for all here
        self.threshold=1
        self.defi_i("learn")
        self.defi_macro_trend("learn")
        
        self.shift=False

        print("init finished")
       
    def log(
            self,
            text: str,
            pr: bool=False
            ):
        '''
        Write a log file

        Arguments
        ----------
           text: text to be added to the log file
           pr: print it in the console
        '''
        if not "filename" in self.__dir__():
            self.filename="strat"

        with open(os.path.join(os.path.dirname(__file__), "output/"+ self.filename+".txt"), "a") as f:
            f.write("\n"+str(text))  
            
        if pr:
            print(text)

    def defi_i_total(self):
        '''
        Calculate the entries and exits for each strategy. Relatively slow, but must be performed only once.
        
        An array instead of a dictionary is used as it makes the variation algorithm easier. It just has to replace 0 with 1 and the other way around.
        
        Be careful that this function is consistent with entry_cols in constant.py

        Arguments
        ----------
           key: total/learn/test
        '''
        for ind in self.indexes: #CAC, DAX, NASDAQ
            all_t={'ent':[], 'ex':[]}
            #to be calculated with total otherwise the result test+learn is different from the total. 
            #Some functions returns NaN for the first indexes for instance            
            open_=self.open_dic[ind]["total"]
            high=self.high_dic[ind]["total"]
            low=self.low_dic[ind]["total"]
            close=self.close_dic[ind]["total"]
            volume=self.volume_dic[ind]["total"]
            
            t=ic.VBTSTOCHKAMA.run(high,low,close)
            all_t['ent'].append(t.entries_kama)
            all_t['ex'].append(t.exits_kama)
            
            t=vbt.talib("MFI").run(high, low, close,volume)
            all_t['ent'].append(t.real_crossed_below(20))
            all_t['ex'].append(t.real_crossed_above(80))
            #all_t['ent'].append(t.real_crossed_above(20))
            #all_t['ex'].append(t.real_crossed_below(80))
            
            t=vbt.STOCH.run(high,low,close)
            all_t['ent'].append(t.slow_k_crossed_below(20))
            all_t['ex'].append(t.slow_k_crossed_above(80))
            #all_t['ent'].append(t.slow_k_crossed_above(20))
            #all_t['ex'].append(t.slow_k_crossed_below(80))
  
            t=vbt.talib("WILLR").run(high, low, close)
            all_t['ent'].append(t.real_crossed_below(-90))
            all_t['ex'].append(t.real_crossed_above(-10))
            #all_t['ent'].append(t.real_crossed_above(-90))
            #all_t['ex'].append(t.real_crossed_below(-10))
            
            t=ic.VBTSUPERTREND.run(high,low,close)
            all_t['ent'].append(t.entries)
            all_t['ex'].append(t.exits)
                            
            t=vbt.BBANDS.run(close)
            all_t['ent'].append(t.lower_above(close))
            all_t['ex'].append(t.upper_below(close))

            t=vbt.RSI.run(close,wtype='simple')
            all_t['ent'].append(t.rsi_crossed_below(20))
            all_t['ex'].append(t.rsi_crossed_above(80))
            #all_t['ent'].append(t.rsi_crossed_above(20))
            #all_t['ex'].append(t.rsi_crossed_below(80))
            
            all_t['ent'].append(t.rsi_crossed_below(30))
            all_t['ex'].append(t.rsi_crossed_above(70))
            #all_t['ent'].append(t.rsi_crossed_above(30))
            #all_t['ex'].append(t.rsi_crossed_below(70))
            
            t=vbt.talib("ULTOSC").run(high, low, close)
            all_t['ent'].append(t.real_crossed_below(20))
            all_t['ex'].append(t.real_crossed_above(80))
            #all_t['ent'].append(t.real_crossed_above(20))
            #all_t['ex'].append(t.real_crossed_below(80))
            all_t['ent'].append(t.real_crossed_below(25))
            all_t['ex'].append(t.real_crossed_above(75))
            #all_t['ent'].append(t.real_crossed_above(25))
            #all_t['ex'].append(t.real_crossed_below(75))

            for func_name in BULL_PATTERNS:
                t=ic.VBTPATTERNONE.run(open_,high,low,close,func_name, "ent").out
                all_t['ent'].append(t)
                
            for func_name in BEAR_PATTERNS:
                t=ic.VBTPATTERNONE.run(open_,high,low,close,func_name, "ex").out
                all_t['ex'].append(t)  

            self.all_t[ind]["total"]={}
            self.all_t[ind]["total"]['ent']=all_t['ent']
            self.all_t[ind]["total"]['ex']=all_t['ex']
            
        del t
        gc.collect() 

    def defi_i(self,key: str):
        '''
        See defi_i_total
        '''
        if "total" not in self.all_t[self.indexes[0]]:
            self.defi_i_total()

        if key not in self.all_t[self.indexes[0]]:
            for ind in self.indexes:
                i=self.open_dic[ind][key].index
                c=self.open_dic[ind][key].columns
                
                self.all_t[ind][key]={"ent":[],"ex":[]}

                for ent_or_ex in ["ent","ex"]:
                    for df in self.all_t[ind]["total"][ent_or_ex]:
                        df2=remove_multi(df)
                        self.all_t[ind][key][ent_or_ex].append(df2.loc[i,c])

    def defi_macro_trend_total(self):
        for ind in self.indexes:
            self.macro_trend[ind]["total"]=VBTMACROTREND.run(self.close_dic[ind]["total"]).macro_trend
     
    def defi_macro_trend(self, key:str):
        if "total" not in self.macro_trend[self.indexes[0]]:
            self.defi_macro_trend_total()
        
        if key not in self.macro_trend[self.indexes[0]]:
            for ind in self.indexes:
                i=self.open_dic[ind][key].index
                self.macro_trend[ind][key]=self.macro_trend[ind]["total"].loc[i]

    def deinterpret_all(self):
        '''
        human readable information in binary array
        '''
        self.arr={}

        for k, v in self.strat_arr.items():
            self.arr[k]={}
            for ent_or_ex, vv in v.items():
                if len(vv)>0 and type(vv[0])==int:
                    self.arr=self.strat_arr
                    return
                else:
                    self.arr[k][ent_or_ex] =self.deinterpret(vv,ent_or_ex)

    def deinterpret(self,arr_input_explicit: list,ent_or_ex: str):
        '''
        human readable information in binary array
        
        Arguments
        ----------
           arr_input_explicit: strategy array with names
           ent_or_ex: key which can be "ent" or "ex"
        '''
        l=[]
        if len(arr_input_explicit)==0:
            l=[0 for e in COL_DIC[ent_or_ex]]
        else:
            #warning
            for e in arr_input_explicit:
                if e not in COL_DIC[ent_or_ex]:
                    print("warning: "+e+" not found in col_dic")
            
            for e in COL_DIC[ent_or_ex]:
                if e in arr_input_explicit:
                    l.append(1)
                else:
                    l.append(0)
        return l       

    def interpret(self,arr_input: list,ent_or_ex: str):
        '''
        to translate the binary array in human readable information
        
        Arguments
        ----------
           arr_input: strategy array with figures to be displayed
        '''
        l=[]
        for ii, e in enumerate(arr_input[ent_or_ex]):
            if e:
                l.append(COL_DIC[ent_or_ex][ii])
        self.log(l)
        
    def defi_ent(self,key: str):
        '''
        See defi
        '''
        self.ents={}
        self.ents_short={}
        self.defi("ent",key)
    
    def defi_ex(self,key: str):
        '''
        See defi
        '''
        self.exs={}
        self.exs_short={}
        self.defi("ex",key)
        
    def defi(self,ent_or_ex:str,key:str):
        '''
        Put the patterns/signals together (OR)
        Note: this is the time consuming operation
        Arguments
        ----------
           key: total/learn/test
        '''  
        if key not in self.all_t[self.indexes[0]]:
            self.defi_i(key)
        if key not in self.macro_trend[self.indexes[0]]:     
            self.defi_macro_trend(key)

        for ind in self.indexes: #CAC, DAX, NASDAQ
            ent=None
            for k, v in self.calc_arr.items():
                arr=v[ent_or_ex]
                ents_raw=None 
               
                s=np.full(np.shape(self.all_t[ind][key][ent_or_ex][0]),0.0)
                
                for ii in range(len(arr)):
                    if arr[ii]==1:
                        s+=remove_multi(self.all_t[ind][key][ent_or_ex][ii])

                ents_raw=(s>=self.threshold)

                if self.nb_macro_modes==1:
                    ent=ents_raw
                else:
                    ents_raw=VBTMACROFILTER.run(ents_raw,self.macro_trend[ind][key],bull_bear_to_int[k]).out
                    
                    if ent is None:
                        ent=ents_raw
                    else:
                        ent=ic.VBTOR.run(ent, ents_raw).out
            
            if ent_or_ex=="ent":
                self.ents[ind]=ent
            else:
                if "learn" in key and self.test_window_start[ind]!=0 and self.split_learn_train=="time":
                    #exit all before the gap due to the exit
                    ent.iloc[self.test_window_start[ind]-1]=True 
                self.exs[ind]=ent
           
    def macro_mode(self,key:str):
        '''
        Adjust the entries and exits depending on the trend
        
        Arguments
        ----------
           key: total/learn/test
        '''  
        if (self.nb_macro_modes ==1 or
           self.macro_trend_mode["bull"]=='long' and self.macro_trend_mode["bear"]=='long' 
           and self.macro_trend_mode["uncertain"]=='long'):
            for ind in self.indexes: 
                self.ents_short[ind]=np.full(self.ents[ind].shape,False)
                self.exs_short[ind]=np.full(self.ents[ind].shape,False)
        else:
            self.ents_raw={}
            self.exs_raw={}
            
            for ind in self.indexes: #CAC, DAX, NASDAQ
                t=VBTMACROMODE.run(self.ents[ind],self.exs[ind], self.macro_trend[ind][key],\
                                   dir_bull=self.macro_trend_mode["bull"],
                                   dir_bear=self.macro_trend_mode["bear"],
                                   dir_uncertain=self.macro_trend_mode["uncertain"])
                self.ents[ind]=t.entries
                self.exs[ind]=t.exits
                self.ents_short[ind]=t.entries_short
                self.exs_short[ind]=t.exits_short 

    def arr_to_key(self):
        self.ind_k=""
        
        for k, v in self.calc_arr.items():
            for ent_or_ex in ["ent","ex"]:
                for e in v[ent_or_ex]:
                    self.ind_k+=str(int(e)) 

    def key_to_arr(self, ind_k):
        
        self.arr={}
        a=[int(e) for e in ind_k]
        if len(a)>(len(COL_DIC["ent"])+len(COL_DIC["ex"])):
            self.arr["bull"]={}
            self.arr["bear"]={}
            self.arr["uncertain"]={}

            self.arr["bull"]["ent"]=a[:len(COL_DIC["ent"])]
            self.arr["bull"]["ex"]=a[len(COL_DIC["ent"]):int(len(ind_k)*1/3)]
            self.arr["bear"]["ent"]=a[int(len(ind_k)*1/3):int(len(ind_k)*1/3)+len(COL_DIC["ent"])]
            self.arr["bear"]["ex"]=a[int(len(ind_k)*1/3)+len(COL_DIC["ent"]):int(len(ind_k)*2/3)]                             
            self.arr["uncertain"]["ent"]=a[int(len(ind_k)*2/3):int(len(ind_k)*2/3)+len(COL_DIC["ent"])]
            self.arr["uncertain"]["ex"]=a[int(len(ind_k)*2/3)+len(COL_DIC["ent"]):]
        else:
            self.arr["simple"]={}
            self.arr["simple"]["ent"]=a[:len(COL_DIC["ent"])]
            self.arr["simple"]["ex"]=a[len(COL_DIC["ent"]):]
            
    def key_to_arr_h(self, ind_k):
            '''
            to translate the binary array in human readable information
            
            Arguments
            ----------
               ind_k: index in test_arr. Combination of 0 and 1.
            '''
            self.key_to_arr(ind_k)
            arr_h={}
                        
            for k, v in self.arr.items():
                arr_h[k]={}
                for ent_or_ex, vv in v.items():
                    arr_h[k][ent_or_ex]=[]
                    for ii, e in enumerate(vv):
                        if e==1:
                            arr_h[k][ent_or_ex].append(COL_DIC[ent_or_ex][ii])
            return arr_h
            
    def check_tested_arrs(
            self,
            )-> bool:
        '''
        Check if the strategy array has already been calculated. It saves time.
        Return True, if not already there
        ''' 
        #merge all list, it makes the rest more simple
        self.get_cols()
        self.arr_to_key()

        if self.test_arrs is None:
            return True    
        return not self.ind_k in self.test_arrs.index
            
    def get_cols_sub(self,name):
        '''
        Define cols which is used for the columns of the Dataframe to be saved
        
        Arguments
        ----------
            name: name of the preprocessing function used
        '''
        for ent_or_ex in ["ent","ex"]:
            for ii, v in enumerate(self.calc_arr[name][ent_or_ex]):
                if ent_or_ex=="ent":
                    w="_entry_"
                else:
                    w="_exit_"
                col_name="a_"+name+w+COL_DIC[ent_or_ex][ii]
                self.row[col_name]=v
                self.cols.append(col_name)  

    def get_cols(self):
        self.cols=[]
        for k in self.calc_arr:
            self.get_cols_sub(k)
        
    def random(self, l:int)-> list:
        '''
        Generate a random strategy array
        ''' 
        #choose randomly 0 and 1. All zeros is not accepted. 90% chance 0, 10% chance 1
        s=0
        while s==0:
            arr=np.random.choice(2,l, p=[1-self.proba_one, self.proba_one]) 
            s=np.sum(arr)
        return arr
    
    def assign_random(self):
        b=True
        while b:
            if self.nb_macro_modes==1:
                self.calc_arr={"simple": {'ent':self.random(len(COL_DIC["ent"])),
                                          'ex':self.random(len(COL_DIC["ex"]))}}
            else:
                self.calc_arr={"bull": {'ent':self.random(len(COL_DIC["ent"])),
                                        'ex':self.random(len(COL_DIC["ex"]))},
                          "bear": {'ent':self.random(len(COL_DIC["ent"])),
                                   'ex':self.random(len(COL_DIC["ex"]))},
                          "uncertain": {'ent':self.random(len(COL_DIC["ent"])),
                                   'ex':self.random(len(COL_DIC["ex"]))},
                          }
            
            b=not self.check_tested_arrs() #random until new one is found
            
        self.arr=copy.deepcopy(self.calc_arr)

    def summarize_eq_ret(self,ret_arr:list)-> numbers.Number:
        '''
        Method to calculate a general score for a strategy from an array of returns
        
        Arguments
        ----------
           ret_arr: array of returns
        '''  
        while np.std(ret_arr)>10:
            ii=np.argmax(ret_arr)
            ret_arr=np.delete(ret_arr,ii,0)
            
        return np.mean(ret_arr)

    def variate(
            self, 
            dic:str="learn"
            ):
        '''
        Variates the array, if it is better, the new array is returned otherwise the original one
        
        Arguments
        ----------
           d: key word to access learn data
        ''' 
        if self.test_arrs is None:
            self.variate_first_ind=None
        else:
            self.variate_first_ind=self.test_arrs.index[-1]
        
        ent_or_exs=["ent"]
        if not self.opt_only_exit:
            ent_or_exs.append("ex")
        
        nb_calc=0
        for k, v in self.arr.items():
            for ent_or_ex in ["ent","ex"]:
                for ii in range(len(v[ent_or_ex])):
                    self.calc_arr=copy.deepcopy(self.arr)
                    if v[ent_or_ex][ii]==0:
                        self.calc_arr[k][ent_or_ex][ii]=1
                    else:
                        self.calc_arr[k][ent_or_ex][ii]=0

                    if np.sum(self.calc_arr[k][ent_or_ex] )!=0:
                        nb_calc+=self.calculate_pf(dic=dic)
        
        if nb_calc==0:
            self.progression=False
        else:
            if self.variate_first_ind is None:
                sub_df=self.test_arrs
            else:
                sub_df=self.test_arrs.loc[self.variate_first_ind:]

            if sub_df["opt_return"].max() > self.best_loop_ret and self.trades>self.minimum_trades:
                self.progression=True
                self.best_loop_ret=sub_df["opt_return"].max()
                self.log("Overall perf, "+dic+": " + str(round(self.best_loop_ret,3)),pr=True)
                self.key_to_arr(sub_df.index[ sub_df["opt_return"].argmax() ]) #set a new self.arr
                self.calc_arr=self.arr
            else:
                self.progression=False
             
    def perf(
            self,
            dic:str="learn",
            dic_test:str="test",
            **kwargs):
        '''
        Main fonction to optimize a strategy
        
        Arguments
        ----------
           d: key word to access learn data
           dic_test: key word to access test data
        '''
        for jj in range(self.loops):
            self.log("loop " + str(jj),pr=True)
            
            #new start point
            self.best_loop_ret=self.init_threshold
            
            if self.test_arrs is None:
                self.loop_first_ind=None
            else:
                self.loop_first_ind=self.test_arrs.index[-1]
            
            if not self.predef:  
                self.assign_random()
            
            self.calculate_pf(dic=dic) #reset 
            self.progression=True
            #start variations
            kk=0
            while self.progression and not (self.testing and kk>0): #for testing only one round
                print("next calc")
                self.variate(dic=dic)
                self.test(dic=dic,dic_test=dic_test,*kwargs)
                kk+=1
                
            self.save_test_arrs()

        if self.loop_first_ind is None:
            sub_df=self.test_arrs
        else:
            sub_df=self.test_arrs.loc[self.loop_first_ind:]

        self.best_all_ret=sub_df["opt_return"].max()
        self.key_to_arr(sub_df.index[ sub_df["opt_return"].argmax() ]) #set a new self.arr
        self.best_all=self.arr.copy()

        self.log("algorithm completed")
        self.log("best of all")
        self.log('arr'+str(self.best_all))
        self.log("return : " + str(round(self.best_all_ret,3)))

        for ent_or_ex in ["ent","ex"]:
            self.log(ent_or_ex)
            for k in self.best_all:
                self.log(k)
                self.interpret(self.best_all[k],"ent")
        self.test(verbose=2,**kwargs)
        
        #Not really useful anymore as everything can be read in the resulting dataframe
        #self.summary_total("test")
        #self.summary_total()
            
    def calculate_pf(self):
        print("calculate_pf not defined at OptMain, see child")
        pass
    
    def calculate_pf_sub(self,dic):
        pf_dic={}   
        self.defi_ent(dic)
        self.defi_ex(dic)
        self.macro_mode(dic)

        for ind in self.indexes: #CAC, DAX, NASDAQ
            pf_dic[ind]=vbt.Portfolio.from_signals(self.data_dic[ind][dic],
                                          self.ents[ind],
                                          self.exs[ind],
                                          short_entries=self.ents_short[ind],
                                          short_exits=self.exs_short[ind],
                                          freq="1d",fees=self.fees,
                                          tsl_stop=self.tsl,
                                          sl_stop=self.sl,
                                          ) #stop_exit_price="close"
        return pf_dic

    def test(
            self,
            dic:str="learn",
            dic_test:str="test",
            dic_total:str="total",
            verbose:int=1,
            ):
        '''
        Compare the performance of learn and test, try to avoid overfitting
        
        Arguments
        ----------
           dic: key word to access learn data
           dic_test: key word to access test data
           verbose: how much verbose is needed
        ''' 
        if verbose>0:
            self.log("Starting tests " + dic)
        ret_arr={}
        
        #recalculate the returns
        for d in [dic, dic_test, dic_total]:
            ret_arr[d]={}
            #self.defi_i(d)
            pf_dic=self.calculate_pf_sub(d)
            
            for ind in self.indexes: #CAC, DAX, NASDAQ
                ret_arr[d][ind]= self.get_ret(pf_dic[ind],ind,d)

            self.calculate_pf(dic=d,bypass_tested_arrs=True)

        return self.compare_learn_test(ret_arr,verbose=verbose)
                  
    def compare_learn_test(
            self,
            ret_arr: list,
            verbose:int=1):
        '''
        See test
        '''
        for k in ret_arr:
            if "test" in k:
                test_key=k
            else:
                learn_key=k

        total_len=0
        confidence=0
        
        for ind in self.indexes:
            total_len+=len(ret_arr[test_key][ind])
           
            for k in ret_arr[test_key][ind]:
                delta=ret_arr[test_key][ind][k]-ret_arr[learn_key][ind][k]

                t=str(k) + " delta: "+str(round(delta,3))
                if delta>0 or ret_arr[test_key][ind][k]>0: #test better than learning set or at least better than the benchmark
                    if verbose>1:
                        self.log(t+" OK",pr=True)
                    confidence+=1
                else:
                    if verbose>1:
                        self.log(t+" failed, learning ratio: " +  str(round(ret_arr[learn_key][ind][k],3)) +\
                          " test ratio: " +  str(round(ret_arr[test_key][ind][k],3)),pr=True) 
        
        if total_len!=0:
            confidence_ratio=100*round(confidence/total_len,2)
            self.row["confidence_ratio"]=confidence_ratio
            
            if verbose>0:
                self.log("confidence_ratio: "+str(round(confidence_ratio,2)) + "%",pr=True)    
        return confidence_ratio
    
    def summary_total(self, dic:str="total"):
        '''
        Display some summary of the results
        '''
        pf_dic=self.calculate_pf_sub(dic)

        for ind in self.indexes:
            if type(pf_dic[ind].total_market_return)!=pd.core.series.Series:
                self.log("Data set " + dic +", Index: "+ ind +", return: "+ str(round(np.mean(pf_dic[ind].get_total_return()),3))+
                    ", benchmark return: "+ str(round(np.mean(pf_dic[ind].total_market_return),3)) )                
            else:
                self.log("Data set " + dic +", Index: "+ ind +", return: "+ str(round(np.mean(pf_dic[ind].get_total_return()),3))+
                    ", benchmark return: "+ str(round(np.mean(pf_dic[ind].total_market_return.values),3)) )

    def filter_symbols(
            self,
            symbols_to_keep: list=None,
            ):
        '''
        Allow selection of only some symbols
        
        Arguments
        ----------
           symbols_to_keep: list of YF tickers to keep
        '''     
        self.symbols={}
        
        for ind in self.indexes:
            self.symbols[ind]=[]
            
            if symbols_to_keep is not None:
                for s in symbols_to_keep:
                    if s in self.close_dic[ind]["total"].columns:
                        self.symbols[ind].append(s)
            else:
               self.symbols[ind]=self.close_dic[ind]["total"].columns 
        self.log(symbols_to_keep)
         
    def split_in_part(
            self,
            sorted_symbols:dict,
            number_of_parts:int=10,
            split:str=None,
            ):
        '''
        Split a learning set in equal part         
        
        Arguments
        ----------
           sorted_symbols: YF tickers sorted in a certain ways with the indexes as key
           number_of_parts: Number of parts in which the total set must be divided
           origin_dic: which set must be divided
           split: if time, the learning and testing set will be splited according to time. So 2007-2008: learning, 2009: testing
                              if symbols, the learning and testing set will be splited according to symbols. So ["AAPL","AMZN"]: learning, ["MSFT"]: testing
           
        '''  
        self.number_of_parts=number_of_parts
        self.selected_symbols=sorted_symbols
        target_l={}

        if split is not None:
            for ind in self.indexes:
                if split=="time":
                    self.total_len[ind]=len(self.close_dic[ind]["total"])
                else: #symbol
                    self.total_len[ind]=len(self.close_dic[ind]["total"].columns)
        else:
            split=self.split_learn_train
        
        for origin_dic in ["total","learn","test"]:
            if origin_dic not in self.all_t[self.indexes[0]]:
                self.defi_i(origin_dic)
            if origin_dic not in self.macro_trend[self.indexes[0]]:     
                self.defi_macro_trend(origin_dic)
            
            if origin_dic!="total":
                prefix=origin_dic+"_"
            else:
                prefix=""
    
            for ind in self.indexes:
                target_l[ind]=int(math.floor(self.total_len[ind]/self.number_of_parts)) 
                for ii in range(self.number_of_parts):
                    self.data_dic[ind][prefix+"part_"+str(ii)]=self.split_in_part_sub(self.data_dic[ind][origin_dic],ii,split,target_l,ind)
                    
                for d in ["Close","Open","Low","High"]:
                    for ii in range(self.number_of_parts):
                        getattr(self,d.lower()+"_dic")[ind][prefix+"part_"+str(ii)]=self.data_dic[ind][prefix+"part_"+str(ii)].get(d)    
                
                for ii in range(self.number_of_parts):
                    self.macro_trend[ind][prefix+"part_"+str(ii)]=self.split_in_part_sub(self.macro_trend[ind][origin_dic],ii,split,target_l,ind)
        
    def split_in_part_sub(self,o,ii:int,split:str,target_l:dict,ind:str):
        '''
        Subfunction for split_in_part
        
        Arguments
        ----------
            o: object to split
            split: split by time or symbol?
            ii: number of this part
            target_l: expected length of the resulting parts
            ind: index    
        '''
        if split=="time": 
            if ii==(self.number_of_parts-1):
                t=o.iloc[ii*target_l[ind]:-1]
            else:
                t=o.iloc[ii*target_l[ind]:(ii+1)*target_l[ind]]
        else: #symbol
            if ii==(self.number_of_parts-1):
                if self.selected_symbols is not None:
                    r=self.selected_symbols[ind][ii*target_l[ind]:-1]
                    if type(o)==pd.DataFrame:
                        t=o[r]
                    else: #data
                        t=o.select(r)
                else:
                    t=o.iloc[:,ii*target_l[ind]:-1]
            else:
                if self.selected_symbols is not None:
                    r=self.selected_symbols[ind][ii*target_l[ind]:(ii+1)*target_l[ind]]
                    if type(o)==pd.DataFrame:
                        t=o[r]
                    else: #data
                        t=o.select(r)
                else:
                    t=o.iloc[:,ii*target_l[ind]:(ii+1)*target_l[ind]]
        return t
        
    def test_by_part(self):
        '''
        Test a set previously divided by part       
        '''  
        self.split_learn_train="time"
        self.split_in_part(None)
        
        self.filter_symbols()
        #filter input for next loop
        ret_arr={}
        ret_dic={}
        stats={}
        
        for ii in range(self.number_of_parts):
            self.tested_arrs=[]
            dic="part_"+str(ii)
            #self.defi_i(dic)
            self.defi_ent(dic)
            self.defi_ex(dic)
            self.macro_mode(dic)
            
            for ind in self.indexes: #CAC, DAX, NASDAQ
                stats[(ii, ind)]={}
                pf=vbt.Portfolio.from_signals(self.data_dic[ind][dic],
                                              self.ents[ind],
                                              self.exs[ind],
                                              short_entries=self.ents_short[ind],
                                              short_exits=self.exs_short[ind],
                                              freq="1d",fees=self.fees,
                                              tsl_stop=self.tsl,
                                              sl_stop=self.sl,
                                              ) 

                ret_dic[ind]= self.get_ret(pf,ind,dic)
                ret_arr[ind]=[v for k, v in ret_dic[ind].items()] #we don't need the key
                
                stats[(ii, ind)]["mean"]=np.mean(ret_arr[ind])
                stats[(ii, ind)]["min"]=np.min(ret_arr[ind])
                stats[(ii, ind)]["argmin"]=np.argmin(ret_arr[ind])
                stats[(ii, ind)]["max"]=np.max(ret_arr[ind])
                stats[(ii, ind)]["argmax"]=np.argmax(ret_arr[ind])
                stats[(ii, ind)]["std"]=np.std(ret_arr[ind])
                
                self.row["surperf_factor_mean_"+ind+"_"+dic]=np.mean(ret_arr[ind])
                self.row["surperf_factor_min_"+ind+"_"+dic]=np.min(ret_arr[ind])
                self.row["surperf_factor_max_"+ind+"_"+dic]=np.max(ret_arr[ind])
                self.row["surperf_factor_std_"+ind+"_"+dic]=np.std(ret_arr[ind])

        df=pd.DataFrame(stats)
        
        df.loc["min",("all","all")] =np.min(df.loc["min",:])
        df.loc["max",("all","all")] =np.max(df.loc["max",:])
        df.loc["min_mean",("all","all")] =np.min(df.loc["mean",:])
        df.loc["max_mean",("all","all")] =np.max(df.loc["mean",:])
        df.loc["std_mean",("all","all")] =np.std(df.loc["mean",:])
        
        self.row["surperf_factor_min_all_indexes_total"]=df.loc["min",("all","all")]
        self.row["surperf_factor_max_all_indexes_total"]=df.loc["max",("all","all")]
        self.row["surperf_factor_min_mean_all_indexes_total"]=df.loc["min_mean",("all","all")]
        self.row["surperf_factor_max_mean_all_indexes_total"]=df.loc["max_mean",("all","all")]
        self.row["surperf_factor_std_mean_all_indexes_total"]=df.loc["std_mean",("all","all")]
        
        for k in ["mean","std"]:
            df.loc[k,("all","all")]=np.mean(df.loc[k,:])
            self.row["surperf_factor_"+k+"_all_indexes_"+dic]=df.loc[k,("all","all")]
        
        for ii in range(self.number_of_parts):
            for k in ["mean","std"]:
                df.loc[k,(ii,"all")]=np.mean(df.loc[k,(ii,slice(None))])
                self.row["surperf_factor_"+k+"_all_indexes_part"+str(ii)]=df.loc[k,(ii,"all")]

            df.loc["min",(ii,"all")]=np.min(df.loc["min",(ii,slice(None))]) 
            self.row["surperf_factor_min_all_indexes_part"+str(ii)]=df.loc["min",(ii,"all")]
            df.loc["max",(ii,"all")]=np.max(df.loc["max",(ii,slice(None))])     
            self.row["surperf_factor_max_all_indexes_part"+str(ii)]=df.loc["max",(ii,"all")]
        
        self.append_row()
        pd.set_option('display.max_columns', None)     
        self.log(df)
        
    def get_ret_sub(self,rb, rr):
        '''
        Should measure the surperformance
        rr-rb (close to alpha calculation) is not used as it would give too much weight to products or index with high rb (Nasdaq for instance compared to CAC40)
        the idea is to have p1>p2 is rr1>rr2
        
        Arguments
        ----------
            rb: benchmark return
            rr: portfolio’s realized return
        '''
        if abs(rb)<0.1: #avoid division by zero
            p=(rr)/ 0.1
        else:
            p=(rr- rb )/ abs(rb)
        return p
        
    def get_ret(self,pf,ind,dic)-> list:
        '''
        Calculate an equivalent score for each product in a portfolio  
        
        Arguments
        ----------
           pf: vbt portfolio
           ind: index
           dic: train, test or total
        '''   
        out={}
        if self.it_is_index or type(pf.total_market_return)!=pd.core.series.Series:
            rb=pf.total_market_return
            rr=pf.get_total_return()  
            out[ind]=self.get_ret_sub(rb,rr) #seems a bit silly to repeat ind twice as key in a row, but makes compare_learn_test simpler
            self.row["return_"+ind+"_"+dic]=rr
            self.row["surperf_factor_"+ind+"_"+dic]=out[ind]
        else:
            rb=pf.total_market_return.values
            rr=pf.get_total_return().values
            for ii, s in enumerate(pf.total_market_return.index):
                if type(s)==tuple:
                    s=s[-1]
                out[s]=self.get_ret_sub(rb[ii],rr[ii])
                self.row["return_"+s+"_"+dic]=rr[ii]
                self.row["surperf_factor_"+s+"_"+dic]=out[s]

        return out  

    def append_row(self):
        '''
        Append a row to test_arrs
        '''
        df_row=pd.DataFrame(self.row,index=[self.ind_k])
        
        if self.test_arrs is None:
            self.test_arrs=df_row
        else:
            if self.ind_k in self.test_arrs.index: #update
                #to avoid a perf warning, by looping on the keys
                common_cols=[]
                not_common_cols=[]
                for c in df_row.columns:
                    if c in self.test_arrs.columns:
                        common_cols.append(c)
                    else:
                        not_common_cols.append(c)
                self.test_arrs.loc[self.ind_k, common_cols]=df_row.loc[self.ind_k, common_cols]
                self.test_arrs.loc[self.ind_k, not_common_cols]=df_row.loc[self.ind_k, not_common_cols]
            else: #append
                self.test_arrs=pd.concat([self.test_arrs.loc[:],df_row])   

    def save_test_arrs(self):
        '''
        Save the test_arr to the disc
        '''
        self.test_arrs.to_csv(self.test_arrs_path)
    
    def calculate_eq_ret(self,pf,ind:str)-> numbers.Number:
        '''
        Calculate an equivalent score for a portfolio  
        
        Arguments
        ----------
           pf: vbt portfolio
           ind: index
        ''' 
        if self.it_is_index or type(pf.total_market_return)!=pd.core.series.Series:
            rb=pf.total_market_return
            rr=pf.get_total_return()           
        else:
            rb=pf.total_market_return.values
            rr=pf.get_total_return().values

        self.row["mean_return_"+ind+"_raw"]=np.mean(rr)
        delta=rr-rb
        self.row["mean_delta_"+ind+"_raw"]=np.mean(delta)

        #check that there is no extrem value that bias the whole result
        #if it the case, this value is not considered in the calculation of the score
        while np.std(delta)>10:
            ii=np.argmax(np.abs(delta))
            delta=np.delete(delta,ii,0)
            rb=np.delete(rb,ii,0)
            rr=np.delete(rr,ii,0)
        
        m_rb=np.mean(rb)
        m_rr=np.mean(rr)
        self.row["mean_return_"+ind+"_corrected"]=m_rr
        self.row["mean_delta_"+ind+"_corrected"]=np.mean(delta)
        
        if abs(m_rb)<0.1: #avoid division by zero
            p=(m_rr)/ 0.1*np.sign(m_rb)   
        else:
            p=(m_rr- m_rb )/ abs(m_rb)
        self.row["mean_surperf_factor_"+ind+"_corrected"]=p

        return 4*p*(p<0) + p*(p>0) #wrong direction for the return are penalyzed        