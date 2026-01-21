"""
Orchestration Layer - Workflow orchestration and scheduling
Part of the 5-Layer Hedge Fund Architecture
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class WorkflowTask:
    """Represents a workflow task"""
    task_id: str
    name: str
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    status: str = "PENDING"
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: str = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.created_at is None:
            self.created_at = str(datetime.utcnow())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error
        }


@dataclass
class Workflow:
    """Represents a workflow"""
    workflow_id: str
    name: str
    tasks: List[WorkflowTask]
    schedule: Optional[str] = None  # Cron expression
    status: str = "PENDING"
    created_at: str = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = str(datetime.utcnow())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "status": self.status,
            "num_tasks": len(self.tasks),
            "schedule": self.schedule,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


class TaskExecutor:
    """Executes individual tasks"""
    
    @staticmethod
    async def execute_task(task: WorkflowTask) -> WorkflowTask:
        """
        Execute a task
        
        Args:
            task: Task to execute
            
        Returns:
            Updated task with result
        """
        try:
            task.status = "RUNNING"
            task.started_at = str(datetime.utcnow())
            
            logger.info(f"Executing task: {task.name}")
            
            # Execute function
            if asyncio.iscoroutinefunction(task.func):
                result = await task.func(*task.args, **task.kwargs)
            else:
                result = task.func(*task.args, **task.kwargs)
            
            task.result = result
            task.status = "COMPLETED"
            task.completed_at = str(datetime.utcnow())
            
            logger.info(f"Task completed: {task.name}")
            
        except Exception as e:
            task.status = "FAILED"
            task.error = str(e)
            task.completed_at = str(datetime.utcnow())
            
            logger.error(f"Task failed: {task.name} - {e}")
        
        return task


class WorkflowExecutor:
    """Executes workflows"""
    
    def __init__(self):
        self.task_executor = TaskExecutor()
        self.workflows: Dict[str, Workflow] = {}
        self.workflow_counter = 0
    
    async def execute_workflow(self, workflow: Workflow) -> Workflow:
        """
        Execute a workflow
        
        Args:
            workflow: Workflow to execute
            
        Returns:
            Updated workflow
        """
        try:
            workflow.status = "RUNNING"
            workflow.started_at = str(datetime.utcnow())
            
            logger.info(f"Starting workflow: {workflow.name}")
            
            # Execute tasks sequentially
            for task in workflow.tasks:
                task = await self.task_executor.execute_task(task)
                
                # Stop if task failed
                if task.status == "FAILED":
                    workflow.status = "FAILED"
                    workflow.completed_at = str(datetime.utcnow())
                    logger.error(f"Workflow failed: {workflow.name}")
                    return workflow
            
            workflow.status = "COMPLETED"
            workflow.completed_at = str(datetime.utcnow())
            
            logger.info(f"Workflow completed: {workflow.name}")
            
        except Exception as e:
            workflow.status = "FAILED"
            workflow.completed_at = str(datetime.utcnow())
            logger.error(f"Workflow error: {workflow.name} - {e}")
        
        return workflow
    
    def create_workflow(
        self,
        name: str,
        tasks: List[WorkflowTask],
        schedule: Optional[str] = None
    ) -> Workflow:
        """Create a workflow"""
        self.workflow_counter += 1
        workflow_id = f"WF_{self.workflow_counter}"
        
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            tasks=tasks,
            schedule=schedule
        )
        
        self.workflows[workflow_id] = workflow
        logger.info(f"Workflow created: {workflow_id} - {name}")
        
        return workflow
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status"""
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        return workflow.to_dict()


class ScheduleManager:
    """Manages workflow scheduling"""
    
    def __init__(self):
        self.scheduled_workflows: Dict[str, Dict[str, Any]] = {}
    
    def schedule_workflow(
        self,
        workflow: Workflow,
        schedule_time: str,  # HH:MM format
        frequency: str = "daily"  # daily, weekly, monthly
    ) -> None:
        """
        Schedule a workflow
        
        Args:
            workflow: Workflow to schedule
            schedule_time: Time to run (HH:MM)
            frequency: Frequency of execution
        """
        schedule_key = f"{workflow.workflow_id}_{frequency}_{schedule_time}"
        
        self.scheduled_workflows[schedule_key] = {
            "workflow_id": workflow.workflow_id,
            "workflow_name": workflow.name,
            "schedule_time": schedule_time,
            "frequency": frequency,
            "created_at": str(datetime.utcnow())
        }
        
        logger.info(f"Workflow scheduled: {workflow.name} at {schedule_time} ({frequency})")
    
    def get_scheduled_workflows(self) -> List[Dict[str, Any]]:
        """Get all scheduled workflows"""
        return list(self.scheduled_workflows.values())
    
    def should_run_now(self, schedule_time: str, frequency: str) -> bool:
        """Check if workflow should run now"""
        now = datetime.utcnow()
        current_time = now.strftime("%H:%M")
        
        if frequency == "daily":
            return current_time == schedule_time
        elif frequency == "weekly":
            # Run on Monday at specified time
            return now.weekday() == 0 and current_time == schedule_time
        elif frequency == "monthly":
            # Run on first day of month at specified time
            return now.day == 1 and current_time == schedule_time
        
        return False


class WorkflowBuilder:
    """Builds workflows"""
    
    def __init__(self):
        self.task_counter = 0
    
    def create_task(
        self,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None
    ) -> WorkflowTask:
        """Create a task"""
        self.task_counter += 1
        task_id = f"TASK_{self.task_counter}"
        
        return WorkflowTask(
            task_id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs or {}
        )
    
    def build_data_fetch_workflow(self, data_manager) -> Workflow:
        """Build data fetch workflow"""
        tasks = [
            self.create_task(
                "Fetch Market Data",
                data_manager.get_market_data,
                kwargs={
                    "symbols": ["AAPL", "MSFT", "GOOGL"],
                    "start_date": "2024-01-01",
                    "end_date": "2026-01-20"
                }
            )
        ]
        
        return Workflow(
            workflow_id="WF_DATA_FETCH",
            name="Data Fetch Workflow",
            tasks=tasks,
            schedule="0 16 * * *"  # Daily at 4 PM UTC
        )
    
    def build_backtest_workflow(self, research_manager, data) -> Workflow:
        """Build backtest workflow"""
        tasks = [
            self.create_task(
                "Run Backtest",
                research_manager.backtest_strategy,
                kwargs={
                    "strategy_func": lambda x, **kw: x,
                    "data": data,
                    "parameters": {"ma_period": 20},
                    "strategy_name": "MA_Crossover"
                }
            )
        ]
        
        return Workflow(
            workflow_id="WF_BACKTEST",
            name="Backtest Workflow",
            tasks=tasks,
            schedule="0 18 * * 0"  # Weekly on Sunday at 6 PM UTC
        )
    
    def build_trade_execution_workflow(self, execution_manager, portfolio_manager) -> Workflow:
        """Build trade execution workflow"""
        tasks = [
            self.create_task(
                "Generate Signals",
                lambda: {"AAPL": 1, "MSFT": 0}
            ),
            self.create_task(
                "Optimize Portfolio",
                portfolio_manager.optimize_weights,
                kwargs={"returns": None, "method": "mean_variance"}
            ),
            self.create_task(
                "Execute Trades",
                lambda signals: logger.info(f"Executing trades: {signals}")
            )
        ]
        
        return Workflow(
            workflow_id="WF_EXECUTION",
            name="Trade Execution Workflow",
            tasks=tasks,
            schedule="0 9 * * 1-5"  # Weekdays at 9 AM UTC
        )


class OrchestrationManager:
    """Main orchestration interface"""
    
    def __init__(self):
        self.workflow_executor = WorkflowExecutor()
        self.schedule_manager = ScheduleManager()
        self.workflow_builder = WorkflowBuilder()
    
    async def run_workflow(self, workflow: Workflow) -> Workflow:
        """Run a workflow"""
        return await self.workflow_executor.execute_workflow(workflow)
    
    def schedule_workflow(
        self,
        workflow: Workflow,
        schedule_time: str,
        frequency: str = "daily"
    ) -> None:
        """Schedule a workflow"""
        self.schedule_manager.schedule_workflow(workflow, schedule_time, frequency)
    
    def get_scheduled_workflows(self) -> List[Dict[str, Any]]:
        """Get scheduled workflows"""
        return self.schedule_manager.get_scheduled_workflows()
    
    def create_data_fetch_workflow(self, data_manager) -> Workflow:
        """Create data fetch workflow"""
        return self.workflow_builder.build_data_fetch_workflow(data_manager)
    
    def create_trade_execution_workflow(self, execution_manager, portfolio_manager) -> Workflow:
        """Create trade execution workflow"""
        return self.workflow_builder.build_trade_execution_workflow(execution_manager, portfolio_manager)
