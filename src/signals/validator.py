"""Signal validation and robustness testing"""

from typing import Dict, List, Optional
from .signal_generator import Signal, SignalType
import pandas as pd


class SignalValidator:
    """Validate signal robustness and statistical significance"""
    
    def __init__(self):
        self.validation_results: Dict = {}
    
    def walk_forward_validate(self, returns: pd.Series, 
                             window_size: int = 252,
                             step_size: int = 63) -> Dict:
        """Walk-forward validation"""
        results = {
            'periods': [],
            'sharpe_ratios': [],
            'win_rates': [],
            'max_drawdowns': []
        }
        
        for i in range(0, len(returns) - window_size, step_size):
            window = returns.iloc[i:i + window_size]
            
            # Calculate metrics
            sharpe = (window.mean() / window.std()) * (252 ** 0.5) if window.std() != 0 else 0
            win_rate = (window > 0).sum() / len(window) if len(window) > 0 else 0
            
            cumulative = (1 + window).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_dd = drawdown.min()
            
            results['periods'].append(i)
            results['sharpe_ratios'].append(sharpe)
            results['win_rates'].append(win_rate)
            results['max_drawdowns'].append(max_dd)
        
        return results
    
    def permutation_test(self, returns: pd.Series, num_permutations: int = 1000) -> Dict:
        """Permutation test for statistical significance"""
        import numpy as np
        
        original_mean = returns.mean()
        permuted_means = []
        
        for _ in range(num_permutations):
            permuted = np.random.permutation(returns)
            permuted_means.append(permuted.mean())
        
        permuted_means = pd.Series(permuted_means)
        p_value = (permuted_means >= original_mean).sum() / num_permutations
        
        return {
            'original_mean': original_mean,
            'permutation_mean': permuted_means.mean(),
            'p_value': p_value,
            'significant': p_value < 0.05
        }
    
    def correlation_analysis(self, signal_returns: pd.Series, 
                            benchmark_returns: pd.Series) -> Dict:
        """Analyze signal correlation with benchmark"""
        correlation = signal_returns.corr(benchmark_returns)
        
        return {
            'correlation': correlation,
            'is_uncorrelated': abs(correlation) < 0.3,
            'signal_std': signal_returns.std(),
            'benchmark_std': benchmark_returns.std()
        }
