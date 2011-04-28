#
# bollinger.py
#
# A module which contains a bollinger strategy.
#
#

#python imports
import cPickle
from pylab import *
from pandas import *
import matplotlib.pyplot as plt
import datetime as dt
import os

#qstk imports
from qstkutil import DataAccess as da
import qstkutil.dateutil as du
import qstkutil.bollinger as boil

#simple versions
#stateful
def createStatefulStrat(adjclose, timestamps, lookback, highthresh, lowthresh):
	alloc=DataMatrix(index=[timestamps[0]],columns=adjclose.columns, data=[zeros(len(adjclose.columns))])
	bs=boil.calcbvals(adjclose, timestamps, adjclose.columns, lookback)
	hold=[]
 	for i in bs.index[1:]:
		for stock in range(0,len(bs.columns)):
			if(bs.xs(i)[stock]<lowthresh and len(hold)<10):
				hold.append(stock)
			elif(bs.xs(i)[stock]>highthresh):
				if stock in hold:
					hold.remove(stock)
		vals=zeros(len(adjclose.columns))
		for j in range(0,len(hold)):
			vals[hold[j]]=.1
		alloc=alloc.append(DataMatrix(index=[i],columns=adjclose.columns,data=[vals]))
	return alloc
	
#stateless
def createStatelessStrat(adjclose, timestamps, lookback, highthresh, lowthresh):
	alloc=DataMatrix(index=[timestamps[0]],columns=adjclose.columns, data=[zeros(len(adjclose.columns))])
	bs=boil.calcbvals(adjclose, timestamps, adjclose.columns, lookback)
	vals=zeros([11,len(bs.columns)])
 	for i in bs.index[1:]:
		for stock in range(0,len(bs.columns)):
			if(bs.xs(i)[stock]<lowthresh):
				vals[0:10,stock]+=1
			elif(bs.xs(i)[stock]>highthresh):
				vals[0:10,stock]-=1
		alloc=alloc.append(DataMatrix(index=[i],columns=adjclose.columns,data=[vals[0,:]]))
		for j in range(0,10):
			vals[j,:]=vals[j+1,:]
	return alloc

#creates an allocation DataMatrix based on bollinger strategy and paramaters
def create(adjclose, timestamps, lookback, spread, high, low, bet, duration):
	alloc=DataMatrix(index=[timestamps[0]],columns=adjclose.columns, data=[zeros(len(adjclose.columns))])
	bs=boil.calcbvals(adjclose, timestamps, adjclose.columns, lookback)
	hold=[]
	time=[]
 	for i in bs.index[1:]:
		for stock in range(0,len(bs.columns)):
			if(bs.xs(i)[stock]<low and len(hold)<spread):
				hold.append(stock)
				time.append(duration)
			elif(bs.xs(i)[stock]>high):
				if stock in hold:
					del time[hold.index(stock)]
					hold.remove(stock)
		for j in range(0,len(time)):
			time[j]-=1
			if(time[j]<=0):
				del hold[j]
				del time[j]
		
		vals=zeros(len(adjclose.columns))
		for j in range(0,len(hold)):
			vals[hold[j]]=bet
		alloc=alloc.append(DataMatrix(index=[i],columns=adjclose.columns,data=[vals]))
	return alloc

if __name__ == "__main__":
	#Usage: python bollinger.py '1-1-2004' '1-1-2009' 'alloc.pkl'
	print "Running Bollinger strategy starting "+sys.argv[1]+" and ending "+sys.argv[2]+"."
	
	#Run S&P500 for thresholds 1 and -1 in simple version for lookback of 10 days
	symbols = list(np.loadtxt(os.environ['QS']+'/quicksim/strategies/S&P500.csv',dtype='str',delimiter=',',comments='#',skiprows=0))
	
	t=map(int,sys.argv[1].split('-'))
	startday = dt.datetime(t[2],t[0],t[1])
	t=map(int,sys.argv[2].split('-'))
	endday = dt.datetime(t[2],t[0],t[1])
	
	timeofday=dt.timedelta(hours=16)
	timestamps=du.getNYSEdays(startday,endday,timeofday)
	
	
	dataobj=da.DataAccess(da.DataSource.NORGATE)
	intersectsyms=list(set(dataobj.get_all_symbols())&set(symbols))
	badsyms=[]
	if size(intersectsyms)<size(symbols):
		badsyms=list(set(symbols)-set(intersectsyms))
		print "bad symms:"
		print badsyms
	for i in badsyms:
		index=symbols.index(i)
		symbols.pop(index)
	historic = dataobj.get_data(timestamps,symbols,"close")
	
	alloc=createStatefulStrat(historic,timestamps,10,1,-1)
	
	output=open(sys.argv[3],"wb")
	cPickle.dump(alloc,output)
	output.close()
