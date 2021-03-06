#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 12 11:27:07 2021

@author: maxime
"""


#For use with Talib
PATTERNS={}
PATTERNS["Pattern"]=["CDL2CROWS", "CDL3BLACKCROWS", "CDL3INSIDE", "CDL3LINESTRIKE",
          "CDL3OUTSIDE", "CDL3STARSINSOUTH", "CDL3WHITESOLDIERS",
          "CDLABANDONEDBABY","CDLADVANCEBLOCK", "CDLBELTHOLD",
          "CDLBREAKAWAY", "CDLCLOSINGMARUBOZU", "CDLCONCEALBABYSWALL",
          "CDLCOUNTERATTACK", "CDLDARKCLOUDCOVER", "CDLDOJI",
          "CDLDOJISTAR", "CDLDRAGONFLYDOJI", "CDLENGULFING", 
          "CDLEVENINGDOJISTAR", "CDLEVENINGSTAR", "CDLGAPSIDESIDEWHITE",
          "CDLGRAVESTONEDOJI", "CDLHAMMER", "CDLHANGINGMAN", "CDLHARAMI",
          "CDLHARAMICROSS", "CDLHIGHWAVE", "CDLHIKKAKE", "CDLHIKKAKEMOD",
          "CDLHOMINGPIGEON", "CDLIDENTICAL3CROWS", "CDLINNECK",
          "CDLINVERTEDHAMMER", "CDLKICKING", "CDLKICKINGBYLENGTH",
          "CDLLADDERBOTTOM", "CDLLONGLEGGEDDOJI", "CDLLONGLINE",
          "CDLMARUBOZU", "CDLMATCHINGLOW", "CDLMATHOLD", "CDLMORNINGDOJISTAR",
          "CDLMORNINGSTAR", "CDLONNECK", "CDLPIERCING", "CDLRICKSHAWMAN",
          "CDLRISEFALL3METHODS", "CDLSEPARATINGLINES", "CDLSHOOTINGSTAR",
          "CDLSHORTLINE", "CDLSPINNINGTOP", "CDLSTALLEDPATTERN",
          "CDLSTICKSANDWICH", "CDLTAKURI", "CDLTASUKIGAP","CDLTHRUSTING",
          "CDLTRISTAR","CDLUNIQUE3RIVER","CDLUPSIDEGAP2CROWS",
          "CDLXSIDEGAP3METHODS"
          ]

PATTERNS["Trends"]=["HT_TRENDMODE"]
PATTERNS["Trends2"]=["MACD","BBANDS"]

PATTERNS["Crosses"]=["HT_SINE", "MACD","AROON","STOCH"]  # "APO" crosses 0 also interesting
PATTERNS["Extremum"]=["APO", "ADX"] 
PATTERNS["Extremum2"]=[ "KAMA","EMA"]  
PATTERNS["Extremum_approx"]=["APO", "ADX", "KAMA","EMA"]  
PATTERNS["Medtrends"]=["KAMA", "EMA"]  
PATTERNS["Bands"]=["BBANDS"]
PATTERNS["Over"]=["RSI","WILLR","ULTOSC","STOCH"]
PATTERNS["Vol"]=["NATR","TRANGE"]
PATTERNS["Flag"]=["Flag_reverse_bear","Flag_reverse_bull"]


#To find the columns afterwards
PATTERNS2=PATTERNS.copy()
PATTERNS2["YN1"]=["TRENDPASTDAY"] 
PATTERNS2["Extremum2"]=["KAMAEXT", "EMAEXT"]

PATTERNS_HIGH=[ "CDLBELTHOLD"]
"""    
    "CDL3BLACKCROWS", "CDL3INSIDE", "CDL3LINESTRIKE","CDLABANDONEDBABY",
               "CDLBELTHOLD",
               "CDLCLOSINGMARUBOZU", "CDLCONCEALBABYSWALL",
               "CDLCOUNTERATTACK", "CDLDARKCLOUDCOVER", 
               "CDLENGULFING", 
               "CDLEVENINGDOJISTAR", "CDLEVENINGSTAR", 
               "CDLHIKKAKE", "CDLHIKKAKEMOD",
               "CDLIDENTICAL3CROWS", "CDLKICKING", "CDLKICKINGBYLENGTH",
               "CDLLONGLINE",
               "CDLMARUBOZU", "CDLMATHOLD", "CDLMORNINGDOJISTAR",
               "CDLMORNINGSTAR", 
               "CDLRISEFALL3METHODS", "CDLSEPARATINGLINES", 
               "CDLSTICKSANDWICH", "CDLUPSIDEGAP2CROWS",
               "CDLXSIDEGAP3METHODS"
               ]#highly reliable pattern
"""
#PATTERNS2["Pattern"]=PATTERNS_HIGH #TEMP

BEAR_PATTERNS={
    "CDLRISEFALL3METHODS":-1,
    "CDL3LINESTRIKE":1,
    "CDLBREAKAWAY":-1,
    "CDLABANDONEDBABY":-1,
    "CDLEVENINGSTAR":-1,
    "CDLCLOSINGMARUBOZU":-1,
    "CDLEVENINGDOJISTAR":-1,
    "CDL3BLACKCROWS":-1,
    "CDLDARKCLOUDCOVER":-1,
    "CDLLONGLINE":-1,
    "CDLENGULFING":-1,
    "CDLSEPARATINGLINES":-1,
    "CDLBELTHOLD":-1,
    "CDLHIKKAKE":-2
    }

BULL_PATTERNS={
    "CDLKICKINGBYLENGTH":1,
    "CDLKICKING":1,
    "CDLMARUBOZU":1,
    "CDLCLOSINGMARUBOZU":1,
    "CDL3WHITESOLDIERS":1,
    "CDLLONGLINE":1,
    "CDLENGULFING":1,
    }

BEAR_PATTERNS_LIGHT={
    "CDLRISEFALL3METHODS":-1,
    "CDL3LINESTRIKE":1,
    "CDLBREAKAWAY":-1,
    "CDLABANDONEDBABY":-1,
    "CDLEVENINGSTAR":-1,
    "CDLCLOSINGMARUBOZU":-1,
    "CDLEVENINGDOJISTAR":-1,
    "CDL3BLACKCROWS":-1,
    "CDLDARKCLOUDCOVER":-1,
    "CDLLONGLINE":-1,
    "CDLENGULFING":-1,
    "CDLSEPARATINGLINES":-1,
    "CDLBELTHOLD":-1,
    "CDLHIKKAKE":-2
    }

BULL_PATTERNS_LIGHT={
    "CDLENGULFING":1,
    }

def bear_patterns():
    return BEAR_PATTERNS

def bull_patterns():
    return BULL_PATTERNS

def bear_patterns_light():
    return BEAR_PATTERNS_LIGHT

def bull_patterns_light():
    return BULL_PATTERNS_LIGHT

def all_methods():
    METHODS=["Pattern","Crosses", "Extremum","Extremum2",#"Extremum_approx",
             "Medtrends","Trends", "Trends2", #"Vol",
             "Bands", "Over", "YN1"]
    
    return METHODS

def patterns():
    return PATTERNS

def patterns_search():

    return PATTERNS2

def cac40(): #top 30
    CAC40=[
        "AC.PA",
        "ACA.PA",
        "AI.PA",
        "AIR.PA",
        "ALO.PA",
        "ATO.PA",
        "BN.PA",
        "BNP.PA",
        "CA.PA",
        "CAP.PA",
        "CS.PA",
        "DG.PA",
        "DSY.PA",
        "EL.PA",
        "EN.PA",
        "ENGI.PA",
        "ERF.PA",
        "GLE.PA",
        "HO.PA",
        "KER.PA",
        "LR.PA",
        "MC.PA",
        "ML.PA",
        "OR.PA",
        "ORA.PA", 
        "PUB.PA",
        "RI.PA",   
        "RMS.PA",
        "RNO.PA",
        "SAF.PA",
        "SAN.PA",
        "SGO.PA",
        "SLB.PA",
        #"STLA.PA", #removed as too new
        "STM.PA",
        "SU.PA",
        "SW.PA",
        "TEP.PA",  #Unibail?
        "TTE.PA",
        "VIE.PA",
        "VIV.PA",
        "WLN.PA",
        ]
    
    return CAC40

def dax():
    DAX=[
        "1COV.DE",
        "ADS.DE",
        "AIR.DE",
        "ALV.DE",
        "BAS.DE",
        "BAYN.DE",
        "BEI.DE", 
        "BMW.DE",
        "BNR.DE",
        "CON.DE",
        "DB1.DE",
        "DBK.DE",
        "DHER.DE",
        "DPW.DE",
        "DTE.DE", 
        #"DTG.DE", #Too new
        #"ENR.DE", #too new
        "FME.DE",
        "FRE.DE",
        "HEI.DE",
        "HEN3.DE",
        "HFG.DE",
        "HNR1.DE",
        "IFX.DE",
        "LIN.DE",
        "MBG.DE",
        "MRK.DE", 
        "MTX.DE",
        "MUV2.DE",
        "PAH3.DE",
        "PUM.DE",
        "QIA.DE",
        "RWE.DE",
        "SAP.DE",
        "SHL.DE",
        "SIE.DE",
        "SRT.DE",
        "SY1.DE",
        "VNA.DE"
        "VOW3.DE",
        "ZAL.DE",
        ]
    return DAX

def nasdaq():
    NASDAQ=[
        "AAPL",  #apple
       # "ABNB", #too new
        "ADBE", #adobe
        "ADI", #analog device
        "ADP", #ADP	Automatic Data Processing, Inc. Common Stock
        "ADSK", #autodesk
        "AEP", #American electric company
        "ALGN", #Align
        "AMAT",
        "AMD",
        "AMGN",
        "AMZN", #amazon
        "ANSS",
        "ASML",
        "ATVI",
        "AVGO",
        "BIDU",
        "BIIB",
        "BKNG",
        "CDNS",
        "CHTR",
        "CMCSA",
        "COST",
        "CPRT",
        #"CRWD", #too new
        "CSCO",
        "CSX",
        "CTAS",
        "CTSH",
        #"DDOG", #too new
        "DLTR",
        "DOCU",
        "DXCM",
        "EA",
        "EBAY",
        "EXC",
        "FAST",
        "FB",
        "FISV",
        "FTNT",
        "GILD",
        "GOOG", #google
        "HON",
        "IDXX",
        "ILMN",
        "INTC",
        "INTU",
        "ISRG",
        "JD",
        "KDP",
        "KHC",
        "KLAC",
        #"LCID", #too new
        "LRCX",
        "LULU",
       # "MAR",
        "MCHP",
        "MDLZ",
        "MELI",
        "MNST",
        "MRNA",
        "MRVL",
        "MSFT", #microsof
        "MTCH",
        "MU",
        "NFLX",
        "NTES",
        "NVDA",
        "NXPI",
        "OKTA",
        "ORLY",
        "PANW",
        "PAYX",
        "PCAR",
        "PDD",
        "PEP",
        #"PTON", #too new
        "PYPL",
        "QCOM",
        "REGN",
        "ROST",
        "SBUX",
        "SGEN",
        "SIRI",
        "SNPS",
        "SPLK",
        "SWKS",
        "TEAM",
        "TMUS",
        "TSLA",
        "TXN",
        "VRSK",
        "VRSN",
        "VRTX",
        "WBA",
        "WDAY",
        "XEL",
#        "XLNX",
        #"ZM", #too new
        "ZS"
        ]
    return NASDAQ

def indexes():
    INDEXES=["^GSPC", #SP500
             "^FCHI", #cac40 
             "^IXIC", #NASDAQ
             "^GDAXI", #DAX
             "^N225", #Nikkei
             "^FTSE",
        ]

    return INDEXES    

def raw():
    RAW=["BZ=F", #brent
         "CL=F",  #crude
         "GC=F", #gold
         ]
    
    return RAW

#DOW
#