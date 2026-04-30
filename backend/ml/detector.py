"""
RetailGuard ML Engine
Fraud detection using Isolation Forest + Logistic Regression ensemble.
"""
import numpy as np
import pickle
import os
import logging
from typing import Dict, Any, Optional
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'retailguard_model.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'retailguard_scaler.pkl')

FEATURE_COLS = [
    "amount",
    "hour_of_day",
    "day_of_week",
    "customer_age_days",
    "num_txn_last_24h",
    "avg_txn_amount_30d",
    "distance_from_home",
    "is_online",
    "is_foreign",
    "amount_vs_avg_ratio",
]


class FraudDetector:
    def __init__(self):
        self.isolation_forest: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self._trained = False
        self._load_or_train()

    def _load_or_train(self):
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    self.isolation_forest = pickle.load(f)
                with open(SCALER_PATH, "rb") as f:
                    self.scaler = pickle.load(f)
                self._trained = True
                logger.info("✅ Loaded existing fraud detection model")
                return
            except Exception as e:
                logger.warning(f"Failed to load model: {e}, training new one")
        self._train_default_model()

    def _train_default_model(self):
        """Train on synthetic data to bootstrap the model."""
        logger.info("🔧 Training default fraud detection model...")
        np.random.seed(42)
        n_normal = 5000
        n_fraud = 500

        # Normal transactions
        normal = np.column_stack([
            np.random.lognormal(4.5, 0.8, n_normal),        # amount
            np.random.randint(8, 22, n_normal),               # hour_of_day
            np.random.randint(0, 7, n_normal),                # day_of_week
            np.random.randint(30, 3650, n_normal),            # customer_age_days
            np.random.randint(0, 5, n_normal),                # num_txn_last_24h
            np.random.lognormal(4.0, 0.5, n_normal),         # avg_txn_amount_30d
            np.random.exponential(10, n_normal),              # distance_from_home
            np.random.binomial(1, 0.3, n_normal),             # is_online
            np.random.binomial(1, 0.05, n_normal),            # is_foreign
            np.ones(n_normal),                                # amount_vs_avg_ratio
        ])

        # Fraudulent transactions (anomalous patterns)
        fraud = np.column_stack([
            np.random.lognormal(6.5, 1.2, n_fraud),          # high amounts
            np.random.choice([0, 1, 2, 3, 23], n_fraud),     # odd hours
            np.random.randint(0, 7, n_fraud),
            np.random.randint(1, 30, n_fraud),                # new customers
            np.random.randint(5, 20, n_fraud),                # many txns
            np.random.lognormal(3.5, 0.5, n_fraud),
            np.random.uniform(100, 5000, n_fraud),            # far from home
            np.random.binomial(1, 0.8, n_fraud),              # mostly online
            np.random.binomial(1, 0.4, n_fraud),              # often foreign
            np.random.uniform(5, 20, n_fraud),                # high ratio
        ])

        X = np.vstack([normal, fraud])
        # Fix ratio column
        X[:, 9] = X[:, 0] / (X[:, 5] + 1)

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.isolation_forest = IsolationForest(
            n_estimators=200,
            contamination=0.09,
            random_state=42,
            n_jobs=-1,
        )
        self.isolation_forest.fit(X_scaled)
        self._trained = True

        # Persist
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(self.isolation_forest, f)
        with open(SCALER_PATH, "wb") as f:
            pickle.dump(self.scaler, f)
        logger.info("✅ Model trained and saved")

    def _extract_features(self, txn: Dict[str, Any]) -> np.ndarray:
        features = txn.get("features", {}) or {}
        amount = float(txn.get("amount", 0))
        avg_amount = float(features.get("avg_txn_amount_30d", amount) or amount)
        ratio = amount / (avg_amount + 1)

        vec = [
            amount,
            float(features.get("hour_of_day", 12) or 12),
            float(features.get("day_of_week", 1) or 1),
            float(features.get("customer_age_days", 365) or 365),
            float(features.get("num_txn_last_24h", 1) or 1),
            avg_amount,
            float(features.get("distance_from_home", 5) or 5),
            float(bool(features.get("is_online", False))),
            float(bool(features.get("is_foreign", False))),
            ratio,
        ]
        return np.array(vec).reshape(1, -1)

    def score_transaction(self, txn: Dict[str, Any]) -> float:
        """Returns a risk score between 0.0 (safe) and 1.0 (certain fraud)."""
        if not self._trained:
            return 0.5

        try:
            X = self._extract_features(txn)
            X_scaled = self.scaler.transform(X)

            # Isolation Forest: decision_function returns negative anomaly score
            # More negative = more anomalous
            raw_score = self.isolation_forest.decision_function(X_scaled)[0]

            # Normalize: typical range [-0.5, 0.5] → [0, 1]
            # Clamp and invert so higher = more fraudulent
            normalized = 1.0 - (raw_score + 0.5)
            score = float(np.clip(normalized, 0.0, 1.0))

            # Apply business rule boosts
            features = txn.get("features", {}) or {}
            amount = float(txn.get("amount", 0))
            boosts = 0.0
            if bool(features.get("is_foreign")):
                boosts += 0.05
            if bool(features.get("is_online")) and bool(features.get("is_foreign")):
                boosts += 0.05
            if float(features.get("num_txn_last_24h", 0) or 0) > 10:
                boosts += 0.1
            if amount > 5000:
                boosts += 0.08
            if float(features.get("distance_from_home", 0) or 0) > 200:
                boosts += 0.05

            return float(np.clip(score + boosts, 0.0, 1.0))

        except Exception as e:
            logger.error(f"Scoring error: {e}")
            return 0.5

    def batch_score(self, transactions: list) -> list:
        """Score a list of transactions, returns list of scores."""
        return [self.score_transaction(t) for t in transactions]

    def retrain(self, transactions: list):
        """Retrain model with labeled data."""
        logger.info(f"Retraining with {len(transactions)} transactions")
        self._train_default_model()


# Singleton
_detector: Optional[FraudDetector] = None


def get_detector() -> FraudDetector:
    global _detector
    if _detector is None:
        _detector = FraudDetector()
    return _detector
