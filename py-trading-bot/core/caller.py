#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 23 11:53:33 2023

@author: maxime
"""
try:
    from ml import ml
    ml_loaded=True
except ImportError:
    ml_loaded=False

from core import strat, strat_legacy, presel
import sys

def name_to_ust_or_presel(
        ust_or_presel_name: str, 
        ml_model_name: str,
        period: str,
        it_is_index:bool=False,
        st=None,
        **kwargs):
    '''
    Function to call class from strat or presel

    Arguments
    ----------
        ust_or_presel_name: Name of the underlying strategy or preselection strategy to be called
        ml_model_name: Name of the machine learning model to use
        period: period of time in year for which we shall retrieve the data
        it_is_index: is it indexes that are provided 
        st: strategy associated
    '''
    try:
        if ml_model_name is not None:
            if ml_loaded:
                pr=ml.PreselMLCustom(period,ml_model_name,**kwargs)
                pr.run()
                return pr
            else:
                raise ImportError("Ml cannot be loaded, check you installed Keras")
        else:
            if ust_or_presel_name[:6]=="Presel":
                if not it_is_index: #Presel for index makes no sense
                    if ust_or_presel_name[6:8].lower()=="wq":
                        nb=int(ust_or_presel_name[8:])
                        pr=presel.PreselWQ(period,nb=nb,st=st,**kwargs)
                    elif ust_or_presel_name[6:8].lower()=="ml":
                        PR=getattr(ml,ust_or_presel_name)
                        pr=PR(period,st=st,**kwargs)
                    else:
                        PR=getattr(presel,ust_or_presel_name)
                        pr=PR(period,st=st,**kwargs)
                        
                    pr.run()
                    return pr
                else:
                    return None
            elif ust_or_presel_name[:5]=="Strat":
                try:
                    UST=getattr(strat,ust_or_presel_name)
                except:
                    try:
                        UST=getattr(strat_legacy,ust_or_presel_name)
                    except:
                        raise ValueError(ust_or_presel_name + " underlying strategy not found")
                ust=UST(period,st=st,it_is_index=it_is_index,**kwargs)
                ust.run()
                return ust
            else:
                print("Class " +ust_or_presel_name + " does not respect the convention of starting with Presel or Strat")
                return None
        
    except Exception as e:
          _, e_, exc_tb = sys.exc_info()
          print(e)
          print("line " + str(exc_tb.tb_lineno))
