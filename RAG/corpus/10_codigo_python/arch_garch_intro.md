# Fuente: https://arch.readthedocs.io/en/latest/univariate/introduction.html

Introduction to ARCH Models - arch 7.2.0 
 
 

 
 
 
 
 
 
 

 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 Skip to content
 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
 Returns 
 
 
 
 
 
 
 Return type 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
 Examples 
 
 
 

 
 
 
 
 
 
 
 
 
 
 Forecasting 
 
 
 

 
 
 
 
 
 
 
 
 
 
 Volatility Forecasting 
 
 
 

 
 
 
 
 
 
 
 
 
 
 Value- at- Risk Forecasting 
 
 
 

 
 
 
 
 
 
 
 
 
 
 Forecasting Scenarios 
 
 
 

 
 
 
 
 
 
 
 
 
 
 Forecasting with Exogenous Variables 
 
 
 

 
 
 
 
 
 
 
 
 
 
 Mean Models 
 
 
 

 
 
 
 
 
 
 
 
 
 
 Volatility Processes 
 
 
 

 
 
 
 
 
 
 
 
 
 
 Using the Fixed Variance Process 
 
 
 

 
 
 
 
 
 
 
 
 
 
 Distributions 
 
 
 

 
 
 
 
 
 
 
 
 
 
 Results 
 
 
 

 
 
 
 
 
 
 
 
 
 
 Utilities 
 
 
 

 
 
 
 
 
 
 
 
 
 
 Background and References 
 
 
 

 
 
 
 
 
 
 

 
 
 
 

 
 
 
 
 
 
 Bootstrapping 
 
 
 

 
 
 
 

 
 
 
 
 
 
 Multiple Comparison Problems 
 
 
 

 
 
 
 

 
 
 
 
 
 
 Unit Root Testing 
 
 
 

 
 
 
 

 
 
 
 
 
 
 Cointegration Analysis 
 
 
 

 
 
 
 

 
 
 
 
 
 
 Long- run Covariance Estimation 
 
 
 

 
 
 
 

 
 
 
 
 
 
 API Reference 
 
 
 

 
 
 
 

 
 
 
 
 
 
 Common Type Definitions 
 
 
 

 
 
 
 

 
 
 
 
 
 
 Change Log 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
 
 

 

 
 
 
 
 
 
 Returns 
 
 
 
 
 
 
 Return type 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 

 Introduction to ARCH Models ¶ 
 ARCH models are a popular class of volatility models that use observed values
of returns or residuals as volatility shocks. A basic GARCH model is specified
as 
 
\begin{eqnarray}
 r_t & = & \mu + \epsilon_t \\
 \epsilon_t & = & \sigma_t e_t \\
 \sigma^2_t & = & \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma^2_{t-1}
\end{eqnarray} A complete ARCH model is divided into three components: 
 
 a mean model , e.g., a constant mean or an ARX ; 
 a volatility process , e.g., a GARCH or an EGARCH process; and 
 a distribution for the standardized residuals. 
 
 In most applications, the simplest method to construct this model is to use the constructor
function arch_model() 
 import datetime as dt 

 import pandas_datareader.data as web 

 from arch import arch_model 

 start = dt . datetime ( 2000 , 1 , 1 ) 
 end = dt . datetime ( 2014 , 1 , 1 ) 
 sp500 = web . DataReader ( '^GSPC' , 'yahoo' , start = start , end = end ) 
 returns = 100 * sp500 [ 'Adj Close' ] . pct_change () . dropna () 
 am = arch_model ( returns ) 
 
 
 Alternatively, the same model can be manually assembled from the building
blocks of an ARCH model 
 from arch import ConstantMean , GARCH , Normal 

 am = ConstantMean ( returns ) 
 am . volatility = GARCH ( 1 , 0 , 1 ) 
 am . distribution = Normal () 
 
 
 In either case, model parameters are estimated using 
 res = am . fit () 
 
 
 with the following output 
 Iteration : 1 , Func . Count : 6 , Neg . LLF : 5159.58323938 
 Iteration : 2 , Func . Count : 16 , Neg . LLF : 5156.09760149 
 Iteration : 3 , Func . Count : 24 , Neg . LLF : 5152.29989336 
 Iteration : 4 , Func . Count : 31 , Neg . LLF : 5146.47531817 
 Iteration : 5 , Func . Count : 38 , Neg . LLF : 5143.86337547 
 Iteration : 6 , Func . Count : 45 , Neg . LLF : 5143.02096168 
 Iteration : 7 , Func . Count : 52 , Neg . LLF : 5142.24105141 
 Iteration : 8 , Func . Count : 60 , Neg . LLF : 5142.07138907 
 Iteration : 9 , Func . Count : 67 , Neg . LLF : 5141.416653 
 Iteration : 10 , Func . Count : 73 , Neg . LLF : 5141.39212288 
 Iteration : 11 , Func . Count : 79 , Neg . LLF : 5141.39023885 
 Iteration : 12 , Func . Count : 85 , Neg . LLF : 5141.39023359 
 Optimization terminated successfully . ( Exit mode 0 ) 
 Current function value : 5141.39023359 
 Iterations : 12 
 Function evaluations : 85 
 Gradient evaluations : 12 
 
 
 print ( res . summary ()) 
 
 
 yields 
 Constant Mean - GARCH Model Results 
 ============================================================================== 
 Dep . Variable : Adj Close R - squared : - 0.001 
 Mean Model : Constant Mean Adj . R - squared : - 0.001 
 Vol Model : GARCH Log - Likelihood : - 5141.39 
 Distribution : Normal AIC : 10290.8 
 Method : Maximum Likelihood BIC : 10315.4 
 No . Observations : 3520 
 Date : Fri , Dec 02 2016 Df Residuals : 3516 
 Time : 22 : 22 : 28 Df Model : 4 
 Mean Model 
 ============================================================================== 
 coef std err t P >| t | 95.0 % Conf . Int . 
 ------------------------------------------------------------------------------ 
 mu 0.0531 1.487e-02 3.569 3.581e-04 [ 2.392e-02 , 8.220e-02 ] 
 Volatility Model 
 ============================================================================== 
 coef std err t P >| t | 95.0 % Conf . Int . 
 ------------------------------------------------------------------------------ 
 omega 0.0156 4.932e-03 3.155 1.606e-03 [ 5.892e-03 , 2.523e-02 ] 
 alpha [ 1 ] 0.0879 1.140e-02 7.710 1.260e-14 [ 6.554e-02 , 0.110 ] 
 beta [ 1 ] 0.9014 1.183e-02 76.163 0.000 [ 0.878 , 0.925 ] 
 ============================================================================== 

 Covariance estimator : robust 
 
 
 Model Constructor ¶ 
 While models can be carefully specified using the individual components, most common specifications can be specified
using a simple model constructor. 
 
 
 arch.univariate. arch_model ( y : ndarray | DataFrame | Series | None , x : ndarray | DataFrame | None = None , mean : 'Constant' | 'Zero' | 'LS' | 'AR' | 'ARX' | 'HAR' | 'HARX' | 'constant' | 'zero' = 'Constant' , lags : int | list [ int ] | ndarray [ Any , dtype [ int32 ] ] | ndarray [ Any , dtype [ longlong ] ] | None = 0 , vol : 'GARCH' | 'ARCH' | 'EGARCH' | 'FIGARCH' | 'APARCH' | 'HARCH' = 'GARCH' , p : int | list [ int ] = 1 , o : int = 0 , q : int = 1 , power : float = 2.0 , dist : 'normal' | 'gaussian' | 't' | 'studentst' | 'skewstudent' | 'skewt' | 'ged' | 'generalized error' = 'normal' , hold_back : int | None = None , rescale : bool | None = None ) → HARX [source] ¶ 
 Initialization of common ARCH model specifications 
 
 Parameters : ¶ 
 
 y : ndarray | DataFrame | Series | None ¶ The dependent variable 
 
 x : ndarray | DataFrame | None = None ¶ Exogenous regressors. Ignored if model does not permit exogenous
regressors. 
 
 mean : 'Constant' | 'Zero' | 'LS' | 'AR' | 'ARX' | 'HAR' | 'HARX' | 'constant' | 'zero' = 'Constant' ¶ Name of the mean model. Currently supported options are: ‘Constant’,
‘Zero’, ‘LS’, ‘AR’, ‘ARX’, ‘HAR’ and ‘HARX’ 
 
 lags : int | list [ int ] | ndarray [ Any , dtype [ int32 ] ] | ndarray [ Any , dtype [ longlong ] ] | None = 0 ¶ Either a scalar integer value indicating lag length or a list of
integers specifying lag locations. 
 
 vol : 'GARCH' | 'ARCH' | 'EGARCH' | 'FIGARCH' | 'APARCH' | 'HARCH' = 'GARCH' ¶ Name of the volatility model. Currently supported options are:
‘GARCH’ (default), ‘ARCH’, ‘EGARCH’, ‘FIGARCH’, ‘APARCH’ and ‘HARCH’ 
 
 p : int | list [ int ] = 1 ¶ Lag order of the symmetric innovation 
 
 o : int = 0 ¶ Lag order of the asymmetric innovation 
 
 q : int = 1 ¶ Lag order of lagged volatility or equivalent 
 
 power : float = 2.0 ¶ Power to use with GARCH and related models 
 
 dist : 'normal' | 'gaussian' | 't' | 'studentst' | 'skewstudent' | 'skewt' | 'ged' | 'generalized error' = 'normal' ¶ Name of the error distribution. Currently supported options are: 
 
 
 Normal: ‘normal’, ‘gaussian’ (default) 
 Students’s t: ‘t’, ‘studentst’ 
 Skewed Student’s t: ‘skewstudent’, ‘skewt’ 
 Generalized Error Distribution: ‘ged’, ‘generalized error” 
 
 
 
 
 hold_back : int | None = None ¶ Number of observations at the start of the sample to exclude when
estimating model parameters. Used when comparing models with different
lag lengths to estimate on the common sample. 
 
 rescale : bool | None = None ¶ Flag indicating whether to automatically rescale data if the scale
of the data is likely to produce convergence issues when estimating
model parameters. If False, the model is estimated on the data without
transformation. If True, than y is rescaled and the new scale is
reported in the estimation results. 
 
 
 
 Returns : ¶ 
 model – Configured ARCH model 
 
 Return type : ¶ 
 arch.univariate.base.ARCHModel 
 
 
 Examples 
 >>> import datetime as dt 
 >>> import pandas_datareader.data as web 
 >>> djia = web . get_data_fred ( 'DJIA' ) 
 >>> returns = 100 * djia [ 'DJIA' ] . pct_change () . dropna () 
 
 
 A basic GARCH(1,1) with a constant mean can be constructed using only
the return data 
 >>> from arch.univariate import arch_model 
 >>> am = arch_model ( returns ) 
 
 
 Alternative mean and volatility processes can be directly specified 
 >>> am = arch_model ( returns , mean = 'AR' , lags = 2 , vol = 'harch' , p = [ 1 , 5 , 22 ]) 
 
 
 This example demonstrates the construction of a zero mean process
with a TARCH volatility process and Student t error distribution 
 >>> am = arch_model ( returns , mean = 'zero' , p = 1 , o = 1 , q = 1 , 
 ... power = 1.0 , dist = 'StudentsT' ) 
 
 
 Notes 
 Input that are not relevant for a particular specification, such as lags 
when mean=’zero’ , are silently ignored.
