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

#Gather the symbols together depending on their correlation and optimize the strategy for the formed cluster
#The clusters are within one single index, as correlation calculation needs aligned data index.

class Opt(OptCorr):
    def __init__(self,period,indexes,symbols,**kwargs): #all symbols should be from same index
        OptMain.__init__(self,period,split_learn_train="time",indexes=[indexes],**kwargs)
        #calculate the correlation for each ind
        self.number_of_parts=0
        corr_arrs={
            indexes: [symbols]
        }
        self.split_in_part(corr_arrs,indexes,**kwargs)
        self.number_of_parts=1

