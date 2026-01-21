"""
Base Agent Framework for AEGIS-III Multi-Agent System
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import logging


class AgentStatus(Enum):
    """Agent operational status"""
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    DISABLED = "disabled"


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentMessage:
    """Message passed between agents"""
    sender: str
    recipient: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None


@dataclass
class AgentDecision:
    """Decision output from an agent"""
    agent_name: str
    decision_type: str
    recommendation: Any
    confidence: float  # 0.0 - 1.0
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class BaseAgent(ABC):
    """
    Abstract base class for all AEGIS-III agents
    
    Each agent must implement:
    - process(): Main decision-making logic
    - validate_input(): Input validation
    - get_status(): Current agent state
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"aegis.agent.{name}")
        self.message_queue: List[AgentMessage] = []
        self.decision_history: List[AgentDecision] = []
        self.error_count = 0
        self.last_execution: Optional[datetime] = None
        
        self.logger.info(f"Agent '{name}' initialized")
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> AgentDecision:
        """
        Main processing logic for the agent
        
        Args:
            input_data: Dictionary containing all necessary input data
            
        Returns:
            AgentDecision object with recommendation and reasoning
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data before processing
        
        Args:
            input_data: Input to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    def execute(self, input_data: Dict[str, Any]) -> Optional[AgentDecision]:
        """
        Execute agent with error handling and logging
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            AgentDecision or None if error occurred
        """
        try:
            self.status = AgentStatus.PROCESSING
            self.last_execution = datetime.now()
            
            # Validate input
            if not self.validate_input(input_data):
                self.logger.error(f"Input validation failed for {self.name}")
                self.status = AgentStatus.ERROR
                self.error_count += 1
                return None
            
            # Process
            self.logger.info(f"Agent '{self.name}' processing...")
            decision = self.process(input_data)
            
            # Store decision
            self.decision_history.append(decision)
            
            # Trim history if too long
            if len(self.decision_history) > 1000:
                self.decision_history = self.decision_history[-1000:]
            
            self.status = AgentStatus.IDLE
            self.logger.info(
                f"Agent '{self.name}' completed: {decision.decision_type} "
                f"(confidence: {decision.confidence:.2f})"
            )
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Agent '{self.name}' error: {str(e)}", exc_info=True)
            self.status = AgentStatus.ERROR
            self.error_count += 1
            return None
    
    def send_message(self, recipient: str, message_type: str, 
                    payload: Dict[str, Any], 
                    priority: MessagePriority = MessagePriority.NORMAL) -> AgentMessage:
        """
        Create a message to send to another agent
        
        Args:
            recipient: Name of recipient agent
            message_type: Type of message
            payload: Message data
            priority: Message priority
            
        Returns:
            AgentMessage object
        """
        message = AgentMessage(
            sender=self.name,
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            priority=priority
        )
        
        self.logger.debug(f"Message sent to {recipient}: {message_type}")
        return message
    
    def receive_message(self, message: AgentMessage):
        """
        Receive a message from another agent
        
        Args:
            message: AgentMessage to process
        """
        self.message_queue.append(message)
        self.logger.debug(f"Message received from {message.sender}: {message.message_type}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status
        
        Returns:
            Dictionary with status information
        """
        return {
            "name": self.name,
            "status": self.status.value,
            "error_count": self.error_count,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "decision_count": len(self.decision_history),
            "queue_size": len(self.message_queue)
        }
    
    def get_recent_decisions(self, limit: int = 10) -> List[AgentDecision]:
        """
        Get recent decisions made by this agent
        
        Args:
            limit: Maximum number of decisions to return
            
        Returns:
            List of recent AgentDecision objects
        """
        return self.decision_history[-limit:]
    
    def reset(self):
        """Reset agent state"""
        self.status = AgentStatus.IDLE
        self.message_queue.clear()
        self.error_count = 0
        self.logger.info(f"Agent '{self.name}' reset")
