"""
Asset Clustering - K-Means based grouping of assets by behavior
Groups stocks based on returns, volatility, and correlation patterns
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import logging


class AssetClusterer:
    """
    K-Means clustering for asset behavior grouping
    
    Features per asset:
    - Mean return
    - Volatility (std dev)
    - Sharpe ratio
    - Max drawdown
    - Beta (vs market)
    - Correlation with market
    """
    
    def __init__(self, n_clusters: int = 5):
        self.logger = logging.getLogger("aegis.ml.clustering")
        self.n_clusters = n_clusters
        self.model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.scaler = StandardScaler()
        self.pca: Optional[PCA] = None
        self.feature_names: List[str] = []
        self.cluster_labels: Optional[np.ndarray] = None
        self.cluster_centers: Optional[np.ndarray] = None
        
        self.logger.info(f"Asset Clusterer initialized with {n_clusters} clusters")
    
    def extract_features(
        self, 
        returns_df: pd.DataFrame,
        market_returns: Optional[pd.Series] = None
    ) -> pd.DataFrame:
        """
        Extract clustering features from returns data
        
        Args:
            returns_df: DataFrame with returns for each asset (columns = symbols)
            market_returns: Optional Series with market returns for beta calculation
            
        Returns:
            DataFrame with features per asset
        """
        features = {}
        
        for symbol in returns_df.columns:
            asset_returns = returns_df[symbol].dropna()
            
            if len(asset_returns) < 20:
                self.logger.warning(f"Insufficient data for {symbol}, skipping")
                continue
            
            # Basic statistics
            mean_return = asset_returns.mean()
            volatility = asset_returns.std()
            sharpe = mean_return / volatility if volatility > 0 else 0
            
            # Drawdown
            cumulative = (1 + asset_returns).cumprod()
            running_max = cumulative.cummax()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # Skewness and kurtosis
            skewness = asset_returns.skew()
            kurtosis = asset_returns.kurtosis()
            
            # Win rate
            win_rate = (asset_returns > 0).sum() / len(asset_returns)
            
            # Beta and correlation (if market returns provided)
            if market_returns is not None:
                aligned_returns = asset_returns.align(market_returns, join='inner')
                asset_aligned = aligned_returns[0]
                market_aligned = aligned_returns[1]
                
                if len(asset_aligned) > 0:
                    covariance = np.cov(asset_aligned, market_aligned)[0, 1]
                    market_variance = market_aligned.var()
                    beta = covariance / market_variance if market_variance > 0 else 1.0
                    correlation = asset_aligned.corr(market_aligned)
                else:
                    beta = 1.0
                    correlation = 0.0
            else:
                beta = 1.0
                correlation = 0.0
            
            # Recent momentum
            momentum_20 = asset_returns.tail(20).sum()
            momentum_60 = asset_returns.tail(60).sum()
            
            features[symbol] = {
                'mean_return': mean_return,
                'volatility': volatility,
                'sharpe': sharpe,
                'max_drawdown': max_drawdown,
                'skewness': skewness,
                'kurtosis': kurtosis,
                'win_rate': win_rate,
                'beta': beta,
                'correlation': correlation,
                'momentum_20': momentum_20,
                'momentum_60': momentum_60
            }
        
        df_features = pd.DataFrame(features).T
        self.feature_names = df_features.columns.tolist()
        
        return df_features
    
    def fit(self, returns_df: pd.DataFrame, 
            market_returns: Optional[pd.Series] = None,
            use_pca: bool = False,
            n_components: int = 3):
        """
        Fit K-Means clustering model
        
        Args:
            returns_df: DataFrame with returns for each asset
            market_returns: Optional market returns for beta calculation
            use_pca: Whether to use PCA for dimensionality reduction
            n_components: Number of PCA components if use_pca=True
        """
        self.logger.info("Fitting clustering model...")
        
        # Extract features
        features_df = self.extract_features(returns_df, market_returns)
        
        if len(features_df) < self.n_clusters:
            self.logger.error(
                f"Insufficient assets ({len(features_df)}) for {self.n_clusters} clusters"
            )
            return
        
        # Scale features
        X_scaled = self.scaler.fit_transform(features_df)
        
        # Optional PCA
        if use_pca:
            self.pca = PCA(n_components=n_components)
            X_scaled = self.pca.fit_transform(X_scaled)
            explained_var = self.pca.explained_variance_ratio_.sum()
            self.logger.info(f"PCA: {explained_var:.2%} variance explained")
        
        # Fit K-Means
        self.model.fit(X_scaled)
        self.cluster_labels = self.model.labels_
        self.cluster_centers = self.model.cluster_centers_
        
        # Calculate inertia (within-cluster sum of squares)
        inertia = self.model.inertia_
        
        self.logger.info(f"Clustering complete - Inertia: {inertia:.2f}")
        
        # Log cluster sizes
        unique, counts = np.unique(self.cluster_labels, return_counts=True)
        for cluster_id, count in zip(unique, counts):
            self.logger.info(f"Cluster {cluster_id}: {count} assets")
    
    def predict(self, returns_df: pd.DataFrame,
                market_returns: Optional[pd.Series] = None) -> np.ndarray:
        """
        Predict cluster assignments for new assets
        
        Args:
            returns_df: DataFrame with returns for each asset
            market_returns: Optional market returns
            
        Returns:
            Array of cluster labels
        """
        # Extract features
        features_df = self.extract_features(returns_df, market_returns)
        
        # Scale
        X_scaled = self.scaler.transform(features_df)
        
        # Optional PCA
        if self.pca is not None:
            X_scaled = self.pca.transform(X_scaled)
        
        # Predict
        labels = self.model.predict(X_scaled)
        
        return labels
    
    def get_cluster_assignments(self, symbols: List[str]) -> Dict[str, int]:
        """
        Get cluster assignments for symbols
        
        Args:
            symbols: List of asset symbols
            
        Returns:
            Dictionary mapping symbol to cluster ID
        """
        if self.cluster_labels is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        return {
            symbol: int(label)
            for symbol, label in zip(symbols, self.cluster_labels)
        }
    
    def get_cluster_members(self, cluster_id: int, 
                           symbols: List[str]) -> List[str]:
        """
        Get all symbols in a specific cluster
        
        Args:
            cluster_id: Cluster ID
            symbols: List of all symbols
            
        Returns:
            List of symbols in the cluster
        """
        if self.cluster_labels is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        return [
            symbol for symbol, label in zip(symbols, self.cluster_labels)
            if label == cluster_id
        ]
    
    def get_cluster_characteristics(
        self, 
        features_df: pd.DataFrame
    ) -> Dict[int, Dict[str, float]]:
        """
        Get average characteristics for each cluster
        
        Args:
            features_df: DataFrame with features
            
        Returns:
            Dictionary mapping cluster ID to average feature values
        """
        if self.cluster_labels is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        features_df['cluster'] = self.cluster_labels
        
        cluster_chars = {}
        for cluster_id in range(self.n_clusters):
            cluster_data = features_df[features_df['cluster'] == cluster_id]
            
            if len(cluster_data) > 0:
                cluster_chars[cluster_id] = {
                    'mean_return': cluster_data['mean_return'].mean(),
                    'volatility': cluster_data['volatility'].mean(),
                    'sharpe': cluster_data['sharpe'].mean(),
                    'beta': cluster_data['beta'].mean(),
                    'count': len(cluster_data)
                }
        
        return cluster_chars
    
    def get_cluster_names(
        self, 
        cluster_chars: Dict[int, Dict[str, float]]
    ) -> Dict[int, str]:
        """
        Assign descriptive names to clusters based on characteristics
        
        Args:
            cluster_chars: Cluster characteristics from get_cluster_characteristics()
            
        Returns:
            Dictionary mapping cluster ID to descriptive name
        """
        cluster_names = {}
        
        for cluster_id, chars in cluster_chars.items():
            sharpe = chars.get('sharpe', 0)
            volatility = chars.get('volatility', 0)
            beta = chars.get('beta', 1)
            
            # Name based on characteristics
            if sharpe > 1.5 and volatility < 0.02:
                name = "Low-Vol Winners"
            elif sharpe > 1.0:
                name = "High Performers"
            elif beta > 1.5:
                name = "High-Beta Growth"
            elif beta < 0.5:
                name = "Defensive"
            elif volatility > 0.03:
                name = "High Volatility"
            else:
                name = "Moderate"
            
            cluster_names[cluster_id] = name
        
        return cluster_names
    
    def visualize_clusters_2d(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Get 2D coordinates for cluster visualization
        
        Args:
            features_df: DataFrame with features
            
        Returns:
            DataFrame with x, y coordinates and cluster labels
        """
        if self.cluster_labels is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Scale features
        X_scaled = self.scaler.transform(features_df)
        
        # PCA to 2D
        pca_2d = PCA(n_components=2)
        coords_2d = pca_2d.fit_transform(X_scaled)
        
        viz_df = pd.DataFrame({
            'x': coords_2d[:, 0],
            'y': coords_2d[:, 1],
            'cluster': self.cluster_labels,
            'symbol': features_df.index
        })
        
        return viz_df
