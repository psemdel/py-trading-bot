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
   o=Opt("2007_2022",loops=1)
   
if False:
   #optimize the strategy without macro
   from opt.opt_strat import Opt
   
   o=Opt("2007_2022",
          loops=40,
          nb_macro_modes=1
          )
   
if False:
   #optimize the strategy with macro
   from opt.opt_strat import Opt
   
   #only for predefined
   a_bull=[1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1,
          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
   a_bear=[0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1,
   0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0]
   a_uncertain= [1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1,
   0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0]

   o=Opt("2007_2023",
          loops=40,
          predefined=False,
          a_bull=a_bull,
          a_bear=a_bear,
          a_uncertain=a_uncertain,   
          #sl=0.005
          #index=True
          macro_trend_bull="long", 
          macro_trend_uncertain="both",
          macro_trend_bear="both",
          #test_window_start=0
          )
   o.perf()
   #o.test_by_part()
   
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

    o=Opt("2007_2022_08",
           loops=40,
          # predefined=True,
           #a_bull=a_bull,
          # a_bear=a_bear,
         #  a_uncertain=a_uncertain,   
           )
    
if False:
    from opt.opt_div import Opt
    
    a_bull=[0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
   0., 0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 1., 1.,
   1., 0., 1., 0., 0., 0., 0., 1., 0., 0.]
  #  a_bear=[0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
  # 0., 0., 0., 0., 0., 
  # 0., 1, 1., 0., 0., 1., 0., 0., 0., 0., 0., 0.,
  # 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
  #  a_uncertain= [0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
  # 0., 0., 0., 0., 0., 
  #   0., 1, 1., 0., 0., 1., 0., 0., 0., 0., 0., 0.,
  # 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    
    o=Opt("2007_2023",
           loops=40,
           nb_macro_modes=3,
           #predefined=True,
           #a_bull=a_bull,
           #a_bear=a_bear,
           #a_uncertain=a_uncertain,   
           )   

if False:
    from opt.opt_weighted import Opt
    
    o=Opt("2007_2023",
           loops=40,
           #nb_macro_modes=3,
           )  
    
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
    
    o=Opt("2007_2023",
           nb_macro_modes=3,
           predefined=True,
           a_bull=a_bull,
           a_bear=a_bear,
           a_uncertain=a_uncertain, 
           #index=True
           )      
    
#o.perf()  

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

    o=Opt("2007_2020",
           nb_macro_modes=3,
           predefined=True,
           a_bull=a_bull,
           a_bear=a_bear,
           a_uncertain=a_uncertain, 
           #index=True
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

    o=OptRecursive("2007_2023",
           nb_macro_modes=3,
           predefined=True,
           a_bull=a_bull,
           a_bear=a_bear,
           a_uncertain=a_uncertain, 
           #index=True,
           test_window_start=0
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

        o=Opt("2007_2023",
               indexes=indexes,
               nb_macro_modes=3,
               predefined=True,
               a_bull=a_bull,
               a_bear=a_bear,
               a_uncertain=a_uncertain, 
               #index=True,
               test_window_start=0
               )  
        
        o.outer_perf()      
  
if True:
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
    o=Opt("2007_2023",
           indexes,
           symbols,
           nb_macro_modes=3,
           predefined=True,
           a_bull=a_bull,
           a_bear=a_bear,
           a_uncertain=a_uncertain, 
           #index=True,
           test_window_start=0
           )  
    
    o.outer_perf()  
