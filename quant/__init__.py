"""Bazzar quant analytics library.

Standalone quantitative-finance modules, organized by domain. Each module is
a pure, side-effect-free building block (data in, numbers out). Rendering and
persistence live in `backend/`; these modules never touch the database, the
network, or the filesystem.

Subpackages:
    risk        VaR / ES (ETL) / expected-shortfall backtests, capital, stress
    copulas     Copula families, calibration, simulation, tail dependence
    timeseries  ARIMA/GARCH/EWMA, cointegration, stationarity, technicals
    portfolio   CAPM, factor models, optimization, attribution, P&L
    stats       OLS/GLS regression, hypothesis tests, PCA, distributions
    pricing     Binomial lattices, Greeks approximations
"""
