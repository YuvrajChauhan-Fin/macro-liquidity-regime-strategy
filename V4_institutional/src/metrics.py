import numpy as np
import pandas as pd


def annualized_return(returns: pd.Series, periods_per_year: int = 12) -> float:
    """
    Calculate annualized return (CAGR) from periodic returns.
    """
    cumulative = (1 + returns).prod()
    n_periods = len(returns)
    years = n_periods / periods_per_year

    if years == 0:
        return np.nan

    return cumulative ** (1 / years) - 1


def sharpe_ratio(returns: pd.Series, periods_per_year: int = 12) -> float:
    """
    Calculate annualized Sharpe ratio.
    Assumes returns are excess returns (or risk-free ~ 0).
    """
    if returns.std() == 0:
        return np.nan

    return (returns.mean() / returns.std()) * np.sqrt(periods_per_year)


def max_drawdown(cumulative_series: pd.Series) -> float:
    """
    Calculate maximum drawdown from cumulative return series.
    """
    rolling_max = cumulative_series.cummax()
    drawdown = (cumulative_series - rolling_max) / rolling_max
    return drawdown.min()