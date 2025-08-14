"""
Action Tools for Multi-Agent System

Tools for performing various actions including:
- User updates
- Ticket creation
- Account modifications
- System notifications
"""

from langchain.tools import BaseTool
from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime

class ActionTool(BaseTool):
    name: str = "action_tool"
    description: str = "Tool for performing various actions in the system"
    database_tool: Any = None
    action_log: List[Dict[str, Any]] = []
    
    def __init__(self, database_tool=None):
        super().__init__()
        self.database_tool = database_tool
        self.action_log = []
    
    def _run(self, action: str, **kwargs) -> Dict[str, Any]:
        """Perform various actions"""
        try:
            if action == "update_user":
                return self._update_user(kwargs)
            elif action == "create_ticket":
                return self._create_ticket(kwargs)
            elif action == "update_preferences":
                return self._update_preferences(kwargs)
            elif action == "escalate_issue":
                return self._escalate_issue(kwargs)
            elif action == "send_notification":
                return self._send_notification(kwargs)
            elif action == "log_interaction":
                return self._log_interaction(kwargs)
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": f"Action failed: {str(e)}"}
    
    def _update_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information"""
        user_id = params.get("user_id")
        updates = params.get("updates", {})
        
        if not user_id:
            return {"error": "User ID is required"}
        
        # In a real implementation, this would update the database
        # For now, simulate the update
        update_result = {
            "user_id": user_id,
            "action": "update_user",
            "updates": updates,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": "User information updated successfully"
        }
        
        # Log the action
        self._log_action("update_user", update_result)
        
        return update_result
    
    def _create_ticket(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a support ticket"""
        user_id = params.get("user_id")
        account_id = params.get("account_id")
        issue_type = params.get("issue_type", "general")
        description = params.get("description", "")
        priority = params.get("priority", "medium")
        
        if not user_id or not account_id:
            return {"error": "User ID and Account ID are required"}
        
        # Generate ticket ID
        ticket_id = str(uuid.uuid4())
        
        # Create ticket data
        ticket_data = {
            "ticket_id": ticket_id,
            "user_id": user_id,
            "account_id": account_id,
            "issue_type": issue_type,
            "description": description,
            "priority": priority,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "channel": "chat"
        }
        
        # In a real implementation, this would create the ticket in the database
        # For now, simulate the creation
        create_result = {
            "ticket_id": ticket_id,
            "action": "create_ticket",
            "status": "success",
            "message": "Support ticket created successfully",
            "ticket_data": ticket_data
        }
        
        # Log the action
        self._log_action("create_ticket", create_result)
        
        return create_result
    
    def _update_preferences(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences"""
        user_id = params.get("user_id")
        preferences = params.get("preferences", {})
        
        if not user_id:
            return {"error": "User ID is required"}
        
        # Validate preferences
        valid_preferences = ["notifications", "privacy", "language", "timezone"]
        filtered_preferences = {k: v for k, v in preferences.items() if k in valid_preferences}
        
        update_result = {
            "user_id": user_id,
            "action": "update_preferences",
            "preferences": filtered_preferences,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": "Preferences updated successfully"
        }
        
        # Log the action
        self._log_action("update_preferences", update_result)
        
        return update_result
    
    def _escalate_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate an issue to human support"""
        ticket_id = params.get("ticket_id")
        reason = params.get("reason", "Complex issue requiring human intervention")
        priority = params.get("priority", "medium")
        
        if not ticket_id:
            return {"error": "Ticket ID is required"}
        
        escalation_data = {
            "escalation_id": str(uuid.uuid4()),
            "ticket_id": ticket_id,
            "reason": reason,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "assigned_to": None
        }
        
        escalation_result = {
            "action": "escalate_issue",
            "status": "success",
            "message": "Issue escalated to human support team",
            "escalation_data": escalation_data
        }
        
        # Log the action
        self._log_action("escalate_issue", escalation_result)
        
        return escalation_result
    
    def _send_notification(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification to user"""
        user_id = params.get("user_id")
        notification_type = params.get("type", "info")
        message = params.get("message", "")
        channel = params.get("channel", "email")
        
        if not user_id or not message:
            return {"error": "User ID and message are required"}
        
        notification_data = {
            "notification_id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": notification_type,
            "message": message,
            "channel": channel,
            "status": "sent",
            "sent_at": datetime.now().isoformat()
        }
        
        notification_result = {
            "action": "send_notification",
            "status": "success",
            "message": f"Notification sent via {channel}",
            "notification_data": notification_data
        }
        
        # Log the action
        self._log_action("send_notification", notification_result)
        
        return notification_result
    
    def _log_interaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Log user interaction"""
        user_id = params.get("user_id")
        interaction_type = params.get("type", "query")
        content = params.get("content", "")
        agent = params.get("agent", "unknown")
        
        if not user_id:
            return {"error": "User ID is required"}
        
        interaction_data = {
            "interaction_id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": interaction_type,
            "content": content,
            "agent": agent,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to action log
        self.action_log.append(interaction_data)
        
        return {
            "action": "log_interaction",
            "status": "success",
            "message": "Interaction logged successfully",
            "interaction_data": interaction_data
        }
    
    def _log_action(self, action_type: str, result: Dict[str, Any]) -> None:
        """Log an action for audit purposes"""
        log_entry = {
            "action_id": str(uuid.uuid4()),
            "action_type": action_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        self.action_log.append(log_entry)
    
    def get_action_log(self, limit: int = 50) -> Dict[str, Any]:
        """Get recent action log entries"""
        recent_actions = self.action_log[-limit:] if self.action_log else []
        
        return {
            "action": "get_action_log",
            "status": "success",
            "total_actions": len(self.action_log),
            "returned_actions": len(recent_actions),
            "actions": recent_actions
        }
    
    def clear_action_log(self) -> Dict[str, Any]:
        """Clear the action log"""
        log_count = len(self.action_log)
        self.action_log.clear()
        
        return {
            "action": "clear_action_log",
            "status": "success",
            "message": f"Cleared {log_count} action log entries"
        }
    
    def validate_action(self, action_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate action parameters before execution"""
        validation_rules = {
            "update_user": ["user_id"],
            "create_ticket": ["user_id", "account_id"],
            "update_preferences": ["user_id"],
            "escalate_issue": ["ticket_id"],
            "send_notification": ["user_id", "message"],
            "log_interaction": ["user_id"]
        }
        
        required_fields = validation_rules.get(action_type, [])
        missing_fields = [field for field in required_fields if field not in params]
        
        if missing_fields:
            return {
                "valid": False,
                "error": f"Missing required fields: {missing_fields}",
                "required_fields": required_fields
            }
        
        return {
            "valid": True,
            "message": "Action parameters are valid"
        }
    
    def get_available_actions(self) -> Dict[str, Any]:
        """Get list of available actions"""
        available_actions = {
            "update_user": {
                "description": "Update user information",
                "required_fields": ["user_id"],
                "optional_fields": ["updates"]
            },
            "create_ticket": {
                "description": "Create a support ticket",
                "required_fields": ["user_id", "account_id"],
                "optional_fields": ["issue_type", "description", "priority"]
            },
            "update_preferences": {
                "description": "Update user preferences",
                "required_fields": ["user_id"],
                "optional_fields": ["preferences"]
            },
            "escalate_issue": {
                "description": "Escalate issue to human support",
                "required_fields": ["ticket_id"],
                "optional_fields": ["reason", "priority"]
            },
            "send_notification": {
                "description": "Send notification to user",
                "required_fields": ["user_id", "message"],
                "optional_fields": ["type", "channel"]
            },
            "log_interaction": {
                "description": "Log user interaction",
                "required_fields": ["user_id"],
                "optional_fields": ["type", "content", "agent"]
            }
        }
        
        return {
            "action": "get_available_actions",
            "status": "success",
            "available_actions": available_actions
        }
