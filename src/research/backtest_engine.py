"""
Research Layer - Backtesting and Strategy Research
Part of the 5-Layer Hedge Fund Architecture
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime
import json

try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Represents backtest results"""
    strategy_name: str
    parameters: Dict[str, Any]
    start_date: str
    end_date: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_trades: int
    trades: List[Dict[str, Any]]
    equity_curve: pd.Series
    daily_returns: pd.Series
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "strategy_name": self.strategy_name,
            "parameters": self.parameters,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "total_return": self.total_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "num_trades": self.num_trades
        }


class PerformanceCalculator:
    """Calculates performance metrics"""
    
    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe Ratio
        
        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Sharpe Ratio
        """
        excess_returns = returns - (risk_free_rate / 252)
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    
    @staticmethod
    def calculate_max_drawdown(equity_curve: pd.Series) -> float:
        """
        Calculate maximum drawdown
        
        Args:
            equity_curve: Series of portfolio values
            
        Returns:
            Maximum drawdown (negative value)
        """
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max
        return drawdown.min()
    
    @staticmethod
    def calculate_calmar_ratio(
        returns: pd.Series,
        equity_curve: pd.Series
    ) -> float:
        """Calculate Calmar Ratio (Return / Max Drawdown)"""
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        max_dd = abs(PerformanceCalculator.calculate_max_drawdown(equity_curve))
        
        if max_dd == 0:
            return 0
        
        return total_return / max_dd
    
    @staticmethod
    def calculate_win_rate(trades: List[Dict[str, Any]]) -> float:
        """Calculate win rate"""
        if len(trades) == 0:
            return 0
        
        winning_trades = sum(1 for t in trades if t.get("pnl", 0) > 0)
        return winning_trades / len(trades)


class BacktestRunner:
    """Runs backtests on strategies"""
    
    def __init__(self, use_mlflow: bool = True):
        self.use_mlflow = use_mlflow and MLFLOW_AVAILABLE
        if self.use_mlflow:
            mlflow.set_tracking_uri("http://localhost:5000")
    
    def run_backtest(
        self,
        strategy_func: Callable,
        data: pd.DataFrame,
        parameters: Dict[str, Any],
        strategy_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> BacktestResult:
        """
        Run a backtest
        
        Args:
            strategy_func: Function that returns signals
            data: OHLCV data
            parameters: Strategy parameters
            strategy_name: Name of strategy
            start_date: Start date for backtest
            end_date: End date for backtest
            
        Returns:
            BacktestResult
        """
        if self.use_mlflow:
            mlflow.start_run()
            mlflow.set_tag("strategy", strategy_name)
            mlflow.log_params(parameters)
        
        try:
            # Filter data by date range
            if start_date:
                data = data[data.index >= start_date]
            if end_date:
                data = data[data.index <= end_date]
            
            start_date = str(data.index[0].date())
            end_date = str(data.index[-1].date())
            
            # Generate signals
            signals = strategy_func(data, **parameters)
            
            # Calculate returns
            returns = data['Close'].pct_change()
            strategy_returns = returns * signals.shift(1)
            
            # Calculate equity curve
            equity_curve = (1 + strategy_returns).cumprod()
            
            # Calculate metrics
            total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
            sharpe_ratio = PerformanceCalculator.calculate_sharpe_ratio(strategy_returns)
            max_drawdown = PerformanceCalculator.calculate_max_drawdown(equity_curve)
            
            # Generate trades
            trades = self._generate_trades(signals, data, strategy_returns)
            win_rate = PerformanceCalculator.calculate_win_rate(trades)
            
            # Create result
            result = BacktestResult(
                strategy_name=strategy_name,
                parameters=parameters,
                start_date=start_date,
                end_date=end_date,
                total_return=total_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                num_trades=len(trades),
                trades=trades,
                equity_curve=equity_curve,
                daily_returns=strategy_returns
            )
            
            # Log to MLflow
            if self.use_mlflow:
                mlflow.log_metric("total_return", total_return)
                mlflow.log_metric("sharpe_ratio", sharpe_ratio)
                mlflow.log_metric("max_drawdown", max_drawdown)
                mlflow.log_metric("win_rate", win_rate)
                mlflow.log_metric("num_trades", len(trades))
            
            logger.info(f"Backtest complete: {strategy_name}")
            logger.info(f"  Total Return: {total_return:.2%}")
            logger.info(f"  Sharpe Ratio: {sharpe_ratio:.2f}")
            logger.info(f"  Max Drawdown: {max_drawdown:.2%}")
            
            return result
        
        finally:
            if self.use_mlflow:
                mlflow.end_run()
    
    @staticmethod
    def _generate_trades(
        signals: pd.Series,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> List[Dict[str, Any]]:
        """Generate trade list from signals"""
        trades = []
        in_trade = False
        entry_price = None
        entry_date = None
        
        for i in range(1, len(signals)):
            signal = signals.iloc[i]
            prev_signal = signals.iloc[i-1]
            
            # Entry
            if not in_trade and signal == 1 and prev_signal == 0:
                entry_price = data['Close'].iloc[i]
                entry_date = data.index[i]
                in_trade = True
            
            # Exit
            elif in_trade and signal == 0 and prev_signal == 1:
                exit_price = data['Close'].iloc[i]
                exit_date = data.index[i]
                pnl = (exit_price - entry_price) / entry_price
                
                trades.append({
                    "entry_date": str(entry_date),
                    "entry_price": entry_price,
                    "exit_date": str(exit_date),
                    "exit_price": exit_price,
                    "pnl": pnl,
                    "duration_days": (exit_date - entry_date).days
                })
                
                in_trade = False
        
        return trades


class ParameterOptimizer:
    """Optimizes strategy parameters using Optuna"""
    
    def __init__(self, backtest_runner: Optional[BacktestRunner] = None):
        self.backtest_runner = backtest_runner or BacktestRunner()
        
        try:
            import optuna
            self.optuna = optuna
            self.optuna_available = True
        except ImportError:
            self.optuna_available = False
            logger.warning("Optuna not available for parameter optimization")
    
    def optimize(
        self,
        strategy_func: Callable,
        data: pd.DataFrame,
        param_space: Dict[str, tuple],
        strategy_name: str,
        n_trials: int = 50,
        metric: str = "sharpe_ratio"
    ) -> Dict[str, Any]:
        """
        Optimize strategy parameters
        
        Args:
            strategy_func: Strategy function
            data: OHLCV data
            param_space: Parameter space (name: (min, max, step))
            strategy_name: Strategy name
            n_trials: Number of trials
            metric: Metric to optimize (sharpe_ratio, total_return, etc.)
            
        Returns:
            Best parameters and results
        """
        if not self.optuna_available:
            logger.error("Optuna not available")
            return {}
        
        def objective(trial):
            # Sample parameters
            params = {}
            for param_name, (min_val, max_val, step) in param_space.items():
                if isinstance(min_val, int):
                    params[param_name] = trial.suggest_int(param_name, min_val, max_val, step=step)
                else:
                    params[param_name] = trial.suggest_float(param_name, min_val, max_val, step=step)
            
            # Run backtest
            result = self.backtest_runner.run_backtest(
                strategy_func,
                data,
                params,
                strategy_name
            )
            
            # Return metric
            return getattr(result, metric)
        
        # Create study
        study = self.optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials)
        
        best_params = study.best_params
        best_value = study.best_value
        
        logger.info(f"Optimization complete: {strategy_name}")
        logger.info(f"  Best {metric}: {best_value:.4f}")
        logger.info(f"  Best parameters: {best_params}")
        
        return {
            "best_params": best_params,
            "best_value": best_value,
            "metric": metric,
            "n_trials": n_trials
        }


class ResearchManager:
    """Main research interface"""
    
    def __init__(self):
        self.backtest_runner = BacktestRunner(use_mlflow=MLFLOW_AVAILABLE)
        self.optimizer = ParameterOptimizer(self.backtest_runner)
    
    def backtest_strategy(
        self,
        strategy_func: Callable,
        data: pd.DataFrame,
        parameters: Dict[str, Any],
        strategy_name: str
    ) -> BacktestResult:
        """Run a backtest"""
        return self.backtest_runner.run_backtest(
            strategy_func,
            data,
            parameters,
            strategy_name
        )
    
    def optimize_parameters(
        self,
        strategy_func: Callable,
        data: pd.DataFrame,
        param_space: Dict[str, tuple],
        strategy_name: str,
        n_trials: int = 50
    ) -> Dict[str, Any]:
        """Optimize strategy parameters"""
        return self.optimizer.optimize(
            strategy_func,
            data,
            param_space,
            strategy_name,
            n_trials
        )
