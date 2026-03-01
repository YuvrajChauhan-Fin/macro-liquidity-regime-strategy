import pandas as pd
import numpy as np


class RiskEngine:
    """
    Institutional Risk Budget Engine

    Responsibilities:

    1) Estimate asset volatility
    2) Apply inverse volatility scaling
    3) Normalize portfolio exposure

    Does NOT know anything about:
    - regime
    - momentum
    - asset selection

    Pure risk math only.
    """

    def __init__(

        self,
        returns: pd.DataFrame,
        vol_lookback: int = 12

    ):

        self.returns = returns.copy()
        self.vol_lookback = vol_lookback

        self.volatility = None


    # --------------------------------------------------
    # Estimate Rolling Volatility
    # --------------------------------------------------
    def compute_volatility(self):

        """
        Monthly volatility estimate.

        Annualised volatility.
        """

        vol = (

            self.returns
            .rolling(self.vol_lookback)
            .std()

            * np.sqrt(12)

        )

        self.volatility = vol

        return vol


    # --------------------------------------------------
    # Apply Risk Budgeting
    # --------------------------------------------------
    def apply_inverse_vol_weights(

        self,
        raw_weights: pd.DataFrame

    ):

        """
        Risk parity style scaling.

        Higher volatility asset → smaller weight.
        """

        if self.volatility is None:

            self.compute_volatility()

        vol = self.volatility.reindex(

            raw_weights.index

        )

        # Avoid division by zero
        vol = vol.replace(0, np.nan)

        inv_vol = 1 / vol

        risk_scaled = raw_weights * inv_vol


        # -----------------------------
        # Normalize exposure
        # -----------------------------

        exposure = risk_scaled.sum(axis=1)

        exposure = exposure.replace(0, np.nan)

        normalized_weights = (

            risk_scaled

            .div(exposure, axis=0)

        )

        # Replace remaining NaNs safely
        normalized_weights = (

            normalized_weights

            .fillna(0.0)

        )

        return normalized_weights