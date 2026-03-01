print("DEBUG: NEW WALK_FORWARD FILE LOADED")

import pandas as pd
from src.regime_engine import RegimeEngine


class WalkForwardEngine:
    """
    Institutional Walk Forward Validation Engine
    Regime + Portfolio OOS Execution
    """

    def __init__(
        self,
        data: pd.DataFrame,
        warmup_years: int = 10,
        rebalance_freq: str = "M"
    ):

        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data must have DatetimeIndex.")

        self.data = data.sort_index()
        self.warmup_years = warmup_years
        self.rebalance_freq = rebalance_freq

    # --------------------------------------------------
    # Start Date (Full Feature Availability)
    # --------------------------------------------------
    def _get_start_date(self):

        first_valid_dates = []

        for col in self.data.columns:
            first_valid_dates.append(
                self.data[col].first_valid_index()
            )

        start_date = max(first_valid_dates)

        print(
            f"V5 Start Date (Full Feature Availability): "
            f"{start_date}"
        )

        return start_date

    # --------------------------------------------------
    # Generate Walk Forward Splits
    # --------------------------------------------------
    def _generate_splits(self):

        start_date = self._get_start_date()

        data = self.data.loc[start_date:]

        splits = []

        warmup_end = start_date + pd.DateOffset(
            years=self.warmup_years
        )

        final_date = data.index.max()

        current_test_start = warmup_end

        while current_test_start < final_date:

            train_start = start_date
            train_end = current_test_start

            test_start = current_test_start
            test_end = current_test_start + pd.DateOffset(years=1)

            if test_end > final_date:
                test_end = final_date

            splits.append({

                "train_start": train_start,
                "train_end": train_end,

                "test_start": test_start,
                "test_end": test_end

            })

            current_test_start = test_end

        print(f"Generated {len(splits)} walk-forward splits.")

        return splits

    # --------------------------------------------------
    # OOS REGIME WALK FORWARD
    # --------------------------------------------------
    def run(self):

        splits = self._generate_splits()
        all_oos_regimes = []

        for split in splits:

            print(
                f"Training "
                f"{split['train_start']} → "
                f"{split['train_end']}"
            )

            train_df = self.data.loc[
                split["train_start"]:split["train_end"]
            ]

            test_df = self.data.loc[
                split["test_start"]:split["test_end"]
            ]

            regime_engine = RegimeEngine()
            regime_engine.fit(train_df)

            test_regimes = regime_engine.predict(test_df)

            all_oos_regimes.append(test_regimes)

        oos_regimes = pd.concat(all_oos_regimes)

        return oos_regimes.sort_index()

    # ==================================================
    # WALK FORWARD PORTFOLIO BACKTEST (OOS)
    # ==================================================
    def run_portfolio_backtest(
        self,
        assets=["NIFTY", "SPY", "GLD"],
        lookback=12,
        transaction_cost=0.001
    ):

        from src.portfolio_engine import MultiAssetRotationEngine

        splits = self._generate_splits()

        # Align portfolio history to asset availability
        asset_start = self.data[assets].dropna().index[0]

        print(f"Portfolio Asset Start Date: {asset_start}")

        valid_data = self.data.loc[asset_start:].copy()

        all_oos_returns = []

        for split in splits:

            print(
                f"\n==== OOS Portfolio Test "
                f"{split['test_start']} → "
                f"{split['test_end']} ===="
            )

            combined_df = valid_data.loc[
                :split["test_end"]
            ].copy()

            print("Combined DF rows:", len(combined_df))

            portfolio = MultiAssetRotationEngine(

                df=combined_df,
                assets=assets,
                lookback=lookback

            )

            equity = portfolio.backtest()

            # -----------------------------
            # DIAGNOSTIC SAFETY CHECKS
            # -----------------------------

            if portfolio.portfolio_returns is None:

                print("Portfolio returns NONE — skipping.")
                continue

            if portfolio.portfolio_returns.empty:

                print("Portfolio returns EMPTY — skipping.")
                continue

            if portfolio.portfolio_returns.isna().all():

                print("Portfolio returns ALL NA — skipping.")
                continue

            gross_returns = portfolio.portfolio_returns

            turnover = (

                portfolio.weights
                .diff()
                .abs()
                .sum(axis=1)

            )

            net_returns = (

                gross_returns
                - turnover * transaction_cost

            )

            oos_returns = net_returns.loc[

                split["test_start"]:
                split["test_end"]

            ]

            if oos_returns.empty:

                print("OOS slice empty — skipping.")
                continue

            all_oos_returns.append(
                oos_returns
            )

        if len(all_oos_returns) == 0:

            raise RuntimeError(
                "No valid OOS returns generated. "
                "Portfolio engine produced no usable data."
            )

        oos_returns = pd.concat(
            all_oos_returns
        )

        oos_returns = oos_returns[
            ~oos_returns.index.duplicated()
        ]

        print(
            f"Total OOS Months: "
            f"{len(oos_returns)}"
        )

        return oos_returns.sort_index()