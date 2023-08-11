#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from opt.opt_strat import Opt as OptStrat
import numpy as np
import vectorbtpro as vbt

import pandas as pd
import scipy.cluster.hierarchy as sch

class Opt(OptStrat):
    def __init__(
            self,
            period,
            indexes,
            **kwargs):
        '''
        Gather the symbols together depending on their correlation and optimize the strategy for the formed clusters
        The clusters are within one single index, as correlation calculation needs aligned data index.

        Arguments
        ----------
           period: period of time in year for which we shall retrieve the data
           indexes: main indexes used to download local data
        '''
        super().__init__(period,split_learn_train="time",indexes=[indexes],**kwargs)
        #calculate the correlation for each ind
        self.number_of_parts=0
        corr_arrs={}
        for ind in self.indexes: #CAC, DAX, NASDAQ
            _, corr_arrs[ind]=cluster_corr(self.close_dic[ind]["learn"].corr())
            self.split_in_part(corr_arrs,ind)
            self.number_of_parts+=len(corr_arrs[ind])

    def outer_perf(self):
        '''
        Method to perform the optimization, within it, perf is called several times
        '''
        for ii in range(self.number_of_parts):
            self.log("Outer loop: "+str(ii),pr=True)

            for ind in self.indexes:
                self.log("symbols optimized: " + str(self.close_dic[ind]["learn_part_"+str(ii)].columns))

            self.defi_i("learn_part_"+str(ii))
            self.init_best_arr() #reinit
            self.perf(dic="learn_part_"+str(ii),dic_test="test_part_"+str(ii))

    def split_in_part(self,corr_arrs: list, ind: str):
        '''
        Split the set in several parts
        
        Arguments
        ----------
           corr_arrs: array where the symbols are gathered together depending on their correlation
           ind: index
        '''
        for ii, arr in enumerate(corr_arrs[ind]):
            for d in ["close","open","low","high"]:
                for dic in ["learn","test"]:
                    prefix=dic+"_"
                    getattr(self,d+"_dic")[ind][prefix+"part_"+str(self.number_of_parts+ii)]=getattr(self,d+"_dic")[ind][dic][arr]
                    self.macro_trend[ind][prefix+"part_"+str(self.number_of_parts+ii)]=self.macro_trend[ind][dic][arr]

def cluster_corr(corr_array, inplace=False):
    """
    Rearranges the correlation matrix, corr_array, so that groups of highly 
    correlated variables are next to eachother 

    Parameters
    ----------
    corr_array : pandas.DataFrame or numpy.ndarray
        a NxN correlation matrix 
        
    Returns
    -------
    pandas.DataFrame or numpy.ndarray
        a NxN correlation matrix with the columns and rows rearranged
    """
    pairwise_distances = sch.distance.pdist(corr_array)
    linkage = sch.linkage(pairwise_distances, method='complete')
    cluster_distance_threshold = pairwise_distances.max()/3 #the 3 can be variated to have more or less groups
    idx_to_cluster_array = sch.fcluster(linkage, cluster_distance_threshold, 
                                        criterion='distance')
    
    arr=[[] for ii in range(max(idx_to_cluster_array))]
    for ii, e in enumerate(idx_to_cluster_array):
        arr[e-1].append(corr_array.columns[ii])

    idx = np.argsort(idx_to_cluster_array)
    
    if not inplace:
        corr_array = corr_array.copy()
    
    if isinstance(corr_array, pd.DataFrame):
        return corr_array.iloc[idx, :].T.iloc[idx, :], arr
    return corr_array[idx, :][:, idx], arr




        
        
        

