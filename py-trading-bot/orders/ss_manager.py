#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 31 22:49:50 2023

@author: maxime
"""

import vectorbtpro as vbt
import numpy as np
import pandas as pd
import numbers

from orders.models import StockStatus, Strategy, Action, StockEx
from orders.ib import OrderPerformer
from trading_bot.settings import _settings

import logging
logger = logging.getLogger(__name__)

'''
This file contains StockStatusManager, see description below
'''
class StockStatusManager():
    def __init__(self, report, exchange: str=None, testing:bool=False, ):
        """
        This function keep track of the present state of the portfolio
        
        By measuring the difference between the desired state and the present state, it will perform reconciliation
        
        It is called during the generation of a report
        
        Arguments
       	----------
           report: report associated with the stockstatus manager, useful to resolve
           exchange: name of the stock exchange
           testing: should be true for testing and avoiding orders

        """
        if exchange is not None:
            s_ex=StockEx.objects.get(name=exchange)
            self.present_ss= pd.DataFrame.from_records(StockStatus.objects.filter(action__stock_ex=s_ex).values(),index="action_id")
            comp= pd.DataFrame.from_records(Action.objects.filter(stock_ex=s_ex).values("symbol","etf_long_id","etf_short_id"),index="symbol")
        else:
            self.present_ss= pd.DataFrame.from_records(StockStatus.objects.all().values(),index="action_id")
            comp= pd.DataFrame.from_records(Action.objects.all().values("symbol","etf_long_id","etf_short_id"),index="symbol")
        self.present_ss=pd.concat([self.present_ss,comp], axis=1)

        #condensated version
        self.target_ss=self.present_ss.copy()
        self.target_ss["priority"]=np.nan

        #will contain the target normalized quantity for each stock
        if exchange is not None:
            self.target_ss_by_st=pd.DataFrame.from_records(StockStatus.objects.filter(action__stock_ex=s_ex).values("action_id"),index="action_id")
            comp= pd.DataFrame.from_records(Action.objects.filter(stock_ex=s_ex).values("symbol","category_id"),index="symbol")
        else:
            self.target_ss_by_st=pd.DataFrame.from_records(StockStatus.objects.all().values("action_id"),index="action_id")
            comp= pd.DataFrame.from_records(Action.objects.all().values("symbol","category_id"),index="symbol")
            
        self.target_ss_by_st.rename(columns={"action_id": "symbol"},inplace=True)    
        self.target_ss_by_st=pd.concat([self.target_ss_by_st,comp], axis=1)
        
        for st in Strategy.objects.all():
            self.target_ss_by_st[st.name]=np.nan
        
        self.priority_st_lookup=pd.DataFrame.from_records(Strategy.objects.all().values("id","name", "priority"),index="id")
        self.priority_st_lookup.loc[np.nan]={"name":"not found","priority":1000}

        self.report=report
        self.testing=testing
    
    #to be written in a more pandas way
    def determine_target_sub(
            self, 
            df, 
            it_is_index):
        '''
        After the filling of self.target_ss_by_st by the different strategies, this function will summarize the decision in
        self.target_ss
        
        Because of the ETF, the operation is performed in two parts: for the stocks and for the index
        
        Should be executed only once
        
        Note: the desired behavior is:
            if strat with higher prio says to buy (=hold)/sell, it will buy (=hold)/sell. 
            if strat with higher prio says nothing, look at lower prio
        Arguments
       	----------
           df: subset of self.target_ss_by_st to summarize
           it_is_index: Is it indexes or stocks?
        '''
        try:
            r1=(self.present_ss["quantity"]!=0)
            #init with present value, otherwise put 1000 and 0
            self.target_ss.loc[r1,"strategy_id"]=self.present_ss.loc[r1,"strategy_id"]
            self.target_ss.loc[r1,"priority"]=self.priority_st_lookup.loc[self.present_ss.loc[r1,"strategy_id"],"priority"].values
            self.target_ss.loc[~r1,"priority"]=1000
            self.target_ss.loc[r1,"norm_quantity"]=np.divide(self.present_ss.loc[r1,"quantity"], abs(self.present_ss.loc[r1,"quantity"]))
            self.target_ss.loc[~r1,"norm_quantity"]=0
    
            for i in df.index:
                #Replace with an order with more priority
                for c in df.columns: #c is the strategy
                    if c!="category_id" and not np.isnan(df.loc[i,c]):
                        p=self.priority_st_lookup[self.priority_st_lookup["name"]==c]["priority"].values[0] #normally only one
                        p_id=self.priority_st_lookup[self.priority_st_lookup["name"]==c]["priority"].index[0]
    
                        if p<self.target_ss.loc[i].priority and not np.isnan(float(df.loc[i,c])):
                            self.target_ss.loc[i,"strategy_id"]=p_id
                            self.target_ss.loc[i,"priority"]=p
                            self.target_ss.loc[i,"norm_quantity"]=df.loc[i,c]
                            
                            if self.present_ss.loc[i,"quantity"]==0 or np.isnan(float(self.present_ss.loc[i,"quantity"])): #float required for decimals
                                present_norm_quantity=0
                            else:
                                present_norm_quantity=self.present_ss.loc[i,"quantity"]/abs(self.present_ss.loc[i,"quantity"])
                            self.target_ss.loc[i,"norm_delta_quantity"]=float(self.target_ss.loc[i,"norm_quantity"])-present_norm_quantity
    
                if it_is_index:
                    #If index, we have to move the order from the index to the etf
                    etf=None
                    #Looking for the index of the corresponding etf
                    if self.target_ss.loc[i,"norm_quantity"]>0:
                        etf=self.present_ss.loc[i,"etf_long_id"]
                    elif self.target_ss.loc[i,"norm_quantity"]<0:
                        etf=self.present_ss.loc[i,"etf_short_id"]
    
                    #Copying the index self.target_ss to the etf self.target_ss
                    if etf is not None:
                        self.target_ss.loc[etf,"norm_quantity"]=self.target_ss.loc[i,"norm_quantity"]
                        self.target_ss.loc[etf,"strategy_id"]=self.target_ss.loc[i,"strategy_id"]
                        self.target_ss.loc[etf,"priority"]=self.target_ss.loc[i,"priority"]
                        
                        if self.present_ss.loc[etf,"quantity"]==0 or np.isnan(float(self.present_ss.loc[etf,"quantity"])): #float required for decimals
                            present_norm_quantity=0
                        else:
                            present_norm_quantity=self.present_ss.loc[etf,"quantity"]/abs(self.present_ss.loc[etf,"quantity"])
                        self.target_ss.loc[etf,"norm_delta_quantity"]=self.target_ss.loc[i,"norm_quantity"]-present_norm_quantity
                        self.target_ss.loc[i,"norm_quantity"]=0
                        self.target_ss.loc[i,"norm_delta_quantity"]=0
        except Exception as msg:
            import sys
            _, _, exc_tb = sys.exc_info()
            print("line " + str(exc_tb.tb_lineno))
            print(msg)    
            
    def determine_target(self):
        #start with index
        self.determine_target_sub(self.target_ss_by_st[self.target_ss_by_st["category_id"]=="IND"],True) #move order from index to etf
        self.determine_target_sub(self.target_ss_by_st[self.target_ss_by_st["category_id"]!="IND"],False)
        
    def display_target_ss_by_st(self,it_is_index:bool=False):
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)

        if it_is_index:
            df=self.target_ss_by_st[self.target_ss_by_st["category_id"]=="IND"]
        else:
            df=self.target_ss_by_st[self.target_ss_by_st["category_id"]!="IND"]
            
        s=""
        for index, row in df.iterrows():
            if not np.isnan(list(row.values[1:])).all():
                s+=str(index) + "\n"
                line1=""
                line2=""
        
                for col in df.columns:
                    if type(row[col])!=str and not np.isnan(row[col]):
                        line1+=col+" "
                        line2+=str(row[col])+" "
                        max_len=max(len(col),len(str(row[col])))
                        
                        #align
                        for i in range(max_len-len(col)):
                            line1+=" "
                        for i in range(max_len-len(str(row[col]))):
                            line2+=" "                            
                s+=line1+"\n"+line2+"\r\n\n"
        return s

    def perform_orders(
            self,
            testing: bool=False
            ):
        """
        Perform orders to reconciliate the state
        Sell orders are performed first to get cash
        
        Arguments
        ----------
        testing: set to True to perform unittest on the function
        """
        try:
            if testing==False:
                testing=self.testing
            
            if "norm_delta_quantity" in self.target_ss: #otherwise there is not order to perform
                sell_df=self.target_ss[self.target_ss["norm_delta_quantity"]<0]
        
                for symbol, row in sell_df.iterrows():
                    st=Strategy.objects.get(id=row["strategy_id"])
                    
                    op= OrderPerformer(
                        symbol,
                        row["strategy_id"],
                        row["norm_quantity"]*st.target_order_size,
                        testing=testing
                        )
                    out=op.sell_order()
                    if out:
                        self.report.handle_listOfActions(op.action, op.entry, _settings["USED_API"]["orders"], False, st.name, reverse=op.reverse)
        
                buy_df=self.target_ss[self.target_ss["norm_delta_quantity"]>0].copy()
                buy_df.sort_values(by=["priority"],inplace=True)
        
                #will stop when not enough cash
                for symbol, row in buy_df.iterrows():
                    st=Strategy.objects.get(id=row["strategy_id"])
                    op= OrderPerformer(
                        symbol,
                        row["strategy_id"],
                        row["norm_quantity"]*st.target_order_size,
                        testing=testing
                        )
                    out=op.buy_order()
                    if out:
                        self.report.handle_listOfActions(op.action, op.entry, _settings["USED_API"]["orders"], True, st.name, reverse=op.reverse)
        except Exception as msg:
            import sys
            _, _, exc_tb = sys.exc_info()
            print("line " + str(exc_tb.tb_lineno))
            print(msg)

    def resolve(self):
        self.determine_target()
        self.perform_orders()
        
    def add_target_quantity(
            self, 
            symbol: str, 
            strategy: str, 
            target_order: numbers.Number):
        """
        Each strategy will use this function to modify the desired state
        
        Arguments
        ----------
            symbol: YF ticker of the stock to be modified
            strategy: Strategy name involved in this decision
            target_order: which desired state (-1, 0, 1) is wanted        
        """
        if target_order is not None:
            if np.isnan(float(self.target_ss_by_st.loc[symbol,strategy])):
                self.target_ss_by_st.loc[symbol,strategy]=target_order
            elif ((target_order==self.target_ss_by_st.loc[symbol,strategy]) or
                  (target_order>0 and self.target_ss_by_st.loc[symbol,strategy]>0) or
                  (target_order<0 and self.target_ss_by_st.loc[symbol,strategy]<0)):
                pass
            else:
                txt="Contradictory orders for symbol: "+symbol + " for the strategy: "+strategy + " then do nothing!"
                logger.info(txt)
                print(txt)
                self.target_ss_by_st.loc[symbol,strategy]=np.nan
            
    def cand_to_quantity(
            self,
            candidates: list,
            strategy: str,
            short:bool):
        """
        For strategy using candidates (retard for instance). Convert a candidate in a desired state bought and so on
        
        Arguments
        ----------
            candidates: list of stocks that this strategy wants to "buy"
            strategy: Strategy name involved in this decision
            short: direction desired for those candidates
        """
        st=Strategy.objects.get(name=strategy)
        df=self.present_ss[self.present_ss["strategy_id"]==st.id]
        sold_symbols={}

        #clean old candidates
        for s in df.index:
            if s not in candidates and self.target_ss_by_st.loc[s,strategy]!=0: #if already cleanup for direction, should not be put in sold_symbols
                self.target_ss_by_st.loc[s,strategy]=0
                sold_symbols[s]=df.loc[s,"quantity"]
        
        #add candidates
        self.cand_to_quantity_entry(candidates, strategy, short)

        return sold_symbols #for keep 
    
    def cand_to_quantity_entry(
            self,
            candidates: list,
            strategy: str,
            short:bool):
        
        '''
        Part for the entry, used alone for only_exit_substrat
        
        Arguments
        ----------
            candidates: list of stocks that this strategy wants to "buy"
            strategy: Strategy name involved in this decision
            short: direction desired for those candidates
        '''
        if len(candidates)==0:
            self.report.concat(strategy +" no candidates")     
        else:
            for s in candidates:
                self.report.concat(strategy +" candidate: "+s)    
                if short:
                    self.target_ss_by_st.loc[s,strategy]=-1
                else:
                    self.target_ss_by_st.loc[s,strategy]=1

    def order_nosubstrat(self,
                         candidates: list, 
                         exchange: str, 
                         strategy: str, 
                         short: bool,
                         **kwargs):
        """
    	Buy automatically the candidate, without any other underlying strategy
        
        From a candidates list, it will fill the target state matrix
    
    	Arguments
    	----------
    	candidates: list of YF symbols which should be bought, when using this strategy
        exchange: name of the stock exchange
        strategy: name of the strategy
        short: direction of the desired order
        
    	"""        
        if len(candidates)==0:
            self.report.concat(strategy +" no candidates")
        
        self.clean_wrong_direction(strategy, short)
        
        sold_symbols=self.cand_to_quantity(candidates, strategy, short)
        
        if kwargs.get("keep",False):
            for s, v in sold_symbols.items():
                self.add_target_quantity(s, "retard_keep", v)

    def ex_ent_to_target(self,
                         ent: bool,
                         ex: bool,
                         ent_short: bool,
                         ex_short: bool,
                         symbol: str,
                         strategy: str, 
                         ):
        """
       	Convert the vbt convention entry/exit in a target normalized quantity

       	Arguments
       	----------
       	ent: present need to enter the product, long direction
           ex: present need to exit the product, long direction
           ent_short: present need to enter the product, short direction
           ex_short: present need to exit the product, short direction
           symbol: YF symbol of the product
           strategy: name of the strategy
       	"""
        q=None
        if ent and not ex:
            q=1
        elif ent_short and not ex_short:   
            q=-1
        elif (ex and not ent) or (ex_short and not ent_short): 
            q=0                
        self.add_target_quantity(symbol, strategy, q)    
    
    def scan_removed_strat(self):
        """
        If we decide not to use a strategy, some stocks may be still owned through it,
        this function will clean the state so to say
        """
        df=self.present_ss[self.present_ss["quantity"]!=0]
        
        for s in df.index:
            st=Strategy.objects.get(id=df.loc[s,"strategy_id"])
            s_ex=Action.objects.get(symbol=s).stock_ex
            s_ex_names=[st.name for st in s_ex.strategies_in_use.all()]

            if st.name not in s_ex_names:   
                #clean
                self.target_ss_by_st.loc[s,st.name]=0

    def clean_wrong_direction(
            self, 
            strategy: str, 
            short: bool):
        """
        If the general trend change, some stocks may be still owned for the past direction,
        this function will clean the state so to say
        
        Arguments
    	----------
        strategy: strategy name following the trend, which could have experienced a reversal
        short: present trend, the other trend must be cleaned
        """
        st=Strategy.objects.get(name=strategy)
        df=self.present_ss[self.present_ss["strategy_id"]==st.id]
    
        if short:
            df_to_be_cleaned=df[df["quantity"]>0]
        else:
            df_to_be_cleaned=df[df["quantity"]<0]
        
        for s in df_to_be_cleaned.index:
            self.target_ss_by_st.loc[s,strategy]=0



        
        
