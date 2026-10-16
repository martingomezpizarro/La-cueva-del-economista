# Fuente: https://arch.readthedocs.io/en/latest/univariate/volatility.html

Volatility Processes - arch 7.2.0 
 
 

 
 
 
 
 
 
 

 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 Skip to content
 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 Fixed Variance 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 Writing New Volatility Processes 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 Volatility Processes 
 
 
 
 
 Volatility Processes 
 
 
 

 

 
 
 
 
 
 
 Fixed Variance 
 
 
 
 
 
 
 
 
 Writing New Volatility Processes 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
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
 
 
 

 
 
 
 
 
 
 
 
 
 
 
 
 

 

 
 
 
 
 
 
 
 
 
 

 Volatility Processes ¶ 
 A volatility process is added to a mean model to capture time-varying
volatility. 
 
 
 ConstantVariance () 
 Constant volatility process 
 
 GARCH ([p, o, q, power]) 
 GARCH and related model estimation 
 
 FIGARCH ([p, q, power, truncation]) 
 FIGARCH model 
 
 EGARCH ([p, o, q]) 
 EGARCH model estimation 
 
 HARCH ([lags]) 
 Heterogeneous ARCH process 
 
 MIDASHyperbolic ([m, asym]) 
 MIDAS Hyperbolic ARCH process 
 
 ARCH ([p]) 
 ARCH process 
 
 APARCH ([p, o, q, delta, common_asym]) 
 Asymmetric Power ARCH (APARCH) volatility process 
 
 
 
 Parameterless Variance Processes ¶ 
 Some volatility processes use fixed parameters and so have no parameters that
are estimable. 
 
 
 EWMAVariance ([lam]) 
 Exponentially Weighted Moving-Average (RiskMetrics) Variance process 
 
 RiskMetrics2006 ([tau0, tau1, kmax, rho]) 
 RiskMetrics 2006 Variance process 
 
 
 
 FixedVariance ¶ 
 The FixedVariance class is a special-purpose volatility process that allows
the so-called zig-zag algorithm to be used. See the example for usage. 
 
 
 FixedVariance (variance[, unit_scale]) 
 Fixed volatility process 
 
 
 
 Writing New Volatility Processes ¶ 
 All volatility processes must inherit from VolatilityProcess and provide
all public methods. 
 
 
 VolatilityProcess () 
 Abstract base class for ARCH models. 
 
 
 
 They may optionally expose a
 VolatilityUpdater class
that can be used in ARCHInMean estimation. 
 
 
 VolatilityUpdater 
 Base class that all volatility updaters must inherit from.
