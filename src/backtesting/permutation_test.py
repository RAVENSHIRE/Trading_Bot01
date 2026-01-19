"""Permutation testing for statistical significance"""

import numpy as np
import pandas as pd
from typing import Dict


class PermutationTester:
    """Test strategy robustness using permutation analysis"""
    
    @staticmethod
    def test_significance(returns: pd.Series, num_permutations: int = 1000) -> Dict:
        """Test if returns are statistically significant"""
        original_mean = returns.mean()
        
        permuted_means = []
        for _ in range(num_permutations):
            permuted = np.random.permutation(returns)
            permuted_means.append(permuted.mean())
        
        permuted_means = np.array(permuted_means)
        p_value = (permuted_means >= original_mean).sum() / num_permutations
        
        return {
            'original_mean': original_mean,
            'permutation_mean': permuted_means.mean(),
            'p_value': p_value,
            'significant': p_value < 0.05,
            'percentile': (permuted_means < original_mean).sum() / num_permutations * 100
        }
    
    @staticmethod
    def test_strategy_robustness(returns: pd.Series, num_variations: int = 100) -> Dict:
        """Test strategy robustness with small parameter variations"""
        returns_list = []
        
        for _ in range(num_variations):
            # Add small noise to simulate parameter variations
            noise = np.random.normal(0, 0.01, len(returns))
            perturbed_returns = returns + noise
            returns_list.append(perturbed_returns.mean())
        
        returns_list = np.array(returns_list)
        
        return {
            'mean_return': returns_list.mean(),
            'std_return': returns_list.std(),
            'robust': returns_list.std() < returns_list.mean() * 0.5
        }
