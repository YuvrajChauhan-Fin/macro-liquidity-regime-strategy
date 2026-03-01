import pandas as pd


class StrategyEngine:

    """
    Converts regimes into portfolio exposure
    and builds strategy returns + equity curve.
    """

    def __init__(self):

        # exposure mapping
        self.exposure_map = {

            "risk_on": 1.2,
            "neutral": 1.0,
            "risk_off": 0.0

        }

    def run(
        self,
        df: pd.DataFrame,
        regimes: pd.Series
    ):

        """
        Parameters
        ----------
        df :
            Must contain NIFTY_RET.

        regimes :
            Output from WalkForwardEngine.

        Returns
        -------
        strategy dataframe.
        """

        if "NIFTY_RET" not in df.columns:
            raise ValueError("NIFTY_RET missing from dataframe.")

        # ---------------------------
        # Align data
        # ---------------------------

        aligned_df = df.loc[regimes.index].copy()

        aligned_df["regime"] = regimes

        # ---------------------------
        # Map exposure
        # ---------------------------

        aligned_df["exposure"] = aligned_df["regime"].map(
            self.exposure_map
        )

        aligned_df["exposure"] = aligned_df["exposure"].fillna(0)

        # ---------------------------
        # Strategy returns
        # ---------------------------

        aligned_df["strategy_ret"] = (

            aligned_df["exposure"]
            *
            aligned_df["NIFTY_RET"]

        )

        # ---------------------------
        # Equity curve
        # ---------------------------

        aligned_df["equity_curve"] = (

            1 + aligned_df["strategy_ret"]

        ).cumprod()

        return aligned_df