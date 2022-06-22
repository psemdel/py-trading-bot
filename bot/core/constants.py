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
    CAC40=["ORA.PA", 
           "KER.PA",
           "CA.PA",
           "ML.PA",
           "ATO.PA",
           "ACA.PA",
           "SGO.PA",
           "MC.PA",
           "CAP.PA",
           "WLN.PA",
           "RI.PA",
           "VIE.PA",
           "ENGI.PA",
           "BN.PA",
           "AIR.PA",
           "DG.PA",
           "AC.PA",
           "HO.PA",
           "AI.PA",
           "EN.PA",
           "BNP.PA",
           "SAN.PA",
           "VIV.PA",
           "OR.PA",
           "LR.PA",
           "GLE.PA",
           "SU.PA",
           "SW.PA",
           "TTE.PA",
           "SLB.PA",
           "ALO.PA",
           "CS.PA",
           "DSY.PA",
           "EL.PA",
           "ERF.PA",
           "RMS.PA",
           "PUB.PA",
           "RNO.PA",
           "SAF.PA",
           "STLA.PA",
           "STM.PA",
           "TEP.PA",  #Unibail?
        ]
    
    return CAC40

def dax():
    DAX=["RWE.DE",
         "BEI.DE", 
         "DHER.DE",
         "ZAL.DE",
         "FME.DE",
         "FRE.DE",
         "SY1.DE",
         "BAS.DE",
         "MTX.DE",
         "AIR.DE",
         "MRK.DE", 
         "HEI.DE",
         "BMW.DE",
         "VOW3.DE",
         "DPW.DE",
         "DB1.DE",
         "BAYN.DE",
         "ENR.DE",
         "SHL.DE",
         "1COV.DE",
         "ALV.DE",
         "SIE.DE",
         "CON.DE",
         "IFX.DE",
         "DTE.DE",
         "DBK.DE",
         "ADS.DE",
         "LIN.DE",
         "HFG.DE",
         "PUM.DE",
         "BNR.DE",
         "DTG.DE", #EON?
         "HNR1.DE",
         "HEN3.DE",
         "MBG.DE",
         "MUV2.DE",
         "PAH3.DE",
         "QIA.DE",
         "SAP.DE",
         "SRT.DE",
         "VNA.DE"
        ]
    return DAX

def nasdaq():
    NASDAQ=[
        "AAPL",  #apple
        "ABNB",
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
        "CRWD",
        "CSCO",
        "CSX",
        "CTAS",
        "CTSH",
        "DDOG",
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
        "LCID",
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
        "PTON",
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
        "ZM",
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