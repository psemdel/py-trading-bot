#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 22:19:50 2023

@author: maxime
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from opt.opt_main import OptMain
from opt.opt_corr import Opt as OptCorr

class Opt(OptCorr):
    def __init__(
            self,
            period:str,
            indexes:list,
            symbols:list,
            filename:str="symbols",
            **kwargs): #all symbols should be from same index
        '''
        Gather the symbols together depending on their correlation and optimize the strategy for the formed clusters
        #The clusters are within one single index, as correlation calculation needs aligned data index.
        
        Arguments
        ----------
           period: period of time in year for which we shall retrieve the data
           indexes: main indexes used to download local data
           symbols: list of YF tickers to be selected
        '''
        OptMain.__init__(self,period,split_learn_train="time",indexes=[indexes],filename=filename,**kwargs)
        #calculate the correlation for each ind
        self.number_of_parts=0
        corr_arrs={
            indexes: [symbols]
        }
        self.split_in_part(corr_arrs,indexes)
        self.number_of_parts=1

