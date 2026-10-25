import os
import joblib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

from app.core.config import MODELS_DIR

logger = logging.getLogger(__name__)

class TrainableScorer:
    """
    Optional supervised regression model trained on verified teacher-awarded marks.
    Learns calibration weights between NLP feature signals and human evaluations.
    """

    MODEL_PATH = MODELS_DIR / "gradeai_rf.joblib"
    MIN_TRAINING_SAMPLES = 5

    def __init__(self):
        self.model = None
        self.weights: Optional[np.ndarray] = None
        self._load_saved_model()

    def _load_saved_model(self):
        if self.MODEL_PATH.exists():
            try:
                loaded = joblib.load(self.MODEL_PATH)
                if isinstance(loaded, np.ndarray):
                    self.weights = loaded
                else:
                    self.model = loaded
                logger.info(f"Loaded trained model artifact from {self.MODEL_PATH}")
            except Exception as e:
                logger.warning(f"Failed to load trained model: {e}")
                self.model = None
                self.weights = None

    def is_trained(self) -> bool:
        return (self.model is not None) or (self.weights is not None)

    def extract_features(
        self,
        keyword_coverage: float,
        tfidf_similarity: float,
        semantic_similarity: float,
        rubric_score: float,
        student_length: int,
        model_length: int
    ) -> np.ndarray:
        """
        Extract normalized numerical features for the regression model.
        Features:
        0: Keyword coverage ratio [0, 1]
        1: TF-IDF cosine similarity [0, 1]
        2: Semantic similarity [0, 1]
        3: Rubric score ratio [0, 1]
        4: Normalized length ratio min(1.5, student_length / max(1, model_length))
        """
        len_ratio = min(1.5, float(student_length) / max(1.0, float(model_length)))
        return np.array([
            keyword_coverage,
            tfidf_similarity,
            semantic_similarity,
            rubric_score,
            len_ratio
        ], dtype=np.float32)

    def train(self, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train regression model using validated teacher marks.
        samples: list of dicts with:
        - keyword_coverage, tfidf_similarity, semantic_similarity, rubric_score
        - student_length, model_length
        - max_marks
        - teacher_awarded_marks
        """
        if len(samples) < self.MIN_TRAINING_SAMPLES:
            return {
                "success": False,
                "error": f"Insufficient training data. Found {len(samples)} approved answers; minimum {self.MIN_TRAINING_SAMPLES} required.",
                "sample_count": len(samples)
            }

        X = []
        y = []

        for s in samples:
            feat = self.extract_features(
                keyword_coverage=s.get("keyword_coverage", 0.0),
                tfidf_similarity=s.get("tfidf_similarity", 0.0),
                semantic_similarity=s.get("semantic_similarity", 0.0),
                rubric_score=s.get("rubric_score", 0.0),
                student_length=s.get("student_length", 0),
                model_length=s.get("model_length", 1)
            )
            # Target is normalized score [0, 1] (teacher_marks / max_marks)
            max_m = max(0.1, float(s.get("max_marks", 10.0)))
            target_ratio = min(1.0, max(0.0, float(s.get("teacher_awarded_marks", 0.0)) / max_m))
            
            X.append(feat)
            y.append(target_ratio)

        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.float32)

        if SKLEARN_AVAILABLE:
            test_size = 0.2 if len(samples) >= 10 else 0.1
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            regressor = RandomForestRegressor(
                n_estimators=50,
                max_depth=5,
                random_state=42
            )
            regressor.fit(X_train, y_train)
            y_pred = regressor.predict(X_test)
            mae = float(mean_absolute_error(y_test, y_pred))
            rmse = float(root_mean_squared_error(y_test, y_pred))
            try:
                r2 = float(r2_score(y_test, y_pred))
            except Exception:
                r2 = 0.0

            joblib.dump(regressor, self.MODEL_PATH)
            self.model = regressor
            self.weights = None
        else:
            # Fallback: Closed-form Ridge Regression via pure NumPy
            # Add bias term (column of 1s)
            X_b = np.hstack([np.ones((X.shape[0], 1), dtype=np.float32), X])
            alpha = 0.1
            I = np.eye(X_b.shape[1], dtype=np.float32)
            I[0, 0] = 0.0  # Do not regularize bias
            w = np.linalg.solve(X_b.T @ X_b + alpha * I, X_b.T @ y)

            # In-sample metrics
            y_pred = X_b @ w
            mae = float(np.mean(np.abs(y - y_pred)))
            rmse = float(np.sqrt(np.mean((y - y_pred) ** 2)))
            ss_tot = float(np.sum((y - np.mean(y)) ** 2))
            ss_res = float(np.sum((y - y_pred) ** 2))
            r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

            joblib.dump(w, self.MODEL_PATH)
            self.weights = w
            self.model = None

        return {
            "success": True,
            "sample_count": len(samples),
            "model_type": "RandomForestRegressor" if SKLEARN_AVAILABLE else "NumPy_RidgeRegressor",
            "metrics": {
                "mae": round(mae, 4),
                "rmse": round(rmse, 4),
                "r2_score": round(r2, 4)
            },
            "model_path": str(self.MODEL_PATH)
        }

    def predict(
        self,
        keyword_coverage: float,
        tfidf_similarity: float,
        semantic_similarity: float,
        rubric_score: float,
        student_length: int,
        model_length: int,
        max_marks: float
    ) -> Optional[float]:
        """Predict calibrated mark using trained model if available."""
        if not self.is_trained():
            return None

        features = self.extract_features(
            keyword_coverage, tfidf_similarity, semantic_similarity, rubric_score, student_length, model_length
        )

        if self.model is not None:
            predicted_ratio = float(self.model.predict(features.reshape(1, -1))[0])
        elif self.weights is not None:
            feat_b = np.insert(features, 0, 1.0)
            predicted_ratio = float(np.dot(feat_b, self.weights))
        else:
            return None

        bounded_ratio = max(0.0, min(1.0, predicted_ratio))
        return round(bounded_ratio * max_marks, 2)


trainable_scorer = TrainableScorer()
