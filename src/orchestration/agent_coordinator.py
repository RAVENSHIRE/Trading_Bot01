"""
Agent Coordinator - Communication Bus for Multi-Agent System
Manages message passing and orchestration between agents
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
from collections import defaultdict, deque

from src.agents import (
    BaseAgent, 
    AgentMessage, 
    AgentDecision, 
    MessagePriority,
    OracleAgent,
    SentinelAgent
)


class AgentCoordinator:
    """
    Central coordinator for AEGIS-III agent communication
    
    Responsibilities:
    - Route messages between agents
    - Maintain message history
    - Coordinate multi-agent workflows
    - Aggregate agent decisions
    """
    
    def __init__(self):
        self.logger = logging.getLogger("aegis.coordinator")
        self.agents: Dict[str, BaseAgent] = {}
        self.message_history: deque = deque(maxlen=10000)
        self.decision_log: List[Dict[str, Any]] = []
        
        self.logger.info("Agent Coordinator initialized")
    
    def register_agent(self, agent: BaseAgent):
        """
        Register an agent with the coordinator
        
        Args:
            agent: BaseAgent instance to register
        """
        self.agents[agent.name] = agent
        self.logger.info(f"Agent '{agent.name}' registered")
    
    def send_message(self, message: AgentMessage):
        """
        Route a message to the recipient agent
        
        Args:
            message: AgentMessage to route
        """
        self.message_history.append(message)
        
        recipient = self.agents.get(message.recipient)
        if recipient:
            recipient.receive_message(message)
            self.logger.debug(
                f"Message routed: {message.sender} → {message.recipient} "
                f"({message.message_type})"
            )
        else:
            self.logger.error(f"Recipient agent '{message.recipient}' not found")
    
    def broadcast_message(self, sender: str, message_type: str, 
                         payload: Dict[str, Any],
                         exclude: Optional[List[str]] = None):
        """
        Broadcast a message to all agents except sender
        
        Args:
            sender: Name of sending agent
            message_type: Type of message
            payload: Message data
            exclude: List of agent names to exclude
        """
        exclude = exclude or []
        exclude.append(sender)
        
        for agent_name, agent in self.agents.items():
            if agent_name not in exclude:
                message = AgentMessage(
                    sender=sender,
                    recipient=agent_name,
                    message_type=message_type,
                    payload=payload
                )
                self.send_message(message)
    
    def execute_agent(self, agent_name: str, 
                     input_data: Dict[str, Any]) -> Optional[AgentDecision]:
        """
        Execute a specific agent
        
        Args:
            agent_name: Name of agent to execute
            input_data: Input data for agent
            
        Returns:
            AgentDecision or None if error
        """
        agent = self.agents.get(agent_name)
        if not agent:
            self.logger.error(f"Agent '{agent_name}' not found")
            return None
        
        decision = agent.execute(input_data)
        
        if decision:
            self.decision_log.append({
                "timestamp": datetime.now().isoformat(),
                "agent": agent_name,
                "decision": decision
            })
        
        return decision
    
    def execute_workflow(self, workflow_name: str, 
                        input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a predefined multi-agent workflow
        
        Args:
            workflow_name: Name of workflow to execute
            input_data: Initial input data
            
        Returns:
            Dictionary with workflow results
        """
        if workflow_name == "regime_detection":
            return self._workflow_regime_detection(input_data)
        elif workflow_name == "trade_validation":
            return self._workflow_trade_validation(input_data)
        elif workflow_name == "full_cycle":
            return self._workflow_full_cycle(input_data)
        else:
            self.logger.error(f"Unknown workflow: {workflow_name}")
            return {"error": f"Unknown workflow: {workflow_name}"}
    
    def _workflow_regime_detection(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Workflow: Market regime detection
        
        Steps:
        1. Oracle analyzes market conditions
        2. Broadcast regime to all agents
        """
        self.logger.info("Executing workflow: regime_detection")
        
        # Execute Oracle
        oracle_decision = self.execute_agent("Oracle", input_data)
        
        if not oracle_decision:
            return {"error": "Oracle execution failed"}
        
        # Broadcast regime to all agents
        regime_data = oracle_decision.recommendation
        self.broadcast_message(
            sender="Oracle",
            message_type="REGIME_UPDATE",
            payload=regime_data
        )
        
        return {
            "workflow": "regime_detection",
            "success": True,
            "regime": regime_data.get("regime"),
            "confidence": oracle_decision.confidence,
            "reasoning": oracle_decision.reasoning
        }
    
    def _workflow_trade_validation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Workflow: Validate proposed trades
        
        Steps:
        1. Sentinel performs risk checks
        2. Return approval/veto decision
        """
        self.logger.info("Executing workflow: trade_validation")
        
        # Execute Sentinel
        sentinel_decision = self.execute_agent("Sentinel", input_data)
        
        if not sentinel_decision:
            return {"error": "Sentinel execution failed"}
        
        approved = sentinel_decision.recommendation.get("approved", False)
        
        return {
            "workflow": "trade_validation",
            "success": True,
            "approved": approved,
            "decision_type": sentinel_decision.decision_type,
            "veto_reasons": sentinel_decision.recommendation.get("veto_reasons", []),
            "risk_metrics": sentinel_decision.recommendation.get("risk_metrics", {}),
            "reasoning": sentinel_decision.reasoning
        }
    
    def _workflow_full_cycle(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Workflow: Full trading cycle
        
        Steps:
        1. Oracle: Detect regime
        2. Analyst: Generate signals (placeholder)
        3. Strategist: Optimize portfolio (placeholder)
        4. Sentinel: Validate trades
        5. Sovereign: Final decision (placeholder)
        """
        self.logger.info("Executing workflow: full_cycle")
        
        results = {}
        
        # Step 1: Regime Detection
        oracle_result = self._workflow_regime_detection(input_data)
        results["regime_detection"] = oracle_result
        
        if not oracle_result.get("success"):
            return results
        
        # Step 2-3: Analyst & Strategist (placeholder)
        # These will be implemented in the ML phase
        results["analyst"] = {"status": "not_implemented"}
        results["strategist"] = {"status": "not_implemented"}
        
        # Step 4: Risk Validation
        if "proposed_trades" in input_data:
            validation_result = self._workflow_trade_validation(input_data)
            results["risk_validation"] = validation_result
        
        # Step 5: Sovereign Decision (placeholder)
        results["sovereign"] = {"status": "not_implemented"}
        
        return {
            "workflow": "full_cycle",
            "success": True,
            "results": results
        }
    
    def get_agent_status_all(self) -> Dict[str, Any]:
        """
        Get status of all registered agents
        
        Returns:
            Dictionary with status for each agent
        """
        return {
            name: agent.get_status() 
            for name, agent in self.agents.items()
        }
    
    def get_message_history(self, limit: int = 100) -> List[AgentMessage]:
        """
        Get recent message history
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of recent AgentMessage objects
        """
        return list(self.message_history)[-limit:]
    
    def get_decision_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent decision log
        
        Args:
            limit: Maximum number of decisions to return
            
        Returns:
            List of recent decisions
        """
        return self.decision_log[-limit:]
    
    def reset_all(self):
        """Reset all agents"""
        for agent in self.agents.values():
            agent.reset()
        
        self.message_history.clear()
        self.decision_log.clear()
        
        self.logger.info("All agents reset")
