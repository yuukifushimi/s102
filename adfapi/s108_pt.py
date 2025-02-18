### Quantiacs Mean Reversion Trading System Example
# import necessary Packages below:
import talib as ta
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.tsa.stattools as ts
import sys
from numpy import zeros, ones, flipud, log
from numpy.linalg import inv, eig, cholesky as chol
import seitoolz.portfolio as portfolio
import logging
from statsmodels.regression.linear_model import OLS

##### Do not change this function definition ####
portfolioData=dict()
pairSeries=dict()
tsPairratio=dict()
tsZscore=dict()
tsDates=dict()
indSmaZscore=dict()
intDatapoints=1522
sentEntryOrder = dict()
sentExitOrder = dict()
crossAbove=dict()
crossBelow=dict()
intSMALength = 30
instPair1Factor=1
instPair2Factor=1
dblQty=1
dblQty2=1

dblUpperThreshold = 1;
dblLowerThreshold = -1;
dblRiskPer = 0.05;
dblTargetPer = 0.05;
dblStartStop = 0.06;
dblPlaceStop = 0.14;
dblBBUOrder = 2;
dblBBLOrder = 2;

def procBar(bar1, bar2, pos, trade, displayPL=False):
    global portfolioData
    global pairSeries
    global tsPairratio
    global tsZscore
    global tsDates
    global indSmaZscore
    global intDatapoints
    global sentEntryOrder 
    global sentExitOrder 
    global intSMALength 
    global dblUpperThreshold 
    global dblLowerThreshold 
    global instPair1Factor
    global instPair2Factor
    global dblQty
    global dblQty2 
    global crossAbove
    global crossBelow
    
    
    if bar1['Close'] > 0 and bar2['Close'] > 0:
        xd = bar1['Close'] * instPair1Factor
        yd = bar2['Close'] * instPair2Factor
        sym1=bar1['Symbol']
        sym2=bar2['Symbol']
        logging.info("s106:procBar:" + sym1 + "," + sym2)
        if not pairSeries.has_key(sym1):
            pairSeries[sym1]=list()
        if not pairSeries.has_key(sym2):
            pairSeries[sym2]=list()
        if not tsPairratio.has_key(sym1+sym2):
            tsPairratio[sym1+sym2]=list()
        if not tsPairratio.has_key(sym2+sym1):
            tsPairratio[sym2+sym1]=list()
        if not tsZscore.has_key(sym1+sym2):
            tsZscore[sym1+sym2]=list()
        if not tsZscore.has_key(sym2+sym1):
            tsZscore[sym2+sym1]=list()
        if not tsDates.has_key(sym1):
            tsDates[sym1]=list()
        if not tsDates.has_key(sym2):
            tsDates[sym2]=list()
        if not tsDates.has_key(sym1+sym2):
            tsDates[sym1+sym2]=list()
        if not tsDates.has_key(sym2+sym1):
            tsDates[sym2+sym1]=list()
        if not crossAbove.has_key(sym1+sym2):
            crossAbove[sym1+sym2]=False
        if not crossBelow.has_key(sym1+sym2):
            crossBelow[sym1+sym2]=False
        if not sentEntryOrder.has_key(sym1+sym2):
            sentEntryOrder[sym1+sym2]=False
        if not sentExitOrder.has_key(sym1+sym2):
            sentExitOrder[sym1+sym2]=False
        
        if bar1['Date'] not in tsDates[sym1]:
            pairSeries[sym1].append(bar1['Close'])
            tsDates[sym1].append(bar1['Date'])
        
        if bar2['Date'] not in tsDates[sym2]:
            pairSeries[sym2].append(bar2['Close'])
            tsDates[sym2].append(bar2['Date'])

        dblRatioData = bar1['Close'] / bar2['Close'];
        tsPairratio[sym1+sym2].append( dblRatioData );
        
        dblRatioData2 = bar2['Close'] / bar1['Close'];
        tsPairratio[sym2+sym1].append( dblRatioData2 );

        if len(tsPairratio[sym1+sym2])< intDatapoints or len(tsPairratio[sym2+sym1]) < intDatapoints:
            return []

        iStart = len(tsPairratio[sym1+sym2]) - intDatapoints;
        iEnd = len(tsPairratio[sym1+sym2]) - 1;
        dblAverage = np.mean(tsPairratio[sym1+sym2][iStart:iEnd]);
        dblRatioStdDev = np.std(tsPairratio[sym1+sym2][iStart:iEnd]);
        dblResidualsData = (dblRatioData - dblAverage);
        dblZscoreData = (dblRatioData - dblAverage) / dblRatioStdDev;
        tsZscore[sym1+sym2].append(dblZscoreData)
        tsDates[sym1+sym2].append(bar1['Date'])
        
        iStart2 = len(tsPairratio[sym2+sym1]) - intDatapoints;
        iEnd2 = len(tsPairratio[sym2+sym1]) - 1;
        dblAverage2 = np.mean(tsPairratio[sym2+sym1][iStart2:iEnd2]);
        dblRatioStdDev2 = np.std(tsPairratio[sym2+sym1][iStart2:iEnd2]);
        dblResidualsData2 = (dblRatioData2 - dblAverage2);
        dblZscoreData2 = (dblRatioData2 - dblAverage2) / dblRatioStdDev2;
        tsZscore[sym2+sym1].append(dblZscoreData2)
        tsDates[sym2+sym1].append(bar2['Date'])
         
        signals=pd.DataFrame()
        signals['Date']=tsDates[sym1+sym2]
        signals['tsZscore']=tsZscore[sym1+sym2]
        signals['tsZscore2']=tsZscore[sym2+sym1]
        #signals['indSmaZscore']=pd.rolling_mean(signals['tsZscore'], intSMALength, min_periods=1)
        #signals['indSmaZscore2']=pd.rolling_mean(signals['tsZscore2'], intSMALength, min_periods=1)    
        
        (signals['indBbu'], signals['indBbm'], signals['indBbl']) = ta.BBANDS(
            np.array(signals['tsZscore']), 
            timeperiod=intSMALength,
            # number of non-biased standard deviations from the mean
            nbdevup=dblBBUOrder,
            nbdevdn=dblBBLOrder,
            # Moving average type: simple moving average here
            matype=0)
            
        (signals['indBbu2'], signals['indBbm2'], signals['indBbl2']) = ta.BBANDS(
            np.array(signals['tsZscore2']), 
            timeperiod=intSMALength,
            # number of non-biased standard deviations from the mean
            nbdevup=dblBBUOrder,
            nbdevdn=dblBBLOrder,
            # Moving average type: simple moving average here
            matype=0)
        
        
        signals['indSmaZscore']=ta.EMA(np.array(signals['tsZscore']), intSMALength)      
        signals['indSmaZscore2']=ta.EMA(np.array(signals['tsZscore2']), intSMALength)        
        signals=signals.set_index('Date')
        
        #				tsPricePair1.Add(bar1['Date']Time, bar1['Close']);
        #			tsPricePair2.Add(bar2['Date']Time, bar2['Close']);
        #				double dblBeta = tsPricePair1.GetCovariance( tsPricePair2 ) /tsPricePair1.GetVariance(Bars.Ago(intDatapoints).DateTime,	Bars.Ago(1).DateTime);

        #print 'ZScore:' + str(dblZscoreData) + ' Upper: ' +  str(dblUpperThreshold) +  + ' Lower: ' +  str(dblLowerThreshold)
       
        if len(signals['tsZscore']) < 5 or len(signals['indSmaZscore']) < 5 or len(signals['indSmaZscore2']) < 5:
            return [];

        #updateCointData();

        if trade:
                #print strOrderComment
                (crossBelow[sym1+sym2], crossAbove[sym1+sym2])=crossCheck(signals, sym1+sym2, 'tsZscore', 'indSmaZscore')                
                (z1CBBbu, z1CABbu)=crossCheck(signals, 'bb'+sym1+sym2, 'tsZscore', 'indBbu')
                (z1CBBbl, z1CABbl)=crossCheck(signals, 'bb2'+sym1+sym2, 'tsZscore2','indBbl')
                
                #print ' crossAbove: ' + str(crossAbove) + ' crossBelow: ' + str(crossBelow)
                #crossBelow = signals['tsZscore'].iloc[-1] >= signals['indSmaZscore'].iloc[-1] and crossBelow.any()
                #crossAbove = signals['tsZscore'].iloc[-1] <= signals['indSmaZscore'].iloc[-1] and crossAbove.any()
                #print ' crossAbove: ' + str(crossAbove) + ' crossBelow: ' + str(crossBelow)
                if not sentEntryOrder[sym1+sym2] and not pos.has_key(bar1['Symbol']) and not pos.has_key(bar2['Symbol']):

                    #dblQty = Math.Ceiling(1/dblBeta);
                    #dblQty2 = Math.Ceiling(dblBeta);
    
                    # Create the set of short and long simple moving averages over the 
                    # respective periods
                    
                   
                    # Create a 'signal' (invested or not invested) when the short moving average crosses the long
                    # moving average, but only for the period greater than the shortest moving average window
    
                    
                
                    if dblZscoreData >= dblUpperThreshold and \
                        z1CABbu:
                        #crossAbove[sym1+sym2] == 1 and \
                        
                        
                        #Sell(instPair1, dblQty, strOrderComment);
                        #Buy(instPair2, dblQty2, strOrderComment2);
            
                        #if (myParam.hasOpt)
                        #{
                        #    Sell(myParam.getSym1OptInst(PutCall.Put, bar1['Close'], this), myParam.sym1OptQty, strOrderComment);
                        #    Sell(myParam.getSym2OptInst(PutCall.Call, bar2['Close'], this), myParam.sym2OptQty, strOrderComment2);
                        #}
                        sentEntryOrder[sym1+sym2] = True
                        sentExitOrder[sym1+sym2] = False
                        strOrderComment = '{"Entry": 1, "Exit": 0, "symPair": "' + sym1+sym2 + '", "zScore": ' + str(round(dblZscoreData, 2)) + ', "zSMA": ' + str(round(signals.iloc[-1]['indSmaZscore'], 2)) + '}';
                        strOrderComment2 = '{"Entry": 1, "Exit": 0, "symPair": "' + sym1+sym2 + '", "zScore": '+ str(round(dblZscoreData2, 2)) + ', "zSMA": ' + str(round(signals.iloc[-1]['indSmaZscore2'], 2))+ '}';
                        portfolioData[sym1]={ 'symbol': bar1['Symbol'], 'qty':-abs(dblQty), 'date':bar1['Date'], 'price':bar1['Close'] }
                        portfolioData[sym2]={ 'symbol': bar2['Symbol'], 'qty':abs(dblQty2), 'date':bar2['Date'], 'price':bar2['Close'] }
                        return ([bar1['Symbol'], -abs(dblQty), strOrderComment], 
                                [bar2['Symbol'], abs(dblQty2), strOrderComment2])
                    elif dblZscoreData <= -1 * dblUpperThreshold and \
                        z1CABbu:
                        #crossBelow[sym1+sym2] and \
                        
                        
                        #Buy(instPair1, dblQty, strOrderComment);
                        #Sell(instPair2, dblQty2, strOrderComment2);
                        #if (myParam.hasOpt)
                        #{
                        #    Sell(myParam.getSym1OptInst(PutCall.Call, bar1['Close'], this), myParam.sym1OptQty, strOrderComment);
                        #    Sell(myParam.getSym2OptInst(PutCall.Put, bar2['Close'], this), myParam.sym2OptQty, strOrderComment2);
                        #}
                        sentEntryOrder[sym1+sym2] = True
                        sentExitOrder[sym1+sym2] = False
                        strOrderComment = '{"Entry": 1, "Exit": 0, "symPair": "' + sym1+sym2 + '", "zScore": ' + str(round(dblZscoreData, 2)) + ', "zSMA": ' + str(round(signals.iloc[-1]['indSmaZscore'], 2)) + '}';
                        strOrderComment2 = '{"Entry": 1, "Exit": 0, "symPair": "' + sym1+sym2 + '", "zScore": '+ str(round(dblZscoreData2, 2)) + ', "zSMA": ' + str(round(signals.iloc[-1]['indSmaZscore2'], 2))+ '}';
                        portfolioData[sym1]={ 'symbol': bar1['Symbol'], 'qty':abs(dblQty), 'date':bar1['Date'], 'price':bar1['Close'] }
                        portfolioData[sym2]={ 'symbol': bar2['Symbol'], 'qty':-abs(dblQty2), 'date':bar2['Date'], 'price':bar2['Close'] }
                
                        return ([bar1['Symbol'], abs(dblQty), strOrderComment], 
                                [bar2['Symbol'], -abs(dblQty2), strOrderComment2])
    
                elif not sentExitOrder[sym1+sym2] and pos.has_key(bar1['Symbol']) and pos.has_key(bar2['Symbol']):
                    pl=0
                    pl_amt=0
                    try:
                        qty1=1
                        qty2=1
                        #qty1=portfolioData[sym1]['qty']
                        #qty2=portfolioData[sym2]['qty']
                        (pl1, value1)=calc_pl(portfolioData[sym1]['price'], bar1['Close'], qty1)
                        (pl2, value2)=calc_pl(portfolioData[sym2]['price'], bar2['Close'], qty2)
                        plp1=float(pl1)/ bar1['Close'] # / abs( float(portfolioData[sym1]['qty']))
                        plp2=float(pl2)/ bar2['Close'] # / abs( float(portfolioData[sym2]['qty']))
                        pl_amt=float(pl1) + float(pl2)
                        pl=plp1 + plp2
                        #print pl
                    except Exception as e:
                        print (e)
                        
                    if displayPL:
                        try:
                            print ("PL: ", pl1, ' ', plp1, '% sym1 entry', portfolioData[sym1]['price'], 'sym1 now', bar1['Close'])
                            print ("PL: ", pl2, ' ', plp2, '% sym2 entry', portfolioData[sym2]['price'], 'sym2 now', bar2['Close'])
                            print ("PL: ", pl,  'qty1', portfolioData[sym1]['qty'], 'qty2', portfolioData[sym2]['qty'])
                        except Exception as e:
                            print (e)                         
                    
                    if pos[bar1['Symbol']] < 0 and pos[bar2['Symbol']] > 0 and \
                        (pl > 0.006 or (dblZscoreData <= dblLowerThreshold and crossAbove[sym1+sym2]==1 and z1CBBbl and pl > 0.004)):
                        #pl_amt > 0 and \
                        
                        sentEntryOrder[sym1+sym2] = False;
                        sentExitOrder[sym1+sym2] = True;
                        strOrderComment = '{"Entry": 0, "Exit": 1, "symPair": "' + sym1+sym2 + '", "zScore": ' + str(round(dblZscoreData, 2)) + ', "zSMA": ' + str(round(signals.iloc[-1]['indSmaZscore'], 2)) + '}';
                        strOrderComment2 = '{"Entry": 0, "Exit": 1, "symPair": "' + sym1+sym2 + '", "zScore": '+ str(round(dblZscoreData2, 2)) + ', "zSMA": ' + str(round(signals.iloc[-1]['indSmaZscore2'], 2))+ '}';

                        portfolioData[sym1]={ 'symbol': bar1['Symbol'], 'qty':abs(dblQty), 'date':bar1['Date'], 'price':bar1['Close'] }
                        portfolioData[sym2]={ 'symbol': bar2['Symbol'], 'qty':-abs(dblQty2), 'date':bar2['Date'], 'price':bar2['Close'] }
                
                        return ([bar1['Symbol'], abs(dblQty), strOrderComment], 
                                [bar2['Symbol'], -abs(dblQty2), strOrderComment2])
    
                    elif pos[bar1['Symbol']] > 0 and pos[bar2['Symbol']] < 0 and \
                        (pl > 0.006 or (dblZscoreData >= -1 * dblLowerThreshold and crossBelow[sym1+sym2] == 1 and z1CBBbl and pl > 0.004)):
                        #pl_amt > 0 and \
                        
                        sentEntryOrder[sym1+sym2] = False;
                        sentExitOrder[sym1+sym2] = True;
                        strOrderComment = '{"Entry": 0, "Exit": 1, "symPair": "' + sym1+sym2 + '", "zScore": ' + str(round(dblZscoreData, 2)) + ', "zSMA": ' + str(round(signals.iloc[-1]['indSmaZscore'], 2)) + '}';
                        strOrderComment2 = '{"Entry": 0, "Exit": 1, "symPair": "' + sym1+sym2 + '", "zScore": '+ str(round(dblZscoreData2, 2)) + ', "zSMA": ' + str(round(signals.iloc[-1]['indSmaZscore2'], 2))+ '}';

                        portfolioData[sym1]={ 'symbol': bar1['Symbol'], 'qty':-abs(dblQty), 'date':bar1['Date'], 'price':bar1['Close'] }
                        portfolioData[sym2]={ 'symbol': bar2['Symbol'], 'qty':abs(dblQty2), 'date':bar2['Date'], 'price':bar2['Close'] }
                
                        return ([bar1['Symbol'], -abs(dblQty), strOrderComment], 
                                [bar2['Symbol'], abs(dblQty2), strOrderComment2])
               
def getBar(price, symbol, date):
    bar=dict()
    bar['Close']=price
    bar['Symbol']=symbol
    bar['Date']=date
    return bar

def updateEntry(symPair, entryOrder, exitOrder):
    sentEntryOrder[symPair] = entryOrder
    sentExitOrder[symPair] = exitOrder

def calc_pl(openAt, closeAt, qty):
    mult=1
    if qty > 0:
        side='long'
    elif qty < 0:
        side='short'
        
    if side == 'short':
        pl=(openAt - closeAt)*abs(qty)*abs(mult)
        value=closeAt*abs(qty)*abs(mult)
        #    print 'Calc: PL: ' + side + ' ' + str(pl) + ' Value: ' + str(value) + ' Open: ' + str(openAt) + ' Close: ' + str(closeAt) + ' Qty' + str(qty)
        return (pl, value)
        
    if side == 'long':
        pl=(closeAt - openAt)*abs(qty)*abs(mult)
        value=closeAt*abs(qty)*abs(mult)
        #    print 'Calc: PL: ' + side + ' ' + str(pl) + ' Value: ' + str(value) + ' Open: ' + str(openAt) + ' Close: ' + str(closeAt) + ' Qty' + str(qty)
        return (pl,value)

def updatePortfolio(sym, price, qty):
    global portfolioData
    try:
        if portfolioData.has_key(sym):
            portfolioData[sym]['price']=price
            portfolioData[sym]['qty']=qty
            
    except Exception as e:
        print (e)

def crossCheck(signals, symPair, tsz, check2):
    global crossBelow
    global crossAbove
    if not crossBelow.has_key(symPair):
        crossBelow[symPair]=False
    if not crossAbove.has_key(symPair):
        crossAbove[symPair]=False
        
    if signals.iloc[-2][tsz] > signals.iloc[-2][check2]  \
            and                                                         \
       signals.iloc[-1][tsz] <= signals.iloc[-1][check2]:
            crossBelow[symPair]=False
            crossAbove[symPair]=True
            
    if signals.iloc[-2][tsz] < signals.iloc[-2][check2] \
           and                                                         \
       signals.iloc[-1][tsz] >= signals.iloc[-1][check2]:
             crossBelow[symPair]=True
             crossAbove[symPair]=False
    
    return (crossBelow[symPair], crossAbove[symPair])
#def updateEntry(systemname, broker, sym1, sym2, currency, date, isLive):
#    data=portfolio.get_portfolio(systemname, broker, date, isLive)
#    qty1=portfolio.get_pos(data, broker, sym1, currency, date)
#    qty2=portfolio.get_pos(data, broker, sym1, currency, date)
    
