import pandas as pd

class TrendEngine:
    """
    12-month time-series momentum engine.
    Monthly frequency.
    """

    def __init__(self, lookback=12):
        self.lookback = lookback

    def generate_signal(self, price_series: pd.Series) -> pd.DataFrame:
        """
        Parameters
        ----------
        price_series : pd.Series
            Monthly price series (NIFTY total return preferred)

        Returns
        -------
        pd.DataFrame
            index = date
            column = trend_signal (0 or 1)
        """

        # 12M return
        momentum = price_series.pct_change(self.lookback)

        # Binary signal
        signal = (momentum > 0).astype(int)

        signal_df = pd.DataFrame({
            "trend_signal": signal
        })

        return signal_df.dropna()