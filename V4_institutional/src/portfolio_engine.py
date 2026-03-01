import pandas as pd

from src.regime_engine import RegimeEngine
from src.risk_engine import RiskEngine
from src.vol_target_engine import VolTargetEngine


class MultiAssetRotationEngine:

    def __init__(
        self,
        df,
        assets=["NIFTY", "SPY", "GLD"],
        lookback=12,
        transaction_cost=0.001
    ):

        self.df = df.copy()
        self.assets = assets
        self.lookback = lookback
        self.transaction_cost = transaction_cost

        self.vol_target_engine = VolTargetEngine(
            target_vol=0.10,
            lookback=12
        )

        self.monthly_prices = None
        self.monthly_returns = None
        self.regime_monthly = None
        self.momentum = None
        self.weights = None
        self.turnover = None
        self.portfolio_returns = None

    # --------------------------------------------------
    # Monthly Data
    # --------------------------------------------------
    def _build_monthly_data(self):

        monthly_prices = (
            self.df[self.assets]
            .resample("ME")
            .last()
        )

        monthly_prices = monthly_prices.dropna()

        self.monthly_prices = monthly_prices

        self.monthly_returns = (
            self.monthly_prices
            .pct_change()
            .dropna()
        )

    # --------------------------------------------------
    # Liquidity Regime (Strength Based)
    # --------------------------------------------------
    def _build_regime(self):

        engine = RegimeEngine()

        engine.fit(self.df)

        daily_regime = engine.predict(self.df)

        if isinstance(daily_regime, pd.DataFrame):
            daily_regime = daily_regime.squeeze()

        daily_regime = (
            daily_regime
            .reindex(self.df.index)
            .ffill()
        )

        self.regime_monthly = (
            daily_regime
            .resample("ME")
            .last()
        )

    # --------------------------------------------------
    # Momentum
    # --------------------------------------------------
    def _build_momentum(self):

        self.momentum = (
            self.monthly_prices
            .pct_change(self.lookback)
        )

    # --------------------------------------------------
    # Institutional Regime Strength Allocation
    # --------------------------------------------------
    def _generate_weights(self):

        common_index = (
            self.monthly_returns.index
            .intersection(self.momentum.index)
            .intersection(self.regime_monthly.index)
        )

        returns = self.monthly_returns.loc[common_index]
        momentum = self.momentum.loc[common_index]
        regime = self.regime_monthly.loc[common_index]

        weights = pd.DataFrame(
            0.0,
            index=returns.index,
            columns=self.assets
        )

        for date in returns.index:

            if momentum.loc[date].isna().all():
                continue

            regime_state = regime.loc[date]

            equity_assets = [
                a for a in self.assets if a != "GLD"
            ]

            equity_mom = (
                momentum.loc[date, equity_assets]
                .dropna()
            )

            # Rank equities by momentum
            ranked = equity_mom.sort_values(
                ascending=False
            )

            # -----------------------------------
            # STRONG RISK ON (+2)
            # 80% equity / 20% gold
            # -----------------------------------
            if regime_state == 2:

                if not ranked.empty:
                    weights.loc[date, ranked.index[0]] = 0.80

                weights.loc[date, "GLD"] = 0.20

            # -----------------------------------
            # MODERATE RISK ON (+1)
            # 60% equity / 40% gold
            # -----------------------------------
            elif regime_state == 1:

                if not ranked.empty:
                    weights.loc[date, ranked.index[0]] = 0.60

                weights.loc[date, "GLD"] = 0.40

            # -----------------------------------
            # DEFENSIVE (0)
            # 30% equity / 70% gold
            # -----------------------------------
            elif regime_state == 0:

                if not ranked.empty:
                    weights.loc[date, ranked.index[0]] = 0.30

                weights.loc[date, "GLD"] = 0.70

            # -----------------------------------
            # STRONG RISK OFF (-1)
            # 100% gold
            # -----------------------------------
            else:

                weights.loc[date, "GLD"] = 1.0

        # -----------------------------------
        # Prevent Lookahead Bias
        # -----------------------------------
        weights = weights.shift(1).fillna(0.0)

        # -----------------------------------
        # Apply Risk Budget (Inverse Vol)
        # -----------------------------------
        risk_engine = RiskEngine(
            returns=self.monthly_returns,
            vol_lookback=12
        )

        weights = risk_engine.apply_inverse_vol_weights(
            weights
        )

        self.weights = weights

    # --------------------------------------------------
    # Backtest
    # --------------------------------------------------
    def backtest(self):

        self._build_monthly_data()
        self._build_regime()
        self._build_momentum()
        self._generate_weights()

        aligned_returns = self.monthly_returns.loc[
            self.weights.index
        ]

        gross_returns = (
            self.weights * aligned_returns
        ).sum(axis=1)

        self.turnover = (
            self.weights
            .diff()
            .abs()
            .sum(axis=1)
            .fillna(0.0)
        )

        cost = self.turnover * self.transaction_cost

        raw_returns = gross_returns - cost

        # Apply Vol Targeting
        self.portfolio_returns = (
            self.vol_target_engine
            .apply_vol_targeting(raw_returns)
        )

        equity_curve = (
            1 + self.portfolio_returns
        ).cumprod()

        return equity_curve