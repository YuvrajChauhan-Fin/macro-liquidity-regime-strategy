import pandas as pd
import numpy as np


class RegimeEngine:

    def __init__(self):

        # learned ONLY from training window
        self.mean_ = None
        self.std_ = None

        self.fitted = False


    # =====================================================
    # FIT (TRAIN ONLY)
    # =====================================================

    def fit(self, train_df: pd.DataFrame):

        """
        Learn liquidity distribution from TRAINING DATA ONLY.
        """

        liquidity = self._build_liquidity_composite(train_df)

        liquidity = liquidity.dropna()

        if liquidity.empty:
            raise ValueError(
                "Liquidity series empty after preprocessing."
            )

        self.mean_ = liquidity.mean()

        self.std_ = liquidity.std()

        if self.std_ == 0 or np.isnan(self.std_):

            raise ValueError(
                "Standard deviation invalid during training."
            )

        self.fitted = True


    # =====================================================
    # PREDICT (OUT OF SAMPLE SAFE)
    # =====================================================

    def predict(self, df: pd.DataFrame):

        """
        Predict regime using TRAINING distribution.

        Output:

        +2 → Strong Risk On
        +1 → Moderate Risk On
         0 → Defensive / Neutral
        -1 → Strong Risk Off
        """

        if not self.fitted:

            raise RuntimeError(
                "RegimeEngine must be fitted before predict()."
            )

        liquidity = self._build_liquidity_composite(df)

        # ===============================
        # APPLY TRAINING DISTRIBUTION
        # ===============================

        zscore = (

            liquidity - self.mean_

        ) / self.std_

        regimes = pd.Series(
            index=zscore.index,
            dtype="float"
        )

        # =====================================
        # REGIME STRENGTH CLASSIFICATION
        # =====================================

        # Strong Risk On
        regimes[zscore > 1.0] = 2

        # Moderate Risk On
        regimes[
            (zscore > 0.0)
            & (zscore <= 1.0)
        ] = 1

        # Neutral / Defensive
        regimes[
            (zscore >= -1.0)
            & (zscore <= 0.0)
        ] = 0

        # Strong Risk Off
        regimes[zscore < -1.0] = -1

        # =====================================
        # INSTITUTIONAL CLEANUP
        # =====================================

        # avoid early NA signal breaks
        regimes = regimes.ffill()

        regimes = regimes.dropna()

        return regimes


    # =====================================================
    # LIQUIDITY COMPOSITE
    # =====================================================

    def _build_liquidity_composite(
        self,
        df: pd.DataFrame
    ):

        """
        Global Liquidity Composite.

        Uses:

        - US M2 growth
        - ECB Assets growth

        Steps:

        1) Growth rate
        2) 3 month smoothing
        3) Equal weight combine
        """

        required_cols = [

            "US_M2",
            "ECB_ASSETS"

        ]

        for col in required_cols:

            if col not in df.columns:

                raise ValueError(
                    f"{col} column missing."
                )

        # Growth

        us_growth = df["US_M2"].pct_change()

        ecb_growth = df["ECB_ASSETS"].pct_change()

        # Smooth noise

        us_growth = us_growth.rolling(3).mean()

        ecb_growth = ecb_growth.rolling(3).mean()

        # Composite

        global_liquidity = (

            us_growth + ecb_growth

        ) / 2

        return global_liquidity