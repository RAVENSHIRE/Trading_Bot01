"""
MLflow Databricks Integration
Experiment Tracking, Model Registry, and Managed Hosting
Part of Ravenshire Intelligence Engine
"""

import mlflow
import mlflow.sklearn
import mlflow.pytorch
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """MLflow Experiment Configuration"""
    experiment_name: str
    run_name: str
    tags: Dict[str, str] = None
    params: Dict[str, Any] = None
    description: str = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.params is None:
            self.params = {}


class MLflowDatabricksClient:
    """MLflow Databricks Integration Client"""
    
    def __init__(
        self,
        databricks_host: str = None,
        databricks_token: str = None,
        tracking_uri: str = None
    ):
        """
        Initialize MLflow Databricks Client
        
        Args:
            databricks_host: Databricks workspace URL
            databricks_token: Databricks API token
            tracking_uri: MLflow tracking URI (defaults to Databricks)
        """
        self.databricks_host = databricks_host or os.getenv("DATABRICKS_HOST")
        self.databricks_token = databricks_token or os.getenv("DATABRICKS_TOKEN")
        
        # Set tracking URI to Databricks
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        elif self.databricks_host and self.databricks_token:
            # Use Databricks as tracking server
            mlflow.set_tracking_uri(f"databricks://{self.databricks_host}")
        else:
            logger.warning("No Databricks credentials provided, using local MLflow")
        
        logger.info(f"MLflow Tracking URI: {mlflow.get_tracking_uri()}")
    
    def create_experiment(
        self,
        experiment_name: str,
        artifact_location: str = None,
        tags: Dict[str, str] = None
    ) -> str:
        """
        Create or get experiment
        
        Args:
            experiment_name: Name of experiment
            artifact_location: Location for artifacts
            tags: Experiment tags
            
        Returns:
            Experiment ID
        """
        try:
            # Check if experiment exists
            experiment = mlflow.get_experiment_by_name(experiment_name)
            
            if experiment:
                logger.info(f"Using existing experiment: {experiment_name}")
                return experiment.experiment_id
            
            # Create new experiment
            experiment_id = mlflow.create_experiment(
                name=experiment_name,
                artifact_location=artifact_location,
                tags=tags or {}
            )
            
            logger.info(f"Created experiment: {experiment_name} (ID: {experiment_id})")
            return experiment_id
            
        except Exception as e:
            logger.error(f"Error creating experiment: {e}")
            raise
    
    def start_run(
        self,
        config: ExperimentConfig,
        nested: bool = False
    ) -> str:
        """
        Start MLflow run
        
        Args:
            config: Experiment configuration
            nested: Whether to create nested run
            
        Returns:
            Run ID
        """
        try:
            # Create or get experiment
            experiment_id = self.create_experiment(config.experiment_name)
            
            # Set experiment
            mlflow.set_experiment(config.experiment_name)
            
            # Start run
            run = mlflow.start_run(
                run_name=config.run_name,
                nested=nested
            )
            
            # Log tags
            for key, value in config.tags.items():
                mlflow.set_tag(key, value)
            
            # Log params
            for key, value in config.params.items():
                mlflow.log_param(key, value)
            
            logger.info(f"Started MLflow run: {config.run_name} (ID: {run.info.run_id})")
            return run.info.run_id
            
        except Exception as e:
            logger.error(f"Error starting run: {e}")
            raise
    
    def log_metrics(
        self,
        metrics: Dict[str, float],
        step: int = None
    ) -> None:
        """
        Log metrics to MLflow
        
        Args:
            metrics: Dictionary of metrics
            step: Step number
        """
        try:
            for key, value in metrics.items():
                mlflow.log_metric(key, value, step=step)
            
            logger.debug(f"Logged {len(metrics)} metrics")
            
        except Exception as e:
            logger.error(f"Error logging metrics: {e}")
    
    def log_model(
        self,
        model: Any,
        artifact_path: str,
        model_type: str = "sklearn",
        registered_model_name: str = None
    ) -> None:
        """
        Log model to MLflow Model Registry
        
        Args:
            model: Model object
            artifact_path: Path to save model
            model_type: Type of model (sklearn, pytorch, etc)
            registered_model_name: Name for model registry
        """
        try:
            if model_type == "sklearn":
                mlflow.sklearn.log_model(
                    model,
                    artifact_path=artifact_path,
                    registered_model_name=registered_model_name
                )
            elif model_type == "pytorch":
                mlflow.pytorch.log_model(
                    model,
                    artifact_path=artifact_path,
                    registered_model_name=registered_model_name
                )
            else:
                mlflow.log_model(
                    model,
                    artifact_path=artifact_path,
                    registered_model_name=registered_model_name
                )
            
            logger.info(f"Logged model: {artifact_path}")
            
        except Exception as e:
            logger.error(f"Error logging model: {e}")
    
    def log_artifact(
        self,
        local_path: str,
        artifact_path: str = None
    ) -> None:
        """
        Log artifact to MLflow
        
        Args:
            local_path: Local file path
            artifact_path: Remote artifact path
        """
        try:
            mlflow.log_artifact(local_path, artifact_path)
            logger.info(f"Logged artifact: {local_path}")
            
        except Exception as e:
            logger.error(f"Error logging artifact: {e}")
    
    def end_run(self, status: str = "FINISHED") -> None:
        """
        End MLflow run
        
        Args:
            status: Run status (FINISHED, FAILED)
        """
        try:
            mlflow.end_run(status=status)
            logger.info(f"Ended run with status: {status}")
            
        except Exception as e:
            logger.error(f"Error ending run: {e}")
    
    def get_run_info(self, run_id: str) -> Dict[str, Any]:
        """
        Get run information
        
        Args:
            run_id: Run ID
            
        Returns:
            Run information
        """
        try:
            run = mlflow.get_run(run_id)
            
            return {
                "run_id": run.info.run_id,
                "experiment_id": run.info.experiment_id,
                "status": run.info.status,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time,
                "params": run.data.params,
                "metrics": run.data.metrics,
                "tags": run.data.tags
            }
            
        except Exception as e:
            logger.error(f"Error getting run info: {e}")
            return {}
    
    def search_runs(
        self,
        experiment_id: str = None,
        filter_string: str = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search runs
        
        Args:
            experiment_id: Experiment ID
            filter_string: Filter string
            max_results: Maximum results
            
        Returns:
            List of runs
        """
        try:
            runs = mlflow.search_runs(
                experiment_ids=[experiment_id] if experiment_id else None,
                filter_string=filter_string,
                max_results=max_results
            )
            
            return [
                {
                    "run_id": run.run_id,
                    "status": run.status,
                    "metrics": run.data.metrics,
                    "params": run.data.params
                }
                for run in runs
            ]
            
        except Exception as e:
            logger.error(f"Error searching runs: {e}")
            return []


class ModelRegistry:
    """MLflow Model Registry Manager"""
    
    def __init__(self, client: MLflowDatabricksClient):
        """
        Initialize Model Registry
        
        Args:
            client: MLflow Databricks client
        """
        self.client = client
    
    def register_model(
        self,
        model_uri: str,
        model_name: str,
        description: str = None,
        tags: Dict[str, str] = None
    ) -> str:
        """
        Register model in Model Registry
        
        Args:
            model_uri: Model URI from run
            model_name: Model name
            description: Model description
            tags: Model tags
            
        Returns:
            Model version
        """
        try:
            result = mlflow.register_model(
                model_uri=model_uri,
                name=model_name,
                tags=tags or {}
            )
            
            # Update model description
            if description:
                client = mlflow.tracking.MlflowClient()
                client.update_registered_model(
                    name=model_name,
                    description=description
                )
            
            logger.info(f"Registered model: {model_name} (Version: {result.version})")
            return result.version
            
        except Exception as e:
            logger.error(f"Error registering model: {e}")
            raise
    
    def transition_model_stage(
        self,
        model_name: str,
        version: str,
        stage: str
    ) -> None:
        """
        Transition model stage (Staging, Production, Archived)
        
        Args:
            model_name: Model name
            version: Model version
            stage: Target stage
        """
        try:
            client = mlflow.tracking.MlflowClient()
            client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage
            )
            
            logger.info(f"Transitioned {model_name} v{version} to {stage}")
            
        except Exception as e:
            logger.error(f"Error transitioning model: {e}")
    
    def get_model_versions(self, model_name: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a model
        
        Args:
            model_name: Model name
            
        Returns:
            List of model versions
        """
        try:
            client = mlflow.tracking.MlflowClient()
            versions = client.search_model_versions(f"name='{model_name}'")
            
            return [
                {
                    "version": v.version,
                    "stage": v.current_stage,
                    "created_timestamp": v.creation_timestamp,
                    "source": v.source,
                    "status": v.status
                }
                for v in versions
            ]
            
        except Exception as e:
            logger.error(f"Error getting model versions: {e}")
            return []


class ExperimentTracker:
    """High-level experiment tracking interface"""
    
    def __init__(self, client: MLflowDatabricksClient):
        """
        Initialize Experiment Tracker
        
        Args:
            client: MLflow Databricks client
        """
        self.client = client
        self.model_registry = ModelRegistry(client)
        self.current_run_id = None
    
    def track_backtest(
        self,
        strategy_name: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, float],
        model: Any = None,
        tags: Dict[str, str] = None
    ) -> str:
        """
        Track backtest run
        
        Args:
            strategy_name: Strategy name
            parameters: Strategy parameters
            metrics: Performance metrics
            model: Trained model (optional)
            tags: Additional tags
            
        Returns:
            Run ID
        """
        try:
            # Create config
            config = ExperimentConfig(
                experiment_name="Ravenshire_Backtests",
                run_name=f"{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                params=parameters,
                tags={
                    "strategy": strategy_name,
                    "type": "backtest",
                    **(tags or {})
                }
            )
            
            # Start run
            run_id = self.client.start_run(config)
            self.current_run_id = run_id
            
            # Log metrics
            self.client.log_metrics(metrics)
            
            # Log model if provided
            if model:
                self.client.log_model(
                    model,
                    artifact_path="model",
                    registered_model_name=f"{strategy_name}_model"
                )
            
            return run_id
            
        except Exception as e:
            logger.error(f"Error tracking backtest: {e}")
            raise
    
    def track_live_trading(
        self,
        strategy_name: str,
        daily_metrics: Dict[str, float],
        portfolio_state: Dict[str, Any]
    ) -> None:
        """
        Track live trading metrics
        
        Args:
            strategy_name: Strategy name
            daily_metrics: Daily performance metrics
            portfolio_state: Current portfolio state
        """
        try:
            # Log daily metrics
            self.client.log_metrics(daily_metrics)
            
            # Log portfolio state as artifact
            state_file = f"/tmp/portfolio_state_{datetime.now().isoformat()}.json"
            with open(state_file, "w") as f:
                json.dump(portfolio_state, f)
            
            self.client.log_artifact(state_file, "portfolio_states")
            
        except Exception as e:
            logger.error(f"Error tracking live trading: {e}")
    
    def end_experiment(self) -> None:
        """End current experiment"""
        if self.current_run_id:
            self.client.end_run()
            self.current_run_id = None
