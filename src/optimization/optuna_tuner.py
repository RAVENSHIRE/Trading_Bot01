"""
Optuna-based Hyperparameter Optimization for Trading Signals
"""

import logging
from pathlib import Path
from typing import Callable, Dict, Any, Optional, List, Tuple
from datetime import datetime

import numpy as np
import pandas as pd
import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler

logger = logging.getLogger(__name__)


class SignalOptimizer:
    """Optimize trading signal parameters using Optuna"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = f"sqlite:///{Path(__file__).parent.parent.parent / 'database' / 'optuna' / 'optuna.db'}"
        
        self.db_path = db_path
        self.storage = optuna.storages.RDBStorage(url=db_path)
        logger.info(f"Initialized Optuna with storage: {db_path}")
    
    def create_study(
        self,
        study_name: str,
        direction: str = "maximize",
        load_if_exists: bool = True
    ) -> optuna.Study:
        """
        Create or load an Optuna study
        
        Args:
            study_name: Name of the study
            direction: 'maximize' or 'minimize'
            load_if_exists: Load existing study if exists
            
        Returns:
            optuna.Study object
        """
        sampler = TPESampler(seed=42)
        pruner = MedianPruner()
        
        study = optuna.create_study(
            study_name=study_name,
            storage=self.storage,
            sampler=sampler,
            pruner=pruner,
            direction=direction,
            load_if_exists=load_if_exists
        )
        
        logger.info(f"Created study: {study_name} (direction={direction})")
        return study
    
    def optimize_momentum_signal(
        self,
        price_data: pd.DataFrame,
        n_trials: int = 100
    ) -> Tuple[Dict[str, float], float]:
        """
        Optimize momentum signal parameters
        
        Args:
            price_data: DataFrame with OHLCV data
            n_trials: Number of optimization trials
            
        Returns:
            Tuple of (best_params, best_sharpe)
        """
        study = self.create_study("momentum_optimization")
        
        def objective(trial: optuna.Trial) -> float:
            # Parameters to optimize
            fast_ma = trial.suggest_int('fast_ma', 5, 20)
            slow_ma = trial.suggest_int('slow_ma', 20, 100)
            rsi_period = trial.suggest_int('rsi_period', 10, 30)
            rsi_threshold = trial.suggest_float('rsi_threshold', 30, 70)
            
            # Ensure fast < slow
            if fast_ma >= slow_ma:
                return -1.0  # Invalid params
            
            # Calculate momentum signal
            price_data['fast_ma'] = price_data['close'].rolling(fast_ma).mean()
            price_data['slow_ma'] = price_data['close'].rolling(slow_ma).mean()
            
            # Calculate RSI
            delta = price_data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / (loss + 1e-10)
            price_data['rsi'] = 100 - (100 / (1 + rs))
            
            # Generate signals
            price_data['signal'] = (
                (price_data['fast_ma'] > price_data['slow_ma']).astype(int) &
                (price_data['rsi'] > rsi_threshold).astype(int)
            )
            
            # Calculate returns
            price_data['returns'] = price_data['close'].pct_change()
            price_data['strategy_returns'] = price_data['signal'].shift(1) * price_data['returns']
            
            # Calculate Sharpe ratio
            sharpe = price_data['strategy_returns'].mean() / (price_data['strategy_returns'].std() + 1e-10) * np.sqrt(252)
            
            # Report intermediate values for pruning
            trial.report(sharpe, step=len(price_data))
            
            return sharpe
        
        # Run optimization
        study.optimize(objective, n_trials=n_trials)
        
        best_params = study.best_params
        best_value = study.best_value
        
        logger.info(f"Momentum optimization complete. Best Sharpe: {best_value:.4f}")
        logger.info(f"Best parameters: {best_params}")
        
        return best_params, best_value
    
    def optimize_mean_reversion_signal(
        self,
        price_data: pd.DataFrame,
        n_trials: int = 100
    ) -> Tuple[Dict[str, float], float]:
        """
        Optimize mean reversion signal parameters
        
        Args:
            price_data: DataFrame with OHLCV data
            n_trials: Number of optimization trials
            
        Returns:
            Tuple of (best_params, best_sharpe)
        """
        study = self.create_study("mean_reversion_optimization")
        
        def objective(trial: optuna.Trial) -> float:
            # Parameters to optimize
            lookback = trial.suggest_int('lookback', 10, 50)
            z_score_threshold = trial.suggest_float('z_score_threshold', 1.0, 3.0)
            atr_period = trial.suggest_int('atr_period', 10, 20)
            
            # Calculate z-score
            rolling_mean = price_data['close'].rolling(lookback).mean()
            rolling_std = price_data['close'].rolling(lookback).std()
            z_score = (price_data['close'] - rolling_mean) / (rolling_std + 1e-10)
            
            # Calculate ATR for stops
            high_low = price_data['high'] - price_data['low']
            high_close = np.abs(price_data['high'] - price_data['close'].shift())
            low_close = np.abs(price_data['low'] - price_data['close'].shift())
            
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(atr_period).mean()
            
            # Generate signals (extreme deviations)
            price_data['signal'] = (
                (np.abs(z_score) > z_score_threshold).astype(int) *
                np.sign(z_score) * -1  # Reverse signal for mean reversion
            )
            
            # Calculate returns
            price_data['returns'] = price_data['close'].pct_change()
            price_data['strategy_returns'] = price_data['signal'].shift(1) * price_data['returns']
            
            # Calculate Sharpe ratio
            sharpe = price_data['strategy_returns'].mean() / (price_data['strategy_returns'].std() + 1e-10) * np.sqrt(252)
            
            trial.report(sharpe, step=len(price_data))
            return sharpe
        
        study.optimize(objective, n_trials=n_trials)
        
        best_params = study.best_params
        best_value = study.best_value
        
        logger.info(f"Mean reversion optimization complete. Best Sharpe: {best_value:.4f}")
        logger.info(f"Best parameters: {best_params}")
        
        return best_params, best_value
    
    def optimize_custom_signal(
        self,
        objective_func: Callable,
        param_grid: Dict[str, Tuple],
        n_trials: int = 100,
        study_name: str = "custom_optimization"
    ) -> Tuple[Dict[str, Any], float]:
        """
        Optimize custom signal with user-defined objective function
        
        Args:
            objective_func: Function that takes trial and returns fitness score
            param_grid: Dict with parameter ranges
            n_trials: Number of trials
            study_name: Name of the study
            
        Returns:
            Tuple of (best_params, best_score)
        """
        study = self.create_study(study_name)
        
        def trial_objective(trial: optuna.Trial) -> float:
            return objective_func(trial, param_grid)
        
        study.optimize(trial_objective, n_trials=n_trials)
        
        logger.info(f"Custom optimization complete. Best score: {study.best_value:.4f}")
        
        return study.best_params, study.best_value
    
    def get_study_results(self, study_name: str) -> pd.DataFrame:
        """Retrieve optimization results as DataFrame"""
        try:
            study = optuna.load_study(study_name=study_name, storage=self.storage)
            trials_data = []
            
            for trial in study.trials:
                trials_data.append({
                    'trial_id': trial.number,
                    'value': trial.value,
                    'params': trial.params,
                    'state': trial.state.name,
                    'datetime_start': trial.datetime_start,
                    'datetime_complete': trial.datetime_complete
                })
            
            return pd.DataFrame(trials_data)
        except Exception as e:
            logger.error(f"Error loading study {study_name}: {e}")
            return pd.DataFrame()
    
    def list_studies(self) -> List[str]:
        """List all available studies"""
        return optuna.study.get_all_study_names(self.storage)
    
    def export_results(self, study_name: str, output_path: str):
        """Export optimization results to CSV"""
        df = self.get_study_results(study_name)
        df.to_csv(output_path, index=False)
        logger.info(f"Exported results to {output_path}")


class ParameterTuner:
    """High-level parameter tuning interface"""
    
    def __init__(self):
        self.optimizer = SignalOptimizer()
    
    def tune_signal_parameters(
        self,
        signal_type: str,
        price_data: pd.DataFrame,
        n_trials: int = 100
    ) -> Dict[str, float]:
        """
        Main entry point for parameter tuning
        
        Args:
            signal_type: 'momentum', 'mean_reversion', or 'custom'
            price_data: Historical price data
            n_trials: Number of trials
            
        Returns:
            Dictionary of optimized parameters
        """
        if signal_type == "momentum":
            params, sharpe = self.optimizer.optimize_momentum_signal(price_data, n_trials)
            params['best_sharpe'] = sharpe
            return params
        
        elif signal_type == "mean_reversion":
            params, sharpe = self.optimizer.optimize_mean_reversion_signal(price_data, n_trials)
            params['best_sharpe'] = sharpe
            return params
        
        else:
            logger.error(f"Unknown signal type: {signal_type}")
            return {}


if __name__ == "__main__":
    # Example: Generate sample data and optimize
    dates = pd.date_range('2023-01-01', periods=252)
    sample_price = 100 + np.cumsum(np.random.randn(252) * 2)
    
    df = pd.DataFrame({
        'date': dates,
        'close': sample_price,
        'high': sample_price + np.abs(np.random.randn(252)),
        'low': sample_price - np.abs(np.random.randn(252)),
        'volume': np.random.randint(1000000, 10000000, 252)
    })
    
    tuner = ParameterTuner()
    
    print("Optimizing momentum signal...")
    momentum_params = tuner.tune_signal_parameters("momentum", df, n_trials=20)
    print(f"Best parameters: {momentum_params}")
