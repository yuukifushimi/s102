import numpy as np
import pandas as pd
import time
from os import listdir
from os.path import isfile, join
from swigibpy import EPosixClientSocket, ExecutionFilter, CommissionReport, Execution, Contract
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 08 20:10:29 2016
3 mins - 2150 dp per request
10 mins - 630 datapoints per request
30 mins - 1025 datapoints per request
1 hour - 500 datapoint per request
@author: Hidemi
"""
import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import datetime
import sys
import random
import copy
import pytz
from pytz import timezone
from datetime import datetime as dt
from tzlocal import get_localzone
from sklearn.feature_selection import SelectKBest, chi2, f_regression, RFECV
import os
from dateutil.parser import parse
import logging
import re
from pandasticsearch import Select
from stockstats import StockDataFrame as idf
import pandas as pd
import pytz
import    os
sys.path.append("./")
sys.path.append("../")
from coin import *
import    sys
import os
idx_name='forecast'
from    main.elasticmodels    import    *

rtbar={}
rtdict={}
rthist={}
rtfile={}
rtreqid={}
lastDate={}
tickerId=1

def get_bidask_list():
    dataPath='./data/bidask/'
    files = [ f for f in os.listdir(dataPath) if os.path.isfile(os.path.join(dataPath,f)) ]
    baList=list()
    for file in files:
            inst=file.rsplit('.',1)[0]
            baList.append(inst)
            #print 'Found BidAsk: ' + inst
    return baList

def get_btc_list():
    dataPath='./data/from_IB/'
    files = [ f for f in os.listdir(dataPath) if os.path.isfile(os.path.join(dataPath,f)) ]
    btcList=list()
    for file in files:
            if re.search(r'BTCUSD', file):
                inst=file.rsplit('.',1)[0]
                btcList.append(inst)
                #print 'Found ' + inst
    return btcList

def get_btc_exch_list():
    dataPath='./data/from_IB/'
    files = [ f for f in os.listdir(dataPath) if os.path.isfile(os.path.join(dataPath,f)) ]
    btcList=list()
    for file in files:
            if re.search(r'BTCUSD', file):
                inst=file.rsplit('.',1)[0]
                btcList.append(inst)
                #print 'Found ' + inst
    return btcList
    
    
def get_currencies():
    return get_symbols()


def get_symbols():
    symList=dict()
    
    systemdata=pd.read_csv('./data/systems/system.csv')
    systemdata=systemdata.reset_index()
    for i in systemdata.index:
        system=systemdata.ix[i]
        symbol=system['ibsym']
        if system['ibtype'] == 'CASH':
          symbol=system['ibsym']+system['ibcur']
        if system['ibtype'] != 'BITCOIN':
          symList[symbol]=[symbol, system['ibexch'], system['ibtype'], system['ibcur']]
          
       
    return symList.keys()

def get_contracts():
    symList=dict()
    
    systemdata=pd.read_csv('./data/systems/system.csv')
    print systemdata.columns
    systemdata=systemdata.reset_index()
    for i in systemdata.index:
        #print 'Read: ',i
        system=systemdata.ix[i]
        #print system
        contract = Contract()
        symbol=system['ibsym']
        if system['ibtype'] == 'CASH':
          symbol=system['ibsym']+system['ibcur']
        if system['ibtype'] != 'BITCOIN':
                contract.symbol = system['ibsym']
                contract.secType = system['ibtype']
                contract.exchange = system['ibexch']
                contract.currency = system['ibcur']
                if system['ibtype'] == 'FUT':
                        contract.localSymbol= system['iblocalsym']
                symList[symbol]=contract
          
    return symList.values()  


def get_cash_contracts():
    symList=dict()
    
    systemdata=pd.read_csv('./data/systems/system.csv')
    print systemdata.columns
    systemdata=systemdata.reset_index()
    for i in systemdata.index:
        #print 'Read: ',i
        system=systemdata.ix[i]
        #print system
        contract = Contract()
        symbol=system['ibsym']
        if system['ibtype'] == 'CASH':
            symbol=system['ibsym']+system['ibcur']
            if system['ibtype'] != 'BITCOIN':
                    contract.symbol = system['ibsym']
                    contract.secType = system['ibtype']
                    contract.exchange = system['ibexch']
                    contract.currency = system['ibcur']
                    if system['ibtype'] == 'FUT':
                            contract.localSymbol= system['iblocalsym']
                    symList[symbol]=contract
              
    return symList.values()  


def create_bars(currencyPairs, interval='30m'):
    try:
        global tickerId
        
        dataPath='./data/from_IB/'
        for pair in currencyPairs:
            filename=dataPath+interval+'_'+pair+'.csv'
            minFile=dataPath+'1 min'+'_'+pair+'.csv'
            symbol = pair
            if os.path.isfile(minFile):
                data=pd.read_csv(minFile)
                for i in data.index:
                    quote=data.ix[i]
                    compress_min_bar(symbol, quote, filename, interval)
    except Exception as e:
        logging.error("create_bars", exc_info=True)

def cache_bar_csv(pair, filename, interval):
    global rtbar
    global rtdict
    global rtfile
    global rtreqid
    global tickerId
    if not rtreqid.has_key(pair):
            tickerId=tickerId+1
            reqId=tickerId
            rtdict[reqId]=pair
            rtfile[reqId]=filename
            rtreqid[pair]=reqId
            
            print 'Caching: ' + pair
    else:
            reqId=rtreqid[pair]
    if not rtbar.has_key(reqId):
        data=pd.DataFrame({}, columns=['Date','Open','High','Low','Close','Volume']).set_index('Date')
            
        if os.path.isfile(filename):
            procdata=pd.read_csv(filename)
            for i in procdata.index:
                rec=procdata.ix[i].copy()
                if is_bar_date(rec['Date'], interval):
                    data.loc[rec['Date']]=[rec['Open'],rec['High'],rec['Low'],rec['Close'],rec['Volume']]
            data=data.sort_index()
            
        rtbar[reqId]=data
    return rtbar[reqId]

def is_bar_date(dateStr, interval):
        if interval == '30m':
            if re.search(r'\d\d\d\d\d\d  \d\d:[03]0:00', dateStr):
                return True
        elif interval == '10m':
            if re.search(r'\d\d\d\d\d\d  \d\d:[012345]0:00', dateStr):
                return True
        elif interval == '1h':
            if re.search(r'\d\d\d\d\d\d  \d\d:00:00', dateStr):
                return True
        else:
            return True
        return False
        
def proc_history(contract, histdata, interval='30m'):
    try:
        global rtbar
        global rtdict
        global rtfile
        global rtreqid
        global tickerId
        
        dataPath='./data/from_IB/'
        
        symbol= contract.symbol
        currency=contract.currency
        pair=symbol
        if contract.secType == 'CASH':
            pair=symbol+currency
        filename=dataPath+interval+'_'+pair+'.csv'
        data=cache_bar_csv(pair, filename, interval)
        
        if not histdata == None and len(histdata.index) > 1:
            reqId=rtreqid[pair]
            data = data.reset_index().set_index('Date')
            histdata=histdata.reset_index().set_index('Date')
            data = data.combine_first(histdata)
            data=data.sort_index()
            rtbar[reqId]=data
            data.to_csv(filename)
            
        return data
            
    except Exception as e:
        logging.error("get_hist_bars", exc_info=True)

def update_bars(currencyPairs, interval='30m'):
    global tickerId
    global lastDate
    dataPath='./data/from_IB/'
    while 1:
        try:
            for pair in currencyPairs:
                filename=dataPath+interval+'_'+pair+'.csv'
                minFile='./data/bars/'+pair+'.csv'
                symbol = pair
                if os.path.isfile(minFile):
                    data=pd.read_csv(minFile)
                     
                    eastern=timezone('US/Eastern')
                    
                    date=data.iloc[-1]['Date']
                    date=parse(date).replace(tzinfo=eastern)
                    timestamp = time.mktime(date.timetuple())
                    
                    if not lastDate.has_key(symbol):
                        lastDate[symbol]=timestamp
                        dataFile='./data/from_IB/1 min_'+pair+'.csv'
                        if os.path.isfile(dataFile):
                            data=pd.read_csv(dataFile)
                            regentime=60
                            if interval == '30m':
                                regentime=60*6
                            elif interval == '1h':
                                regentime = 60 * 6
                            elif interval == '10m':
                                regentime == 60 * 6
                            
                            quote=data
                            if quote.shape[0] > regentime:
                                quote=quote.tail(regentime)
                            for i in quote.index:
                                data=quote.ix[i]
                                compress_min_bar(symbol, data, filename, interval)
                                       
                    if lastDate[symbol] < timestamp:
                        lastDate[symbol]=timestamp
                        quote=data.iloc[-1]
                        compress_min_bar(symbol, quote, filename, interval) 
                        
            time.sleep(20)
        except Exception as e:
            logging.error("update_bars", exc_info=True)

def compress_min_bar(pair, histData, filename, interval='30m'):
    try:
        global pricevalue
        global finished
        global rtbar
        global rtdict
        global rtfile
        global rtreqid
        global tickerId
        
        data=cache_bar_csv(pair, filename,interval)
        reqId=rtreqid[pair]
        
        date=histData['Date']
        open=histData['Open']
        high=histData['High']
        low=histData['Low']
        close=histData['Close']
        volume=histData['Volume']
        
        eastern=timezone('US/Eastern')
        #timestamp
        date=parse(date).replace(tzinfo=eastern)
        timestamp = time.mktime(date.timetuple())
        if interval == '30m':
            mins=int(datetime.datetime.fromtimestamp(
                        int(timestamp)
                    ).strftime('%M'))
            if mins < 30:
                #time
                date=datetime.datetime.fromtimestamp(
                            int(timestamp)
                        ).strftime('%Y%m%d  %H:00:00') 
            else:
                 date=datetime.datetime.fromtimestamp(
                            int(timestamp)
                        ).strftime('%Y%m%d  %H:30:00') 
        elif interval == '10m':
            mins=int(datetime.datetime.fromtimestamp(
                        int(timestamp)
                    ).strftime('%M'))
            if mins < 10:
                #time
                date=datetime.datetime.fromtimestamp(
                            int(timestamp)
                        ).strftime('%Y%m%d  %H:00:00') 
            elif mins < 20:
                #time
                date=datetime.datetime.fromtimestamp(
                            int(timestamp)
                        ).strftime('%Y%m%d  %H:10:00') 
            elif mins < 30:
                #time
                date=datetime.datetime.fromtimestamp(
                            int(timestamp)
                        ).strftime('%Y%m%d  %H:20:00') 
            elif mins < 40:
                #time
                date=datetime.datetime.fromtimestamp(
                            int(timestamp)
                        ).strftime('%Y%m%d  %H:30:00') 
            elif mins < 50:
                #time
                date=datetime.datetime.fromtimestamp(
                            int(timestamp)
                        ).strftime('%Y%m%d  %H:40:00') 
            else:
                 date=datetime.datetime.fromtimestamp(
                            int(timestamp)
                        ).strftime('%Y%m%d  %H:50:00') 
        elif interval == '1h':
            date=datetime.datetime.fromtimestamp(
                    int(timestamp)
                ).strftime('%Y%m%d  %H:00:00') 
        #time=time.astimezone(eastern).strftime('%Y-%m-%d %H:%M:00') 
        wap=0
        count=data.shape[0]
        if date in data.index:
               
            quote=data.loc[date].copy()
            if high > quote['High']:
                quote['High']=high
            if low < quote['Low']:
                quote['Low']=low
            quote['Close']=close
            quote['Volume']=quote['Volume'] + volume
            if quote['Volume'] < 0:
                quote['Volume'] = 0 
            data.loc[date]=quote
            #print "Update Bar: bar: sym: " + sym + " date:" + str(date) + "open: " + str(quote['Open']) + " high:"  + str(quote['High']) + ' low:' + str(quote['Low']) + ' close: ' + str(quote['Close']) + ' volume:' + str(quote['Volume']) 
                    
        else:
            if len(data.index) > 1:
                data=data.sort_index()
                quote=data.reset_index().iloc[-1]
                print "Close Bar: " + pair + " date:" + str(quote['Date']) + " open: " + str(quote['Open']) + " high:"  + str(quote['High']) + ' low:' + str(quote['Low']) + ' close: ' + str(quote['Close']) + ' volume:' + str(quote['Volume']) + ' wap:' + str(wap) 
                data.to_csv(filename)
                
                gotbar=pd.DataFrame([[quote['Date'], quote['Open'], quote['High'], quote['Low'], quote['Close'], quote['Volume'], pair]], columns=['Date','Open','High','Low','Close','Volume','Symbol']).set_index('Date')
                gotbar.to_csv('./data/bars/' + interval + '_' + pair + '.csv')
            
            print "New Bar:   " + pair + " date:" + str(date) + " open: " + str(open) + " high:"  + str(high) + ' low:' + str(low) + ' close: ' + str(close) + ' volume:' + str(volume) 
            data=data.reset_index().append(pd.DataFrame([[date, open, high, low, close, volume]], columns=['Date','Open','High','Low','Close','Volume'])).set_index('Date')
            
        rtbar[reqId]=data
    except Exception as e:
        logging.error("compress_min_bars", exc_info=True)
        
def get_last_bars(currencyPairs, ylabel, callback):
    global tickerId
    global lastDate
    while 1:
        try:
            
            SST=pd.DataFrame()
            symbols=list()
            returnData=False
            for ticker in currencyPairs:
                pair=ticker
                minFile='./data/bars/'+pair+'.csv'
                symbol = pair
                date=''
                
                if os.path.isfile(minFile):
                    dta=pd.read_csv(minFile)
                    date=dta.iloc[-1]['Date']
                    
                    eastern=timezone('US/Eastern')
                    date=parse(date).replace(tzinfo=eastern)
                    timestamp = time.mktime(date.timetuple())
                    #print 'loading',minFile,date,dta[ylabel],'\n'
                    data=pd.DataFrame()
                    data['Date']=dta['Date']
                    data[symbol]=dta[ylabel]
                    data=data.set_index('Date') 
                    
                    
                    
                    if data.shape[0] > 0:
                        if SST.shape[0] < 1:
                            SST=data
                        else:
                            SST = SST.combine_first(data).sort_index()
                            #SST=SST.join(data)
                        
                        if not lastDate.has_key(symbol):
                            returnData=True
                            lastDate[symbol]=timestamp
                            symbols.append(symbol)
                                                   
                        if lastDate[symbol] < timestamp:
                            returnData=True
                            lastDate[symbol]=timestamp
                            symbols.append(symbol)
                        #print 'Shape: ' + str(len(SST.index)) 
                        
            if returnData:
                data=SST.copy()
                data=data.reset_index() #.set_index('Date')
                data=data.dropna()
                #data=data.fillna(method='pad')
                callback(data, symbols)
            time.sleep(20)
        except Exception as e:
            logging.error("get_last_bar", exc_info=True)


def get_bar_elastic_feed(datas, ylabel, frequency):
    try:
        SST=pd.DataFrame()
        start_date=datetime.now()-relativedelta(minutes=20)
        
        for (currency, ticker, qty) in datas:
            if currency:
                currency_list=CurrencyConversion.search().filter('match',from_currency_name='USD').filter('match',to_currency_name=currency).execute()
                if currency_list and len(currency_list) > 0:
                     to_currency_conversion=float(currency_list[0].to_currency_price)
                else:
                     to_currency_conversion=1
                     currency='USD'
            else:
                currency='USD'
                to_currency_conversion=1

            company_name=ticker
            if company_name:
                #print company_name
                resource_list=Resource.search().filter('term',**{ 'company_name.raw':company_name})
                #print resource_list
                if resource_list and resource_list.count() > 0:
                    resource=resource_list[0].execute()[0]
                    company_name=resource.company_name
                    resource_id=resource.id
                    instrument_list=Instrument.search().filter('term',resource_id=resource.id).sort('id')
    
                    if instrument_list and instrument_list.count() > 0:
                        instrument=instrument_list[0].execute()[0]
                        instrument_id=instrument.id
                        sym=instrument.sym
                        print (instrument_id, sym)
                        
            data=Feed.search().filter('term',instrument_id=int(instrument_id)).filter('term',frequency=frequency).filter('range',**{'date':{'gte':start_date}}).sort('-date')
            if data.count() > 1:
    
                pandas_df = Select.from_dict(data.execute().to_dict()).to_pandas()
                pandas_df= pandas_df[['date','open','high','low','volume','close']]

                # reverse data
                pandas_df= pandas_df.sort_index(axis=1, ascending=True)
                pandas_df= pandas_df.iloc[::-1].reset_index()

                pandas_df['close'] = pandas_df['close'] /to_currency_conversion
                pandas_df['date']=[re.sub('T',' ',x) for x in pandas_df['date']]
                pandas_df['date'] = pd.to_datetime(pandas_df['date'])
                '''
                indicators = idf.retype(pandas_df)
                pandas_df['rsi']=indicators['rsi_14']
                pandas_df['kdjk']=indicators['kdjk']
                pandas_df['kdjd']=indicators['kdjd']
                pandas_df['kdjj']=indicators['kdjj']
                '''
                dta=pandas_df
                
                data=pd.DataFrame()
                
                data['Date']=pandas_df['date']
                
                data[ticker]=dta[ylabel]
                data=data.set_index('Date') 
                if len(SST.index.values) < 2:
                    SST = data
                else:
                    SST = SST.combine_first(data).sort_index()
                
        colnames=list()
        for col in SST.columns:
            if col != 'Date' and col != 0:
                colnames.append(col)
        data=SST
        data=data.reset_index()        
        data['timestamp']= data['Date']
        data = data.drop_duplicates(subset='Date', keep='last')
        data=data.dropna()
        data=data.set_index('Date')
                 
        #try:
        #    data=data.fillna(method='pad')
        #except Exception as e:
        #    print (e)
            
        print (data.index[-1],colnames, data[colnames[0]][-1], data[colnames[1]][-1])
        
        return data
        
    except Exception as e:
        logging.error("something bad happened", exc_info=True)
    return SST

def get_bar_elastic_history(datas, ylabel, frequency):
    try:
        SST=pd.DataFrame()
        start_date=datetime.now()-relativedelta(months=24)
        
        for (currency, ticker, qty) in datas:
            print (currency,ticker,qty)
            if currency:
                currency_list=CurrencyConversion.search().filter('match',from_currency_name='USD').filter('match',to_currency_name=currency).execute()
                if currency_list and len(currency_list) > 0:
                     to_currency_conversion=float(currency_list[0].to_currency_price)
                else:
                     to_currency_conversion=1
                     currency='USD'
            else:
                currency='USD'
                to_currency_conversion=1

            company_name=ticker
            if company_name:
                #print company_name
                resource_list=Resource.search().filter('term',**{ 'company_name.raw':company_name})
                #print resource_list
                if resource_list and resource_list.count() > 0:
                    resource=resource_list[0].execute()[0]
                    company_name=resource.company_name
                    resource_id=resource.id
                    instrument_list=Instrument.search().filter('term',resource_id=resource.id).sort('id')
    
                    if instrument_list and instrument_list.count() > 0:
                        instrument=instrument_list[0].execute()[0]
                        instrument_id=instrument.id
                        sym=instrument.sym
                        print (instrument_id, sym)
                 
            data=Feed.search().filter('term',instrument_id=int(instrument_id)).filter('term',frequency=frequency).filter('range',**{'date':{'gte':start_date}}).sort('date')
            data=data[:data.count()]
    
            pandas_df = Select.from_dict(data.execute().to_dict()).to_pandas()
            pandas_df= pandas_df[['date','open','high','low','volume','close']]
            pandas_df['close'] = pandas_df['close'] /to_currency_conversion
            pandas_df['date'] = [re.sub('T',' ',x) for x in pandas_df['date']]
            pandas_df['date'] = pd.to_datetime(pandas_df['date'])
            '''
            indicators = idf.retype(pandas_df)
            pandas_df['rsi']=indicators['rsi_14']
            pandas_df['kdjk']=indicators['kdjk']
            pandas_df['kdjd']=indicators['kdjd']
            pandas_df['kdjj']=indicators['kdjj']
            '''
            dta=pandas_df
            
            data=pd.DataFrame()
            
            data['Date']=pandas_df['date']
            
            data[ticker]=dta[ylabel]
            data = data.drop_duplicates(subset='Date', keep='last').set_index('Date')
            #data=data.set_index('Date') 
            if len(SST.index.values) < 2:
                SST=data
            else:
                SST = SST.combine_first(data).sort_index()
        colnames=list()
        for col in SST.columns:
            if col != 'Date' and col != 0:
                colnames.append(col)
        data=SST
        data=data.reset_index()        
        data['timestamp']= data['Date']
        data = data.drop_duplicates(subset='Date', keep='last')
        data=data.dropna()
            
        data=data.set_index('Date')
                 
        #try:
        #    data=data.fillna(method='pad')
        #except Exception as e:
        #    print (e)
            

        return data
        
    except Exception as e:
        logging.error("something bad happened", exc_info=True)
    return SST

       
def get_bar_history(datas, ylabel):
    try:
        SST=pd.DataFrame()
        
        for (filename, ticker, qty) in datas:
            dta=pd.read_csv(filename)
            #symbol=ticker[0:3]
            #currency=ticker[3:6]
            #print 'plot for ticker: ' + currency
            #if ylabel == 'Close':
            #    diviser=dta.iloc[0][ylabel]
            #    dta[ylabel]=dta[ylabel] /diviser
                
            #dta[ylabel].plot(label=ticker)   
            data=pd.DataFrame()
            
            data['Date']=pd.to_datetime(dta[dta.columns[0]])
            
            data[ticker]=dta[ylabel]
            data=data.set_index('Date') 
            if len(SST.index.values) < 2:
                SST=data
            else:
                SST = SST.combine_first(data).sort_index()
        colnames=list()
        for col in SST.columns:
            if col != 'Date' and col != 0:
                colnames.append(col)
        data=SST
        data=data.reset_index()        
        data['timestamp']= data['Date']
        
        data=data.set_index('Date')
        data=data.fillna(method='pad')
        return data
        
    except Exception as e:
        logging.error("something bad happened", exc_info=True)
    return SST
    
def feed_ohlc_from_csv(ticker):
    dataSet=pd.read_csv('./data/from_IB/' + ticker  + '.csv', index_col='Date')
    return dataSet

def bar_ohlc_from_csv(ticker):
    dataSet=pd.read_csv('./data/bars/' + ticker + '.csv', index_col='Date')
    return dataSet

def get_bar(ticker):
     return bar_ohlc_from_csv(ticker)
    
def bidask_to_csv(ticker, date, bid, ask):
    data=pd.DataFrame([[date, bid, ask]], columns=['Date','Bid','Ask'])
    data=data.set_index('Date')
    data.to_csv('./data/bidask/' + ticker + '.csv')
    return data

def get_ask(ticker):
    data=bidask_from_csv(ticker).iloc[-1]
    return data['Ask']

def get_bid(ticker):
    data=bidask_from_csv(ticker).iloc[-1]
    return data['Bid']
    
def bidask_from_csv(ticker):
    if os.path.isfile('./data/bidask/' + ticker + '.csv'):
        dataSet=pd.read_csv('./data/bidask/' + ticker + '.csv', index_col='Date')
        return dataSet
    else:
        return pd.DataFrame([['20160101 01:01:01',-1,-1]], columns=['Date','Bid','Ask']).set_index('Date')
