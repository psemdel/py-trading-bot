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
    def calculate_eq_ret(self,pf):
        if self.index:
            rb=pf.total_market_return
            rr=pf.get_total_return()           
        else:
            rb=pf.total_market_return.values
            rr=pf.get_total_return().values
            
        delta=rr-rb
        #check that there is no extrem value that bias the whole result
        #if it the case, this value is not considered in the calculation of the score
        while np.std(delta)>10:
            ii=np.argmax(delta)
            delta=np.delete(delta,ii,0)
            rb=np.delete(rb,ii,0)
            rr=np.delete(rr,ii,0)
        
        m_rb=np.mean(rb)
        m_rr=np.mean(rr)
        

        if abs(m_rb)<0.1: #avoid division by zero
            p=(m_rr)/ 0.1*np.sign(m_rb)   
        else:
            p=(m_rr- m_rb )/ abs(m_rb)
      
        return 4*p*(p<0) + p*(p>0) #wrong direction for the return are penalyzed
  
    def manual_calculate_pf(self,ind,*args): #the order is bull/bear/uncertain
        self.calc_arrs=[]
        for arr in args:
            self.calc_arrs.append(arr)
        
        self.defi_ent()
        self.defi_ex()
        self.macro_mode()
        pf=vbt.Portfolio.from_signals(self.close_dic[ind], self.ents[ind],self.exs[ind],
                                      short_entries=self.ents_short[ind],
                                      short_exits=self.exs_short[ind],
                                      freq="1d",fees=self.fees)

        print("equivalent return " + str(self.calculate_eq_ret(pf)))
        return pf #for display for instance

    def calculate_pf(self, best_arrs_cand, best_ret_cand, best_arrs_ret):
        if not self.check_tested_arrs():
            return best_arrs_cand, best_ret_cand
        self.defi_ent()
        self.defi_ex()
        self.macro_mode()
        
        if self.index:
            ret_arr=[]
        else:
            ret=0

        for ind in self.indexes: #CAC, DAX, NASDAQ
            pf=vbt.Portfolio.from_signals(self.close_dic[ind], self.ents[ind],self.exs[ind],
                                          short_entries=self.ents_short[ind],
                                          short_exits=self.exs_short[ind],
                                          freq="1d",fees=self.fees,sl_stop=self.sl,
                                          ) #stop_exit_price="close"
            
            if self.index:
                ret_arr.append(self.calculate_eq_ret(pf))
            else:
                ret+=self.calculate_eq_ret(pf)

        if self.index:
            while np.std(ret_arr)>10:
                 ii=np.argmax(ret_arr)
                 ret_arr=np.delete(ret_arr,ii,0)
         
            ret=np.mean(ret_arr)

        trades =len(pf.get_trades().records_arr)
        del pf
         
        if ret> best_arrs_ret and ret>best_ret_cand and trades>50:
            return self.calc_arrs, ret
        
        return best_arrs_cand, best_ret_cand


        
    

     