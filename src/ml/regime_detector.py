"""
Regime Detector - Machine Learning based Market Regime Classification
Uses Random Forest to identify market phases: Bull, Bear, Sideways, Crisis, Recovery
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import logging
import pickle
from pathlib import Path


class RegimeDetector:
    """
    ML-based market regime classifier
    
    Features:
    - VIX (volatility)
    - Yield curve (10Y - 2Y)
    - Moving average trends
    - Volume patterns
    - Price momentum
    
    Target Classes:
    0: BULL
    1: BEAR
    2: SIDEWAYS
    3: CRISIS
    4: RECOVERY
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.logger = logging.getLogger("aegis.ml.regime_detector")
        
        # Model components
        self.model: Optional[RandomForestClassifier] = None
        self.scaler = StandardScaler()
        self.feature_names: List[str] = []
        self.class_names = ["BULL", "BEAR", "SIDEWAYS", "CRISIS", "RECOVERY"]
        
        # Model hyperparameters
        self.n_estimators = 100
        self.max_depth = 10
        self.min_samples_split = 10
        
        # Load model if path provided
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
        else:
            self.logger.info("Regime Detector initialized (untrained)")
    
    def extract_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features from market data
        
        Args:
            data: DataFrame with columns: date, open, high, low, close, volume, vix, treasury_10y, treasury_2y
            
        Returns:
            DataFrame with engineered features
        """
        df = data.copy()
        
        # Price-based features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['volatility_20'] = df['returns'].rolling(20).std()
        df['volatility_60'] = df['returns'].rolling(60).std()
        
        # Moving averages
        df['ma_20'] = df['close'].rolling(20).mean()
        df['ma_50'] = df['close'].rolling(50).mean()
        df['ma_200'] = df['close'].rolling(200).mean()
        
        # MA trends
        df['price_above_ma50'] = (df['close'] > df['ma_50']).astype(int)
        df['price_above_ma200'] = (df['close'] > df['ma_200']).astype(int)
        df['ma50_above_ma200'] = (df['ma_50'] > df['ma_200']).astype(int)
        
        # Momentum indicators
        df['rsi_14'] = self._calculate_rsi(df['close'], 14)
        df['momentum_10'] = df['close'] / df['close'].shift(10) - 1
        df['momentum_20'] = df['close'] / df['close'].shift(20) - 1
        
        # Volume features
        df['volume_ma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma_20']
        
        # VIX features (if available)
        if 'vix' in df.columns:
            df['vix_ma_20'] = df['vix'].rolling(20).mean()
            df['vix_spike'] = (df['vix'] > df['vix_ma_20'] * 1.5).astype(int)
        else:
            df['vix'] = 15.0  # Default VIX
            df['vix_ma_20'] = 15.0
            df['vix_spike'] = 0
        
        # Yield curve (if available)
        if 'treasury_10y' in df.columns and 'treasury_2y' in df.columns:
            df['yield_curve'] = df['treasury_10y'] - df['treasury_2y']
            df['yield_curve_inverted'] = (df['yield_curve'] < 0).astype(int)
        else:
            df['yield_curve'] = 1.0  # Default positive curve
            df['yield_curve_inverted'] = 0
        
        # Drawdown
        df['cummax'] = df['close'].cummax()
        df['drawdown'] = (df['close'] - df['cummax']) / df['cummax']
        df['max_drawdown_60'] = df['drawdown'].rolling(60).min()
        
        # Feature list
        self.feature_names = [
            'returns', 'volatility_20', 'volatility_60',
            'price_above_ma50', 'price_above_ma200', 'ma50_above_ma200',
            'rsi_14', 'momentum_10', 'momentum_20',
            'volume_ratio', 'vix', 'vix_spike',
            'yield_curve', 'yield_curve_inverted',
            'drawdown', 'max_drawdown_60'
        ]
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def create_labels(self, data: pd.DataFrame) -> pd.Series:
        """
        Create regime labels based on heuristic rules
        (Used for initial training data generation)
        
        Args:
            data: DataFrame with features
            
        Returns:
            Series with regime labels (0-4)
        """
        labels = pd.Series(2, index=data.index)  # Default: SIDEWAYS
        
        # BULL: Low VIX, uptrend, positive momentum
        bull_mask = (
            (data['vix'] < 15) &
            (data['ma50_above_ma200'] == 1) &
            (data['price_above_ma50'] == 1) &
            (data['momentum_20'] > 0.05)
        )
        labels[bull_mask] = 0
        
        # BEAR: Elevated VIX, downtrend, negative momentum
        bear_mask = (
            (data['vix'] > 20) &
            (data['vix'] < 30) &
            (data['ma50_above_ma200'] == 0) &
            (data['momentum_20'] < -0.05)
        )
        labels[bear_mask] = 1
        
        # CRISIS: Extreme VIX, large drawdown
        crisis_mask = (
            (data['vix'] > 30) |
            (data['max_drawdown_60'] < -0.15)
        )
        labels[crisis_mask] = 3
        
        # RECOVERY: VIX declining from high, positive momentum after crisis
        recovery_mask = (
            (data['vix'] > 20) &
            (data['vix'] < 30) &
            (data['momentum_10'] > 0.03) &
            (data['max_drawdown_60'] < -0.10)
        )
        labels[recovery_mask] = 4
        
        return labels
    
    def train(self, data: pd.DataFrame, labels: Optional[pd.Series] = None):
        """
        Train the regime detection model
        
        Args:
            data: DataFrame with market data
            labels: Optional pre-labeled regimes. If None, will create heuristic labels
        """
        self.logger.info("Training Regime Detector...")
        
        # Extract features
        df_features = self.extract_features(data)
        
        # Create labels if not provided
        if labels is None:
            labels = self.create_labels(df_features)
            self.logger.info("Generated heuristic labels for training")
        
        # Prepare training data
        X = df_features[self.feature_names].dropna()
        y = labels.loc[X.index]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        self.logger.info(f"Training complete - Train accuracy: {train_score:.3f}, Test accuracy: {test_score:.3f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        self.logger.info(f"Top 5 features:\n{feature_importance.head()}")
    
    def predict(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict regime for new data
        
        Args:
            data: DataFrame with market data
            
        Returns:
            (predictions, probabilities)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Extract features
        df_features = self.extract_features(data)
        X = df_features[self.feature_names].dropna()
        
        # Scale
        X_scaled = self.scaler.transform(X)
        
        # Predict
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)
        
        return predictions, probabilities
    
    def predict_single(self, features: Dict[str, float]) -> Tuple[str, float, Dict[str, float]]:
        """
        Predict regime for a single observation
        
        Args:
            features: Dictionary with feature values
            
        Returns:
            (regime_name, confidence, class_probabilities)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Create feature vector
        X = np.array([[features.get(f, 0.0) for f in self.feature_names]])
        
        # Scale
        X_scaled = self.scaler.transform(X)
        
        # Predict
        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]
        
        regime_name = self.class_names[prediction]
        confidence = probabilities[prediction]
        
        class_probs = {
            self.class_names[i]: float(probabilities[i])
            for i in range(len(self.class_names))
        }
        
        return regime_name, confidence, class_probs
    
    def save_model(self, path: str):
        """Save trained model to disk"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'class_names': self.class_names
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        self.logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load trained model from disk"""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.class_names = model_data['class_names']
        
        self.logger.info(f"Model loaded from {path}")
