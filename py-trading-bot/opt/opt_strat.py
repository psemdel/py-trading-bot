import vectorbtpro as vbt
from vectorbtpro.utils.config import Config
import numpy as np
from opt.opt_main import OptMain
"""
Script to optimize the combination of patterns/signals used for a given strategy

The optimization takes place on the actions from CAC40, DAX and Nasdaq
Parameters very good on some actions but very bad for others should not be selected

The optimization algorithm calculates one point, look for the points around it and select the best one
As it can obviously lead to local maximum, the starting point is selected in a random manner
"""
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

class Opt(OptMain):
    '''
    Class to optimize strategy
    '''

    def manual_calculate_pf(self,ind,dic,*args): #the order is bull/bear/uncertain
        '''
        To calculate a portfolio from strategy arrays in jupyter for instance
        
        Arguments
        ----------
           ind: index, for instance "CAC40"
           dic: total/learn/test
        '''  
        self.calc_arrs=[]
        for arr in args:
            self.calc_arrs.append(arr)
        
        self.defi_ent(dic)
        self.defi_ex(dic)
        self.macro_mode(dic)
        pf=vbt.Portfolio.from_signals(self.data_dic[ind]["learn"], 
                                      self.ents[ind]["learn"],
                                      self.exs[ind]["learn"],
                                      short_entries=self.ents_short[ind]["learn"],
                                      short_exits=self.exs_short[ind]["learn"],
                                      tsl_stop=self.tsl,
                                      sl_stop=self.sl,
                                      freq="1d",fees=self.fees)

        print("equivalent return " + str(self.calculate_eq_ret(pf)))
        return pf #for display for instance

    def calculate_pf(
            self,
            best_arrs_cand,
            best_ret_cand,
            best_arrs_ret,
            dic: str="learn"):
        '''
        To calculate a portfolio from strategy arrays
        
        Arguments
        ----------
           best_arrs_cand: table containing the best candidate by the strategy array presently tested
           best_ret_cand: table containing the return of the best candidate by the strategy array presently tested
           best_arrs_ret: table containing the return of the best candidate by the strategy array of the whole loop
        '''
        try:
            if (not self.check_tested_arrs()) and not "test" in dic:
                return best_arrs_cand, best_ret_cand
            
            if self.it_is_index:
                ret_arr=[]
            else:
                ret=0
            
            pf_dic=self.calculate_pf_sub(dic)

            for ind in self.indexes: #CAC, DAX, NASDAQ

                if self.it_is_index:
                    ret_arr.append(self.calculate_eq_ret(pf_dic[ind]))
                else:
                    ret+=self.calculate_eq_ret(pf_dic[ind])
    
            if self.it_is_index:
                while np.std(ret_arr)>10:
                     ii=np.argmax(ret_arr)
                     ret_arr=np.delete(ret_arr,ii,0)
             
                ret=np.mean(ret_arr)
    
            trades =len(pf_dic[ind].get_trades().records_arr)
            del pf_dic
             
            if (ret> best_arrs_ret and ret>best_ret_cand and trades>50) or dic=="test":
                return self.calc_arrs, ret
            
            return best_arrs_cand, best_ret_cand
        except Exception as msg:
            import sys
            _, _, exc_tb = sys.exc_info()
            print("line " + str(exc_tb.tb_lineno))
            print(msg)
            

     