"""
Workflow Logger for End-to-End Ticket Processing

Provides structured logging for:
- Agent decisions and routing choices
- Tool usage and outcomes
- Ticket processing stages
- Error handling and edge cases
- Resolution and escalation scenarios
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import os

class LogLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"

class TicketStage(Enum):
    SUBMISSION = "submission"
    CLASSIFICATION = "classification"
    ROUTING = "routing"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    TOOL_USAGE = "tool_usage"
    RESOLUTION_ATTEMPT = "resolution_attempt"
    ESCALATION = "escalation"
    RESOLUTION = "resolution"
    COMPLETION = "completion"

class LogEntryType(Enum):
    TICKET_SUBMISSION = "ticket_submission"
    AGENT_DECISION = "agent_decision"
    ROUTING_CHOICE = "routing_choice"
    TOOL_USAGE = "tool_usage"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    ERROR_HANDLING = "error_handling"
    RESOLUTION_ATTEMPT = "resolution_attempt"
    ESCALATION = "escalation"
    WORKFLOW_STAGE = "workflow_stage"

@dataclass
class LogEntry:
    """Structured log entry for ticket processing"""
    log_id: str
    timestamp: str
    ticket_id: str
    user_id: str
    entry_type: LogEntryType
    stage: TicketStage
    level: LogLevel
    message: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]

class WorkflowLogger:
    """
    Comprehensive logger for end-to-end ticket processing workflow
    """
    
    def __init__(self, log_file_path: str = "workflow_logs.jsonl"):
        self.log_file_path = log_file_path
        self.logger = self._setup_logger()
        self.current_ticket_id = None
        self.current_user_id = None
        self.session_logs = []
    
    def _setup_logger(self) -> logging.Logger:
        """Setup structured logger"""
        logger = logging.getLogger("workflow_logger")
        logger.setLevel(logging.DEBUG)
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
        
        # File handler for structured logs
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def start_ticket_session(self, ticket_id: str, user_id: str, initial_query: str) -> None:
        """Start logging session for a new ticket"""
        self.current_ticket_id = ticket_id
        self.current_user_id = user_id
        self.session_logs = []
        
        self._log_entry(
            LogEntryType.TICKET_SUBMISSION,
            TicketStage.SUBMISSION,
            LogLevel.INFO,
            f"Ticket session started for {ticket_id}",
            {
                "ticket_id": ticket_id,
                "user_id": user_id,
                "initial_query": initial_query,
                "session_start": datetime.now().isoformat()
            }
        )
    
    def log_agent_decision(self, agent_name: str, decision: Dict[str, Any], confidence: float = None) -> None:
        """Log agent decision and routing choice"""
        self._log_entry(
            LogEntryType.AGENT_DECISION,
            TicketStage.CLASSIFICATION,
            LogLevel.INFO,
            f"Agent {agent_name} made decision",
            {
                "agent": agent_name,
                "decision": decision,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_routing_choice(self, from_agent: str, to_agent: str, reason: str, routing_data: Dict[str, Any] = None) -> None:
        """Log routing decision between agents"""
        self._log_entry(
            LogEntryType.ROUTING_CHOICE,
            TicketStage.ROUTING,
            LogLevel.INFO,
            f"Routed from {from_agent} to {to_agent}: {reason}",
            {
                "from_agent": from_agent,
                "to_agent": to_agent,
                "reason": reason,
                "routing_data": routing_data or {},
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_knowledge_retrieval(self, query: str, articles_found: int, confidence: float, escalation: bool = False) -> None:
        """Log knowledge retrieval attempt"""
        self._log_entry(
            LogEntryType.KNOWLEDGE_RETRIEVAL,
            TicketStage.KNOWLEDGE_RETRIEVAL,
            LogLevel.INFO,
            f"Knowledge retrieval: {articles_found} articles found, confidence: {confidence}",
            {
                "query": query,
                "articles_found": articles_found,
                "confidence": confidence,
                "escalation_required": escalation,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_tool_usage(self, tool_name: str, parameters: Dict[str, Any], result: Any, success: bool = True) -> None:
        """Log tool usage and outcome"""
        self._log_entry(
            LogEntryType.TOOL_USAGE,
            TicketStage.TOOL_USAGE,
            LogLevel.INFO if success else LogLevel.ERROR,
            f"Tool {tool_name} used: {'success' if success else 'failed'}",
            {
                "tool_name": tool_name,
                "parameters": parameters,
                "result": result,
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_resolution_attempt(self, agent: str, resolution_method: str, success: bool, details: Dict[str, Any] = None) -> None:
        """Log resolution attempt"""
        self._log_entry(
            LogEntryType.RESOLUTION_ATTEMPT,
            TicketStage.RESOLUTION_ATTEMPT,
            LogLevel.INFO,
            f"Resolution attempt by {agent}: {'success' if success else 'failed'}",
            {
                "agent": agent,
                "resolution_method": resolution_method,
                "success": success,
                "details": details or {},
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_escalation(self, reason: str, escalation_type: str, details: Dict[str, Any] = None) -> None:
        """Log escalation decision"""
        self._log_entry(
            LogEntryType.ESCALATION,
            TicketStage.ESCALATION,
            LogLevel.WARNING,
            f"Ticket escalated: {reason}",
            {
                "reason": reason,
                "escalation_type": escalation_type,
                "details": details or {},
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None) -> None:
        """Log error handling and edge cases"""
        self._log_entry(
            LogEntryType.ERROR_HANDLING,
            TicketStage.RESOLUTION_ATTEMPT,
            LogLevel.ERROR,
            f"Error occurred: {error_type} - {error_message}",
            {
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {},
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_workflow_stage(self, stage: TicketStage, stage_data: Dict[str, Any] = None) -> None:
        """Log workflow stage transition"""
        self._log_entry(
            LogEntryType.WORKFLOW_STAGE,
            stage,
            LogLevel.INFO,
            f"Workflow stage: {stage.value}",
            {
                "stage": stage.value,
                "stage_data": stage_data or {},
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_ticket_completion(self, final_status: str, resolution_summary: str, total_duration: float) -> None:
        """Log ticket completion"""
        self._log_entry(
            LogEntryType.RESOLUTION_ATTEMPT,
            TicketStage.COMPLETION,
            LogLevel.INFO,
            f"Ticket completed with status: {final_status}",
            {
                "final_status": final_status,
                "resolution_summary": resolution_summary,
                "total_duration_seconds": total_duration,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def _log_entry(self, entry_type: LogEntryType, stage: TicketStage, level: LogLevel, message: str, data: Dict[str, Any]) -> None:
        """Create and store log entry"""
        log_entry = LogEntry(
            log_id=f"log_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now().isoformat(),
            ticket_id=self.current_ticket_id or "unknown",
            user_id=self.current_user_id or "unknown",
            entry_type=entry_type,
            stage=stage,
            level=level,
            message=message,
            data=data,
            metadata={
                "session_id": f"session_{self.current_ticket_id}" if self.current_ticket_id else "unknown",
                "log_version": "1.0"
            }
        )
        
        # Store in session logs
        self.session_logs.append(asdict(log_entry))
        
        # Write to file
        try:
            # Convert enum values to strings for JSON serialization
            log_dict = asdict(log_entry)
            log_dict["entry_type"] = log_dict["entry_type"].value
            log_dict["stage"] = log_dict["stage"].value
            log_dict["level"] = log_dict["level"].value
            
            # Convert datetime objects to ISO strings
            if isinstance(log_dict["timestamp"], datetime):
                log_dict["timestamp"] = log_dict["timestamp"].isoformat()
            
            # Clean up data field for JSON serialization
            if "data" in log_dict and isinstance(log_dict["data"], dict):
                cleaned_data = {}
                for key, value in log_dict["data"].items():
                    if isinstance(value, datetime):
                        cleaned_data[key] = value.isoformat()
                    else:
                        cleaned_data[key] = value
                log_dict["data"] = cleaned_data
            
            with open(self.log_file_path, 'a') as f:
                f.write(json.dumps(log_dict) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write log entry: {e}")
        
        # Log to console for immediate feedback
        log_message = f"[{stage.value.upper()}] {message}"
        if level == LogLevel.ERROR:
            self.logger.error(log_message)
        elif level == LogLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def get_session_logs(self) -> List[Dict[str, Any]]:
        """Get all logs for current session"""
        return self.session_logs.copy()
    
    def search_logs(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search logs based on criteria"""
        results = []
        
        try:
            with open(self.log_file_path, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            log_entry = json.loads(line)
                            
                            # Check if entry matches criteria
                            matches = True
                            for key, value in criteria.items():
                                if key not in log_entry or log_entry[key] != value:
                                    matches = False
                                    break
                            
                            if matches:
                                results.append(log_entry)
                        except json.JSONDecodeError:
                            # Skip malformed JSON lines
                            continue
        except Exception as e:
            self.logger.error(f"Failed to search logs: {e}")
        
        return results
    
    def get_ticket_summary(self, ticket_id: str) -> Dict[str, Any]:
        """Get summary of ticket processing"""
        ticket_logs = self.search_logs({"ticket_id": ticket_id})
        
        if not ticket_logs:
            return {"error": "Ticket not found"}
        
        # Analyze logs
        stages = [log["stage"] for log in ticket_logs]
        agents_used = set()
        tools_used = set()
        errors = []
        escalations = []
        
        for log in ticket_logs:
            if log["entry_type"] == "agent_decision":
                agents_used.add(log["data"].get("agent", "unknown"))
            elif log["entry_type"] == "tool_usage":
                tools_used.add(log["data"].get("tool_name", "unknown"))
            elif log["entry_type"] == "error_handling":
                errors.append(log["data"])
            elif log["entry_type"] == "escalation":
                escalations.append(log["data"])
        
        return {
            "ticket_id": ticket_id,
            "stages_completed": list(set(stages)),
            "agents_used": list(agents_used),
            "tools_used": list(tools_used),
            "error_count": len(errors),
            "escalation_count": len(escalations),
            "total_log_entries": len(ticket_logs),
            "processing_time": self._calculate_processing_time(ticket_logs),
            "final_status": self._determine_final_status(ticket_logs)
        }
    
    def _calculate_processing_time(self, logs: List[Dict[str, Any]]) -> float:
        """Calculate total processing time from logs"""
        if len(logs) < 2:
            return 0.0
        
        start_time = datetime.fromisoformat(logs[0]["timestamp"])
        end_time = datetime.fromisoformat(logs[-1]["timestamp"])
        return (end_time - start_time).total_seconds()
    
    def _determine_final_status(self, logs: List[Dict[str, Any]]) -> str:
        """Determine final status from logs"""
        for log in reversed(logs):
            if log["entry_type"] == "escalation":
                return "escalated"
            elif log["entry_type"] == "resolution_attempt" and log["data"].get("success"):
                return "resolved"
        return "in_progress"
