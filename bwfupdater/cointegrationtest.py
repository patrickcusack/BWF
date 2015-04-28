import numpy as np
import statsmodels.api as stat
import statsmodels.tsa.stattools as ts

def cointegration_test(y, x):
    result = stat.OLS(y, x).fit()
    # print result.summary()
    return ts.adfuller(result.resid)

if __name__ == '__main__':
	# x = np.linspace(0,10000,num=1000)
	# y = np.linspace(1,10001,num=1000)
	# x = np.random.random_sample(size=1000)
	# y = np.random.random_sample(size=1000)
	x = np.random.normal(0,1, 1000)
	y = np.random.normal(0,1, 1000)
	adf, pvalue, usedlag, nobs, criticalValues, icbest = cointegration_test(x,y)
	print adf, pvalue
	print criticalValues


	# for y in range(0,6):
	# for i in range(1,6):
	# 	if i != y:
	# 		print str(y), "vs", str(i), cointegration_test(self.dictOfRunningAnalyses[str(i)][2:-3],self.dictOfRunningAnalyses[str(y)][2:-3])
