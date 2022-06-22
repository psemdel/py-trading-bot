#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  4 14:31:10 2021

@author: maxime
"""
dic={}
dic["^GSPC"]="US"
dic["^IXIC"]="US"
dic["^FTSE"]="UK"
dic["^GDAXI"]="DE"
dic["^FCHI"]="FR"

def symbol_to_market(symbol):
    if symbol in dic:
        return dic[symbol]
    else:
        print("symbol "+ symbol +" not found in market, set to US")
        return "US"
        
dic_stn={
    "^GSPC":"SP500",
    "^FCHI": "CAC40" ,
    "^IXIC":"NASDAQ",
    "^GDAXI": "DAX",
    "^N225": "Nikkei225",
    "^FTSE": "FT SE (London index)",
    "ORA.PA": "Orange",
    "KER.PA": "Kering",
    "CA.PA": "Carrefour",
    "ML.PA": "Michelin",
    "ATO.PA": "Atos",
    "ACA.PA":"Crédit Agricole",
    "SGO.PA":"Saint-Gobain",
    "MC.PA": "LVMH",
    "CAP.PA": "Capgemini",
    "WLN.PA":"Worldline",
    "RI.PA":"Pernod Ricard",  
    "VIE.PA":"Veolia",
    "ENGI.PA":"Engie",
    "BN.PA":"Danone",
    "AIR.PA":"Airbus",
    "DG.PA":"Vinci",
    "AC.PA":"Accor",
    "HO.PA":"Thales",
    "AI.PA":"Air liquide",
    "EN.PA":"Bouygues",
    "BNP.PA":"BNP",
    "SAN.PA":"Sanofi",
    "VIV.PA":"Vivendi",
    "OR.PA":"L'oréal",
    "LR.PA":"Legrand",
    "GLE.PA":"Société générale",
    "SU.PA":"Schneider electric",
    "SW.PA":"Sodexo",
    "TTE.PA":"Total",
    "SLB.PA":"Schlumberger",
    "ALO.PA":"Alstom",
    "MT.PA":"Arcelor",
    "CS.PA":"AXA",
    "DSY.PA":"Dassault Système",
    "EL.PA":"EssilorLuxottica",
    "ERF.PA":"Eurofins Scientific",
    "RMS.PA":"Hermès",
    "PUB.PA":"Publicis",
    "RNO.PA":"Renault",
    "SAF.PA":"Safran",
    "STLA.PA":"Stellantis",
    "STM.PA":"STMicroelectronics",
    "TEP.PA":"Teleperformance",  #Unibail?   
    "RWE.DE":"RWE",
    "BEI.DE":"Beiersdorf", 
    "DHER.DE":"Delivery Hero",
    "ZAL.DE":"Zalendo",
    "FME.DE":"Fresenius Medical",
    "FRE.DE":"Fresenius SE",
    "SY1.DE":"Symrise",
    "BAS.DE":"BASF",
    "MTX.DE":"MTU Aero Engines",
    "AIR.DE":"Airbus DE",
    "MRK.DE":"Merck", 
    "HEI.DE":"HeidelbergCement",
    "BMW.DE":"BMW",
    "VOW3.DE":"Volkswagen",
    "DPW.DE":"Deutsche Post",
    "DB1.DE":"Deutsche Börse",
    "BAYN.DE":"Bayer",
    "ENR.DE":"Siemens Energy",
    "SHL.DE":"Siemens Healthineers",
    "1COV.DE":"Covestro",
    "ALV.DE":"Allianz",
    "SIE.DE":"Siemens",
    "CON.DE":"Continental",
    "IFX.DE":"Infineon",
    "DTE.DE":"Deutsche Telekom",
    "DBK.DE":"DKB",
    "ADS.DE":"Adidas",
    "LIN.DE":"Linde",
    "HFG.DE":"HelloFresh",
    "PUM.DE":"Puma",
    "BNR.DE":"Brenntag",
    "CLR.DE":"Continental",
    "DTG.DE":"Daimler Truck", #EON?
    "HNR1.DE":"Hannover Rückversicherung",
    "HEN3.DE":"Henkel",
    "MBG.DE":"Mercedes",
    "MUV2.DE":"Münchener Rückversicherung",
    "PAH3.DE":"Porsche",
    "QIA.DE":"Qiagen",
    "SAP.DE":"SAP",
    "SRT.DE":"Sartorius",
    "VNA.DE":"Vonovia",    
    "AAPL":"Apple",  #apple
    "ABNB":"Airbnb",
    "ADBE":"Adobe", #adobe
    "ADI":"Analog Device", #analog device
    "ADP":"Automatic Data Processing", #ADP	Automatic Data Processing, Inc. Common Stock
    "ADSK":"Autodesk", #autodesk
    "AEP":"American Electric Company", #American electric company
    "ALGN":"Align", #Align
    "AMAT":"Applied materials",
    "AMD":"AMD",
    "AMGN":"Amgen",
    "AMZN":"Amazon", #amazon
    "ANSS":"Ansys",
    "ASML":"ASML",
    "ATVI":"Activision Blizzard",
    "AVGO":"Broadcom",
    "BIDU":"Baidu",
    "BIIB":"Biogen",
    "BKNG":"Booking Holdings",
    "CDNS":"Cadence Design Systems",
    "CHTR":"Charter Communications",
    "CMCSA":"Comcast",
    "COST":"Costco Wholesale",
    "CPRT":"Copart",
    "CRWD":"CrowdStrike",
    "CSCO":"Cisco",
    "CSX":"CSX",
    "CTAS":"Cintas",
    "CTSH":"Cognizant",
    "DDOG":"Datadog",
    "DLTR":"Dollar Tree",
    "DOCU":"DocuSign",
    "DXCM":"DexCom",
    "EA":"Electronic Arts",
    "EBAY":"Ebay",
    "EXC":"Exelon",
    "FAST":"Fastenal",
    "FB":"Facebook",
    "FISV":"Fiserv",
    "FTNT":"Fortinet",
    "GILD":"Gilead science",
    "GOOG":"Google", #google
    "HON":"Honeywell",
    "IDXX":"Idexx",
    "ILMN":"Illumina",
    "INTC":"Intel",
    "INTU":"Intuit",
    "ISRG":"Intuitive surgical",
    "JD":"JDcom",
    "KDP":"Keurig Dr Pepper",
    "KHC":"Kraft Heinz",
    "KLAC":"Kla",
    "LCID":"Lucid",
    "LRCX":"Lam Research",
    "LULU":"Lululemon",
    "BZ=F":"Brent", #brent
    "CL=F":"Crude oil",  #crude
    "GC=F":"Gold",
    "MCHP":"Microchip",
    "MDLZ":"Mondelez",
    "MELI":"Mercadolibre",
    "MNST":"Monster Beverage",
    "MRNA":"Moderna",
    "MRVL":"Marvell",
    "MSFT":"Microsoft", #microsof
    "MTCH":"Match",
    "MU":"Micron",
    "NFLX":"Netflix",
    "NTES":"Netease",
    "NVDA":"Nvidia",
    "NXPI":"NXP semiconductor",
    "OKTA":"Okta",
    "ORLY":"O'Reilly",
    "PANW":"Palo Alto Networks",
    "PAYX":"Paychex",
    "PCAR":"Paccar",
    "PDD":"Pinduoduo",
    "PEP":"Pepsi",
    "PTON":"Peloton",
    "PYPL":"Paypal",
    "QCOM":"Qualcomm",
    "REGN":"Regeneron",
    "ROST":"Ross Stores",
    "SBUX":"Starbucks",
    "SGEN":"Seagen",
    "SIRI":"Sirlus",
    "SNPS":"Synopsis",
    "SPLK":"Splunk",
    "SWKS":"Skyworks",
    "TEAM":"Atlassian",
    "TMUS":"T-Mobile US",
    "TSLA":"Tesla",
    "TXN":"Texas Instrument",
    "VRSK":"Verisk",
    "VRSN":"Verisign",
    "VRTX":"Vertex",
    "WBA":"Walgreens Boots Alliance",
    "WDAY":"Workday",
    "XEL":"Xcel Energy",
    "XLNX":"Xilinx",
    "ZM":"Zoom Video Communications",
    "ZS":"Zscaler"
    }

def symbol_to_name(symbol):
    if symbol in dic_stn:
        return dic_stn[symbol]
    else:
        return symbol