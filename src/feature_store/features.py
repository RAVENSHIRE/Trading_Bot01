"""
Feature Store - Feature Engineering and Management
Handles feature creation, caching, and versioning
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime
import pickle

import pandas as pd
import numpy as np
from functools import wraps

logger = logging.getLogger(__name__)


class FeatureStore:
    """Centralized feature management system"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / "database" / "cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.features: Dict[str, pd.DataFrame] = {}
        self.feature_metadata: Dict[str, Dict] = {}
        logger.info(f"FeatureStore initialized with cache: {cache_dir}")
    
    def register_feature(
        self,
        name: str,
        feature_df: pd.DataFrame,
        version: str = "1.0",
        description: str = ""
    ):
        """Register a feature with metadata"""
        self.features[name] = feature_df
        self.feature_metadata[name] = {
            'version': version,
            'created_date': datetime.now(),
            'description': description,
            'shape': feature_df.shape
        }
        logger.info(f"Registered feature: {name} (shape: {feature_df.shape})")
    
    def get_feature(self, name: str) -> Optional[pd.DataFrame]:
        """Retrieve a cached feature"""
        if name in self.features:
            return self.features[name]
        
        # Try loading from cache
        cache_file = self.cache_dir / f"{name}.parquet"
        if cache_file.exists():
            logger.info(f"Loading feature from cache: {name}")
            return pd.read_parquet(cache_file)
        
        logger.warning(f"Feature not found: {name}")
        return None
    
    def cache_feature(self, name: str, force: bool = False) -> bool:
        """Cache a registered feature to disk"""
        if name not in self.features:
            logger.error(f"Feature not found for caching: {name}")
            return False
        
        cache_file = self.cache_dir / f"{name}.parquet"
        
        if cache_file.exists() and not force:
            logger.info(f"Feature already cached: {name}")
            return True
        
        try:
            self.features[name].to_parquet(cache_file)
            logger.info(f"Cached feature to {cache_file.name}")
            return True
        except Exception as e:
            logger.error(f"Error caching feature {name}: {e}")
            return False
    
    def list_features(self) -> List[str]:
        """List all available features"""
        return list(self.features.keys())
    
    def get_metadata(self, name: str) -> Dict:
        """Get feature metadata"""
        return self.feature_metadata.get(name, {})


class TechnicalFeatures:
    """Generate technical analysis features"""
    
    @staticmethod
    def moving_average(data: pd.Series, period: int, name: str = None) -> pd.Series:
        """Simple moving average"""
        ma = data.rolling(window=period).mean()
        if name:
            ma.name = f"{name}_MA{period}"
        return ma
    
    @staticmethod
    def exponential_moving_average(data: pd.Series, period: int, name: str = None) -> pd.Series:
        """Exponential moving average"""
        ema = data.ewm(span=period, adjust=False).mean()
        if name:
            ema.name = f"{name}_EMA{period}"
        return ema
    
    @staticmethod
    def relative_strength_index(data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index (RSI)"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        rsi.name = f"RSI{period}"
        return rsi
    
    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            f"BB_UPPER_{period}": upper_band,
            f"BB_MIDDLE_{period}": sma,
            f"BB_LOWER_{period}": lower_band,
            f"BB_WIDTH_{period}": upper_band - lower_band
        }
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'MACD': macd_line,
            'MACD_SIGNAL': signal_line,
            'MACD_HISTOGRAM': histogram
        }
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range"""
        tr1 = high - low
        tr2 = np.abs(high - close.shift())
        tr3 = np.abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        atr.name = f"ATR{period}"
        return atr
    
    @staticmethod
    def momentum(data: pd.Series, period: int = 10) -> pd.Series:
        """Momentum indicator"""
        momentum = data - data.shift(period)
        momentum.name = f"MOMENTUM{period}"
        return momentum
    
    @staticmethod
    def rate_of_change(data: pd.Series, period: int = 12) -> pd.Series:
        """Rate of Change"""
        roc = ((data - data.shift(period)) / data.shift(period)) * 100
        roc.name = f"ROC{period}"
        return roc
    
    @staticmethod
    def volume_features(volume: pd.Series, period: int = 20) -> Dict[str, pd.Series]:
        """Volume-based features"""
        vol_ma = volume.rolling(window=period).mean()
        vol_ratio = volume / vol_ma
        
        return {
            f'VOLUME_MA{period}': vol_ma,
            f'VOLUME_RATIO{period}': vol_ratio,
            'VOLUME_ZSCORE': (volume - vol_ma) / volume.rolling(window=period).std()
        }


class FundamentalFeatures:
    """Generate fundamental analysis features"""
    
    @staticmethod
    def value_metrics(data: Dict[str, float]) -> Dict[str, float]:
        """Calculate value-based metrics"""
        features = {}
        
        if 'pe_ratio' in data:
            features['PE_INVERSE'] = 1 / (data['pe_ratio'] + 0.01)  # Earnings yield proxy
        
        if 'pb_ratio' in data:
            features['PB_INVERSE'] = 1 / (data['pb_ratio'] + 0.01)
        
        if 'debt_equity' in data:
            features['LEVERAGE'] = data['debt_equity']
            features['SOLVENCY'] = 1 / (data['debt_equity'] + 0.01)
        
        return features
    
    @staticmethod
    def growth_metrics(fundamentals_ts: pd.DataFrame) -> Dict[str, float]:
        """Calculate growth metrics from time series data"""
        features = {}
        
        # Revenue growth
        if 'revenue' in fundamentals_ts.columns:
            features['REVENUE_GROWTH'] = fundamentals_ts['revenue'].pct_change().mean()
        
        # Earnings growth
        if 'earnings' in fundamentals_ts.columns:
            features['EARNINGS_GROWTH'] = fundamentals_ts['earnings'].pct_change().mean()
        
        # Dividend growth
        if 'dividend' in fundamentals_ts.columns:
            features['DIVIDEND_GROWTH'] = fundamentals_ts['dividend'].pct_change().mean()
        
        return features
    
    @staticmethod
    def profitability_metrics(data: Dict[str, float]) -> Dict[str, float]:
        """Calculate profitability metrics"""
        features = {}
        
        if 'roe' in data:
            features['ROE'] = data['roe']
        
        if 'roa' in data:
            features['ROA'] = data['roa']
        
        if 'margin' in data:
            features['MARGIN'] = data['margin']
        
        return features


class FeatureEngineering:
    """Main feature engineering pipeline"""
    
    def __init__(self):
        self.feature_store = FeatureStore()
        self.tech_features = TechnicalFeatures()
        self.fund_features = FundamentalFeatures()
    
    def create_price_features(self, ohlcv: pd.DataFrame) -> pd.DataFrame:
        """Create technical features from OHLCV data"""
        features = pd.DataFrame(index=ohlcv.index)
        
        # Moving averages
        features['SMA_20'] = self.tech_features.moving_average(ohlcv['close'], 20)
        features['SMA_50'] = self.tech_features.moving_average(ohlcv['close'], 50)
        features['EMA_12'] = self.tech_features.exponential_moving_average(ohlcv['close'], 12)
        
        # Momentum
        features['RSI_14'] = self.tech_features.relative_strength_index(ohlcv['close'], 14)
        features['MOMENTUM_10'] = self.tech_features.momentum(ohlcv['close'], 10)
        features['ROC_12'] = self.tech_features.rate_of_change(ohlcv['close'], 12)
        
        # Volatility
        features['ATR_14'] = self.tech_features.atr(ohlcv['high'], ohlcv['low'], ohlcv['close'], 14)
        
        # Bollinger Bands
        bb = self.tech_features.bollinger_bands(ohlcv['close'], 20)
        for name, series in bb.items():
            features[name] = series
        
        # MACD
        macd_dict = self.tech_features.macd(ohlcv['close'])
        for name, series in macd_dict.items():
            features[name] = series
        
        # Volume
        if 'volume' in ohlcv.columns:
            vol_features = self.tech_features.volume_features(ohlcv['volume'], 20)
            for name, series in vol_features.items():
                features[name] = series
        
        # Price-based features
        features['CLOSE_SMA20_RATIO'] = ohlcv['close'] / features['SMA_20']
        features['HIGH_LOW_RANGE'] = (ohlcv['high'] - ohlcv['low']) / ohlcv['close']
        
        # Register features
        self.feature_store.register_feature('price_features', features, description='Technical analysis features')
        
        return features
    
    def create_fundamental_features(self, fundamentals: Dict) -> Dict[str, float]:
        """Create fundamental features"""
        features = {}
        
        # Value metrics
        features.update(self.fund_features.value_metrics(fundamentals))
        
        # Profitability metrics
        features.update(self.fund_features.profitability_metrics(fundamentals))
        
        return features
    
    def cache_all_features(self):
        """Cache all features to disk"""
        for feature_name in self.feature_store.list_features():
            self.feature_store.cache_feature(feature_name)
            logger.info(f"Cached feature: {feature_name}")


if __name__ == "__main__":
    # Example usage
    dates = pd.date_range('2023-01-01', periods=252)
    sample_ohlcv = pd.DataFrame({
        'date': dates,
        'open': 100 + np.cumsum(np.random.randn(252) * 2),
        'high': 102 + np.cumsum(np.random.randn(252) * 2),
        'low': 98 + np.cumsum(np.random.randn(252) * 2),
        'close': 100 + np.cumsum(np.random.randn(252) * 2),
        'volume': np.random.randint(1000000, 10000000, 252)
    })
    
    fe = FeatureEngineering()
    features = fe.create_price_features(sample_ohlcv)
    
    print("Price features shape:", features.shape)
    print("\nFeature columns:")
    print(features.columns.tolist())
    print("\nFirst few rows:")
    print(features.head())
