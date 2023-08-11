#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 28 17:07:13 2022

@author: maxime
"""

#Starts the script to optimize parameters relative to different points of the strategy

if False:
   #optimize the trend parameters
   from opt.opt_macro import Opt
   o=Opt("2007_2022_08",filename="macro",loops=1)
   
if False:
   #optimize the strategy without macro
   from opt.opt_strat import Opt
   
   o=Opt("2007_2022_08",
          loops=40,
          nb_macro_modes=1,
          filename="strat_simple",
          )
   
if False:
    #optimize bt
    from opt.opt_presel import Opt
   
    #only for predefined
    a_bull=[0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0.,
    0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]  
    a_bear=[0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0.,
    0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]  
    a_uncertain= [0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0.,
    0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0.,
    0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]  

    o=Opt(
        "PreselDivergence",
        "2007_2022_08",
         loops=40,
         filename="divergence",
          # predefined=True,
           #a_bull=a_bull,
          # a_bear=a_bear,
         #  a_uncertain=a_uncertain,   
           )
    o.perf()   
    
if True:
   #optimize the strategy with macro
    from opt.opt_strat import Opt

   #only for predefined
    a_bull=[1., 0., 0., 1., 0., 1., 1., 0., 0., 1., 0., 1., 0., 0., 0., 1.,
            1., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
            0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    a_bear=[0., 1., 0., 0., 0., 1., 1., 0., 0., 1., 0., 1., 1., 1., 1., 1.,
     1., 0., 1., 0., 1., 0., 0., 0., 0., 1., 0., 1., 0., 0., 0., 0.,
     1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    a_uncertain= [0., 1., 1., 0., 0., 1., 1., 0., 0., 1., 1., 1., 1., 0., 0., 0.,
     0., 0., 0., 1., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
     0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    
    o=Opt("2007_2023_08",
          loops=40,
          predefined=True,
          a_bull=a_bull,
          a_bear=a_bear,
          a_uncertain=a_uncertain,   
          #sl=0.005
          #it_is_index=True
          dir_bull="long", 
          dir_uncertain="both",
          dir_bear="both",
          filename="strat",
          #fees=0,
          #test_window_start_init=0
          )
    
    #o.perf()"
    o.summary_total("total")
    
    #o.test_by_part()
           
if False:
    from opt.opt_sl import Opt
    
    a_bull=[0., 0., 1., 0., 0., 1., 1., 0., 0., 0., 0., 1., 0., 1., 0., 1.,
        1., 1., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0.]
    a_bear= [0., 1., 0., 0., 1., 1., 1., 0., 0., 1., 0., 1., 1., 0., 0., 1.,
        0., 0., 0., 1., 1., 0., 0., 0., 0., 1., 1., 0., 1., 0., 0., 0.,
        1., 0., 1., 0., 1., 0., 0., 0., 0., 1., 0., 0.]
    a_uncertain=   [0., 1., 1., 0., 0., 1., 0., 0., 0., 1., 1., 1., 1., 1., 0., 0.,
        1., 0., 1., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
        0., 1., 0., 1., 0., 0., 0., 0., 0., 1., 0., 0.]
    
    o=Opt("2007_2022_08",
           nb_macro_modes=3,
           predefined=True,
           a_bull=a_bull,
           a_bear=a_bear,
           a_uncertain=a_uncertain, 
           filename="sl",
           #it_is_index=True
           )      
    
    o.perf()  

if False:
    from opt.opt_by_part import Opt
    
    a_bull=[0., 0., 1., 0., 0., 1., 1., 0., 0., 0., 0., 1., 0., 1., 0., 1.,
        1., 1., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0.]
    a_bear=   [0., 1., 0., 0., 1., 1., 1., 0., 0., 1., 0., 1., 1., 0., 0., 1.,
        0., 0., 0., 1., 1.,-+ 0., 0., 0., 0., 1., 1., 0., 1., 0., 0., 0.,
        1., 0., 1., 0., 1., 0., 0., 0., 0., 1., 0., 0.]
    a_uncertain=[0., 1., 1., 0., 0., 1., 0., 0., 0., 1., 1., 1., 1., 1., 0., 0.,
        1., 0., 1., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
        0., 1., 0., 1., 0., 0., 0., 0., 0., 1., 0., 0.]

    o=Opt("2007_2022_08",
           nb_macro_modes=3,
           predefined=True,
           a_bull=a_bull,
           a_bear=a_bear,
           a_uncertain=a_uncertain, 
           filename="by_part",
           #it_is_index=True
           )  
    
    o.outer_perf()      
    
if False:
    from opt.opt_by_part_rec import OptRecursive
    
    a_bull=[ 0.,  0.,  0.,  1.,  1.,  1.,  1.,  0.,  0.,  0.,  1.,  1.,  0.,
             0.,  0.,  1.,  1.,  1.,  0.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,
             0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  1.,  0.,
             0.,  0.,  0.,  0.,  0.]
    a_bear=  [ 1.,  1.,  0.,  0.,  1.,  1.,  1.,  0.,  0.,  1.,  0.,  1.,  0.,
      0.,  0.,  0.,  0.,  0.,  1.,  0.,  1., -0.,  0.,  0.,  0.,  1.,
      0.,  0.,  1.,  0.,  0.,  0.,  0.,  0.,  1.,  1.,  0.,  1.,  0.,
      0.,  0.,  0.,  0.,  0.]
    a_uncertain= [ 1.,  0.,  1.,  1.,  0.,  1.,  1.,  0.,  0.,  1.,  1.,  1.,  1.,
      1.,  0.,  0.,  0.,  0.,  1.,  1.,  0.,  1.,  0.,  0.,  0.,  0.,
      0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  0.,  0.,
      0.,  0.,  1.,  0.,  0.]

    o=OptRecursive("2007_2022_08",
           nb_macro_modes=3,
           predefined=True,
           a_bull=a_bull,
           a_bear=a_bear,
           a_uncertain=a_uncertain, 
           #it_is_index=True,
           test_window_start_init=0,
           filename="recursive",
           )  
    
    o.perf_recursion()    
  
if False:
    from opt.opt_corr import Opt
    
    a_bull=[ 0.,  0.,  0.,  1.,  1.,  1.,  1.,  0.,  0.,  0.,  1.,  1.,  0.,
             0.,  0.,  1.,  1.,  1.,  0.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,
             0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  1.,  0.,
             0.,  0.,  0.,  0.,  0.]
    a_bear=  [ 1.,  1.,  0.,  0.,  1.,  1.,  1.,  0.,  0.,  1.,  0.,  1.,  0.,
      0.,  0.,  0.,  0.,  0.,  1.,  0.,  1., -0.,  0.,  0.,  0.,  1.,
      0.,  0.,  1.,  0.,  0.,  0.,  0.,  0.,  1.,  1.,  0.,  1.,  0.,
      0.,  0.,  0.,  0.,  0.]
    a_uncertain= [ 1.,  0.,  1.,  1.,  0.,  1.,  1.,  0.,  0.,  1.,  1.,  1.,  1.,
      1.,  0.,  0.,  0.,  0.,  1.,  1.,  0.,  1.,  0.,  0.,  0.,  0.,
      0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  0.,  0.,
      0.,  0.,  1.,  0.,  0.]

    for indexes in ["CAC40","DAX","NASDAQ","IT"]:

        o=Opt("2007_2022_08",
               indexes=indexes,
               nb_macro_modes=3,
               predefined=True,
               a_bull=a_bull,
               a_bear=a_bear,
               a_uncertain=a_uncertain, 
               #it_is_index=True,
               test_window_start_init=0,
               filename="corr",
               )  
        
        o.outer_perf()      
  
if False:
    from opt.opt_symbols import Opt
    
    a_bull=[ 0.,  0.,  0.,  1.,  1.,  1.,  1.,  0.,  0.,  0.,  1.,  1.,  0.,
             0.,  0.,  1.,  1.,  1.,  0.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,
             0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  1.,  0.,
             0.,  0.,  0.,  0.,  0.]
    a_bear=  [ 1.,  1.,  0.,  0.,  1.,  1.,  1.,  0.,  0.,  1.,  0.,  1.,  0.,
      0.,  0.,  0.,  0.,  0.,  1.,  0.,  1., -0.,  0.,  0.,  0.,  1.,
      0.,  0.,  1.,  0.,  0.,  0.,  0.,  0.,  1.,  1.,  0.,  1.,  0.,
      0.,  0.,  0.,  0.,  0.]
    a_uncertain= [ 1.,  0.,  1.,  1.,  0.,  1.,  1.,  0.,  0.,  1.,  1.,  1.,  1.,
      1.,  0.,  0.,  0.,  0.,  1.,  1.,  0.,  1.,  0.,  0.,  0.,  0.,
      0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  0.,  0.,
      0.,  0.,  1.,  0.,  0.]

    indexes="CAC40"
    symbols=['AC', 'ATO', 'RNO']
    o=Opt("2007_2022_08",
           indexes,
           symbols,
           nb_macro_modes=3,
           predefined=True,
           a_bull=a_bull,
           a_bear=a_bear,
           a_uncertain=a_uncertain, 
           #it_is_index=True,
           test_window_start_init=0,
           filename="symbols",
           )  
    
    o.outer_perf()  
