import pandas as pd


class VolTargetEngine:

    def __init__(self, target_vol=0.10, lookback=12):
        self.target_vol = target_vol
        self.lookback = lookback

    def apply_vol_targeting(
        self,
        portfolio_returns: pd.Series
    ):

        realized_vol = (
            portfolio_returns
            .rolling(self.lookback)
            .std() * (12 ** 0.5)
        )

        scaling = self.target_vol / realized_vol

        scaling = scaling.clip(upper=2.0)  # optional leverage cap

        adjusted_returns = portfolio_returns * scaling.shift(1)

        return adjusted_returns.fillna(0.0)