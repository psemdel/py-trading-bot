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
          loops=1,
          nb_macro_modes=1
          )
   
if False:
   #optimize the strategy with macro
   from opt.opt_strat import Opt
   
   #only for predefined
   a_bull=[0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       1., 0., 1., 0., 0., 0., 0., 0., 0., 0.]
   a_bear=[0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0.,
       1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 1., 0.,
       0., 0., 1., 0., 0., 0., 0., 0., 0., 0.]
   a_uncertain=[0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 1., 0., 0.,
       1., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0.,
       0., 0., 1., 0., 1., 0., 0., 0., 0., 0.]

   o=Opt("2007_2022",
          loops=1,
          predefined=True,
          a_bull=a_bull,
          a_bear=a_bear,
          a_uncertain=a_uncertain,         
          #macro_trend_bull="short", 
          #macro_trend_uncertain="short",
          #macro_trend_bear="short"
          )
   
if True:
    #optimize bt
    from opt.opt_bt import Opt
   
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
    a_bear=[0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
   0., 0., 0., 0., 0., 
   0., 1, 1., 0., 0., 1., 0., 0., 0., 0., 0., 0.,
   0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    a_uncertain= [0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
   0., 0., 0., 0., 0., 
     0., 1, 1., 0., 0., 1., 0., 0., 0., 0., 0., 0.,
   0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    
    o=Opt("2007_2022_08",
           loops=40,
           nb_macro_modes=1,
           fees=0.0001,
           predefined=True,
           a_bull=a_bull,
           a_bear=a_bear,
           a_uncertain=a_uncertain,   
           )   

o.perf() 
