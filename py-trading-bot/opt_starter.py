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
   
if True:
    #optimize bt
    from opt.opt_presel import Opt
   
    #only for predefined
    a={'bull': {'ent': ['CDLINNECK', 'CDL3BLACKCROWS'],
                    'ex': ['WILLR','SUPERTREND','BBANDS','CDLBELTHOLD','CDLRISEFALL3METHODS','CDLEVENINGDOJISTAR',
                           'CDLUNIQUE3RIVER','CDLCOUNTERATTACK','CDLMORNINGDOJISTAR']},
            'bear': {'ent': ['CDL3BLACKCROWS'],
             'ex': ['STOCH','SUPERTREND','ULTOSC20','CDLCLOSINGMARUBOZU','CDLRISEFALL3METHODS','CDLUNIQUE3RIVER',
              'CDLCOUNTERATTACK']},
            'uncertain': {'ent': ['CDL3BLACKCROWS'],
             'ex': ['SUPERTREND','RSI20','ULTOSC20','ULTOSC25','CDLRISEFALL3METHODS','CDLABANDONEDBABY',
              'CDLHIKKAKEMOD','CDLUNIQUE3RIVER']}}

    o=Opt(
        "PreselDivergence",
        "2007_2023_08",
         loops=40,
         filename="divergence",
         #strat_arr=a,
         #opt_only_exit=True,
         #second=True
         )
    o.perf()   

if False:
    #optimize retard keep
    from opt.opt_keep import Opt

    #only for predefined
    
    a={'bull': {'ent': ['RSI20'],
                'ex':['SUPERTREND',"CDLENGULFING", "CDLSEPARATINGLINES","CDLEVENINGDOJISTAR","CDLDARKCLOUDCOVER"]},
       'bear': {'ent': ['RSI20'],
                'ex': ["CDL3LINESTRIKE","CDLSEPARATINGLINES","CDLEVENINGDOJISTAR"]},
       'uncertain': {'ent': ['RSI20'],
                     'ex': ['RSI20',"CDLEVENINGDOJISTAR"]}
      }
    o=Opt(
         "2007_2023_08",
         loops=40,
         filename="keep",
         strat_arr=a,
         #test_window_start_init=0,
         opt_only_exit=True,
         #testing=True
         )
    o.perf() 

    
if False:
   #optimize the strategy with macro
    from opt.opt_strat import Opt

    a={'bull': {'ent': ['KAMA','RSI20','RSI30','CDLMARUBOZU',"CDL3WHITESOLDIERS","CDLENGULFING","CDLTAKURI","CDLMORNINGDOJISTAR","CDLMORNINGSTAR","CDLKICKING_INV"],
                'ex': ["CDLRISEFALL3METHODS","CDLABANDONEDBABY"]},
       'bear': {'ent': ['STOCH','RSI20','RSI30',"CDLMARUBOZU","CDL3WHITESOLDIERS","CDLLONGLINE","CDLENGULFING","CDLTAKURI",
                        "CDLMORNINGDOJISTAR","CDLHANGINGMAN","CDLKICKINGBYLENGTH_INV"],
                'ex': ['SUPERTREND','BBANDS',"CDLBELTHOLD"]},
       'uncertain': {'ent': ['STOCH','KAMA','RSI20','RSI30',"CDLMARUBOZU","CDLCLOSINGMARUBOZU","CDL3WHITESOLDIERS","CDLLONGLINE","CDLENGULFING",
                             "CDLMORNINGDOJISTAR","CDLHANGINGMAN","CDLKICKINGBYLENGTH_INV","CDLKICKING_INV"],
                     'ex': ["CDLHIKKAKE","CDL3LINESTRIKE","CDLBREAKAWAY"]}} 

    o=Opt("2007_2023_08",
          loops=40,
          #strat_arr=a,
          #sl=0.005
          #it_is_index=True,
          dir_bull="long", 
          dir_uncertain="both",
          dir_bear="both",
          filename="strat_abs",
          #second=True
          #fees=0,
          #test_window_start_init=0
          )
    
    o.perf()
    #o.summary_total("total")
    #o.test_by_part()
           
if False:
    from opt.opt_sl import Opt
    
    a={'bull': {'ent': ['KAMA','RSI20','RSI30','CDLMARUBOZU',"CDL3WHITESOLDIERS","CDLENGULFING","CDLTAKURI","CDLMORNINGDOJISTAR","CDLMORNINGSTAR","CDLKICKING_INV"],
                'ex': ["CDLRISEFALL3METHODS","CDLABANDONEDBABY"]},
       'bear': {'ent': ['STOCH','RSI20','RSI30',"CDLMARUBOZU","CDL3WHITESOLDIERS","CDLLONGLINE","CDLENGULFING","CDLTAKURI",
                        "CDLMORNINGDOJISTAR","CDLHANGINGMAN","CDLKICKINGBYLENGTH_INV"],
                'ex': ['SUPERTREND','BBANDS',"CDLBELTHOLD"]},
       'uncertain': {'ent': ['STOCH','KAMA','RSI20','RSI30',"CDLMARUBOZU","CDLCLOSINGMARUBOZU","CDL3WHITESOLDIERS","CDLLONGLINE","CDLENGULFING",
                             "CDLMORNINGDOJISTAR","CDLHANGINGMAN","CDLKICKINGBYLENGTH_INV","CDLKICKING_INV"],
                     'ex': ["CDLHIKKAKE","CDL3LINESTRIKE","CDLBREAKAWAY"]}} 
    
    o=Opt("2007_2022_08",
           nb_macro_modes=3,
           strat_arr=a,
           filename="sl",
           #it_is_index=True
           )      
    
    o.perf()  

if False:
    from opt.opt_by_part import Opt
    
    a={'bull': {'ent': ['KAMA','RSI20','RSI30','CDLMARUBOZU',"CDL3WHITESOLDIERS","CDLENGULFING","CDLTAKURI","CDLMORNINGDOJISTAR","CDLMORNINGSTAR","CDLKICKING_INV"],
                'ex': ["CDLRISEFALL3METHODS","CDLABANDONEDBABY"]},
       'bear': {'ent': ['STOCH','RSI20','RSI30',"CDLMARUBOZU","CDL3WHITESOLDIERS","CDLLONGLINE","CDLENGULFING","CDLTAKURI",
                        "CDLMORNINGDOJISTAR","CDLHANGINGMAN","CDLKICKINGBYLENGTH_INV"],
                'ex': ['SUPERTREND','BBANDS',"CDLBELTHOLD"]},
       'uncertain': {'ent': ['STOCH','KAMA','RSI20','RSI30',"CDLMARUBOZU","CDLCLOSINGMARUBOZU","CDL3WHITESOLDIERS","CDLLONGLINE","CDLENGULFING",
                             "CDLMORNINGDOJISTAR","CDLHANGINGMAN","CDLKICKINGBYLENGTH_INV","CDLKICKING_INV"],
                     'ex': ["CDLHIKKAKE","CDL3LINESTRIKE","CDLBREAKAWAY"]}} 

    o=Opt("2007_2022_08",
           nb_macro_modes=3,
           strat_arr=a,
           filename="by_part",
           #it_is_index=True
           )  
    
    o.outer_perf()      
    

  
   
  

