"""
Account Management Agent - Expert in User Account Operations

This agent is responsible for:
- Handling account creation and updates
- Managing user preferences
- Processing account transfers
- Handling privacy and security concerns
- Managing user data
"""

from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import json
import re

class AccountManagementAgent:
    def __init__(self, llm: ChatOpenAI, knowledge_base_agent=None):
        self.llm = llm
        self.knowledge_base_agent = knowledge_base_agent
        self.system_prompt = self._create_system_prompt()
        self.account_keywords = self._create_account_keywords()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the account management agent"""
        return """You are the Account Management Agent for Uda-hub, a customer support system for CultPass users. Your role is to:

1. HANDLE account creation and updates
2. MANAGE user preferences and settings
3. PROCESS account transfers between users
4. HANDLE privacy and security concerns
5. MANAGE user data and profile information

Account management features:
- Profile updates and preferences
- Privacy settings and data management
- Account transfer requests
- Security settings and authentication
- Data export and deletion requests

Always prioritize user privacy and security. For sensitive operations, explain the process clearly and mention verification requirements."""
    
    def _create_account_keywords(self) -> Dict[str, List[str]]:
        """Create account keywords for query classification"""
        return {
            "profile": ["profile", "account", "information", "details", "personal"],
            "preferences": ["preferences", "settings", "notifications", "privacy", "options"],
            "transfer": ["transfer", "gift", "share", "give", "move account"],
            "security": ["security", "password", "authentication", "login", "access"],
            "data": ["data", "information", "export", "delete", "privacy"]
        }
    
    def handle_account_operations(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle account-related operations"""
        query_lower = query.lower()
        
        # Classify the account operation
        operation_type = self._classify_operation(query_lower)
        
        # Get relevant account articles
        account_articles = []
        if self.knowledge_base_agent:
            account_articles = self.knowledge_base_agent.get_articles_by_tag("account")
        
        # Generate response
        response = self._generate_account_response(query, operation_type, account_articles, user_context)
        
        return {
            "operation_type": operation_type,
            "response": response,
            "articles": account_articles,
            "requires_verification": self._requires_verification(operation_type)
        }
    
    def _classify_operation(self, query: str) -> str:
        """Classify the type of account operation"""
        for operation_type, keywords in self.account_keywords.items():
            if any(keyword in query for keyword in keywords):
                return operation_type
        
        return "general_account"
    
    def _generate_account_response(self, query: str, operation_type: str, articles: List[Dict[str, Any]], context: Dict[str, Any] = None) -> str:
        """Generate account response based on operation type"""
        if operation_type == "profile":
            return self._handle_profile_operation(query, articles)
        elif operation_type == "preferences":
            return self._handle_preferences_operation(query, articles)
        elif operation_type == "transfer":
            return self._handle_transfer_operation(query, articles)
        elif operation_type == "security":
            return self._handle_security_operation(query, articles)
        elif operation_type == "data":
            return self._handle_data_operation(query, articles)
        else:
            return self._handle_general_account(query, articles)
    
    def _handle_profile_operation(self, query: str, articles: List[Dict[str, Any]]) -> str:
        """Handle profile-related operations"""
        if "update" in query.lower() or "change" in query.lower():
            response = "To update your profile information:\n\n"
            response += "1. Go to 'My Account' > 'Profile' in the app\n"
            response += "2. Tap 'Edit' to modify your information\n"
            response += "3. Update your name, email, or other details\n"
            response += "4. Save your changes\n\n"
            response += "Your profile information is used to personalize your experience and for event communications."
        else:
            response = "Your profile information includes:\n\n"
            response += "• Name and contact information\n"
            response += "• Account preferences and settings\n"
            response += "• Experience history and favorites\n"
            response += "• Subscription details\n\n"
            response += "You can view and update your profile in the 'My Account' section of the app."
        
        return response
    
    def _handle_preferences_operation(self, query: str, articles: List[Dict[str, Any]]) -> str:
        """Handle preferences and settings operations"""
        response = "Account preferences and settings:\n\n"
        response += "• Notification preferences (email, push notifications)\n"
        response += "• Privacy settings (data sharing, visibility)\n"
        response += "• Experience preferences (categories, locations)\n"
        response += "• Language and regional settings\n\n"
        
        if "update" in query.lower() or "change" in query.lower():
            response += "To update your preferences:\n"
            response += "1. Go to 'My Account' > 'Preferences'\n"
            response += "2. Modify your notification and privacy settings\n"
            response += "3. Update your experience preferences\n"
            response += "4. Save your changes\n\n"
            response += "Changes take effect immediately."
        else:
            response += "You can manage all your preferences in the 'My Account' > 'Preferences' section."
        
        return response
    
    def _handle_transfer_operation(self, query: str, articles: List[Dict[str, Any]]) -> str:
        """Handle account transfer operations"""
        response = "Account transfers:\n\n"
        response += "• Account transfers require verification of the original account holder\n"
        response += "• Both parties must agree to the transfer\n"
        response += "• Remaining monthly credits are transferred\n"
        response += "• Transfer process takes 24-48 hours\n\n"
        
        response += "To request an account transfer:\n"
        response += "1. Contact our support team via email\n"
        response += "2. Include both account details\n"
        response += "3. Provide verification information\n"
        response += "4. Wait for approval and processing\n\n"
        response += "Note: Account transfers are final and cannot be reversed."
        
        return response
    
    def _handle_security_operation(self, query: str, articles: List[Dict[str, Any]]) -> str:
        """Handle security-related operations"""
        if "password" in query.lower():
            response = "Password management:\n\n"
            response += "• Use the 'Forgot Password' feature to reset your password\n"
            response += "• Ensure your email is correct and accessible\n"
            response += "• Check spam folder if you don't receive reset emails\n"
            response += "• Contact support if you continue having issues\n\n"
            response += "For security, we cannot reset passwords over chat."
        else:
            response = "Account security features:\n\n"
            response += "• Secure password requirements\n"
            response += "• Email verification for account changes\n"
            response += "• Session management and logout\n"
            response += "• Activity monitoring for suspicious behavior\n\n"
            response += "If you notice any suspicious activity, contact support immediately."
        
        return response
    
    def _handle_data_operation(self, query: str, articles: List[Dict[str, Any]]) -> str:
        """Handle data-related operations"""
        if "delete" in query.lower():
            response = "Account deletion:\n\n"
            response += "• Account deletion is permanent and cannot be undone\n"
            response += "• All data, history, and preferences will be lost\n"
            response += "• Active subscriptions will be cancelled\n"
            response += "• Contact support to request account deletion\n\n"
            response += "We'll guide you through the verification process."
        elif "export" in query.lower():
            response = "Data export:\n\n"
            response += "• You can request a copy of your personal data\n"
            response += "• Include your account information and experience history\n"
            response += "• Data will be provided in a standard format\n"
            response += "• Processing takes 3-5 business days\n\n"
            response += "Contact support to request your data export."
        else:
            response = "Data and privacy:\n\n"
            response += "• We collect only necessary information for service delivery\n"
            response += "• Your data is encrypted and securely stored\n"
            response += "• You can control data sharing in privacy settings\n"
            response += "• We never sell your personal information\n\n"
            response += "Review our privacy policy for detailed information."
        
        return response
    
    def _handle_general_account(self, query: str, articles: List[Dict[str, Any]]) -> str:
        """Handle general account inquiries"""
        response = "Account management options:\n\n"
        response += "• Update profile information and preferences\n"
        response += "• Manage privacy and security settings\n"
        response += "• View account history and activity\n"
        response += "• Request data export or account deletion\n"
        response += "• Transfer account to another user\n\n"
        response += "All account management features are available in the 'My Account' section of the app."
        
        return response
    
    def _requires_verification(self, operation_type: str) -> bool:
        """Determine if the operation requires verification"""
        verification_required_types = ["transfer", "security", "data"]
        return operation_type in verification_required_types
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences (placeholder for database integration)"""
        # In a real implementation, this would update the database
        return {
            "user_id": user_id,
            "status": "success",
            "message": "Preferences updated successfully",
            "updated_preferences": preferences,
            "updated_at": "2024-01-15T10:30:00Z"
        }
    
    def process_account_transfer(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process account transfer requests"""
        return {
            "transfer_id": f"TRF-{request.get('from_user')}-{request.get('to_user')}",
            "status": "pending_verification",
            "message": "Transfer request submitted for verification",
            "estimated_completion": "24-48 hours",
            "requires_verification": True
        }
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile information (placeholder for database integration)"""
        return {
            "user_id": user_id,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "preferences": {
                "notifications": "email",
                "privacy": "standard",
                "language": "en"
            },
            "account_created": "2023-01-15",
            "last_updated": "2024-01-15"
        }
    
    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process an account management query"""
        # Handle the account operation
        operation_result = self.handle_account_operations(query, context)
        
        # Check if escalation is needed
        needs_escalation = self._should_escalate_account(query, operation_result)
        
        # Extract support operations if available
        support_operations = []
        if context and "support_tools" in context:
            support_tools = context["support_tools"]
            
            # Check for account lookup requests
            if "look up" in query.lower() or "find account" in query.lower():
                support_operations.append("account_lookup")
            
            # Check for subscription management requests
            if "subscription" in query.lower() and ("update" in query.lower() or "change" in query.lower()):
                support_operations.append("subscription_management")
        
        return {
            "agent": "ACCOUNT",
            "response": operation_result["response"],
            "operation_type": operation_result["operation_type"],
            "requires_verification": operation_result["requires_verification"],
            "needs_escalation": needs_escalation,
            "confidence": 0.8 if operation_result.get("articles") else 0.6,
            "support_operations": support_operations
        }
    
    def _should_escalate_account(self, query: str, operation_result: Dict[str, Any]) -> bool:
        """Determine if account query should be escalated"""
        escalation_keywords = [
            "urgent", "emergency", "hacked", "compromised", "unauthorized access",
            "fraud", "complaint", "escalate", "manager", "supervisor"
        ]
        
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in escalation_keywords):
            return True
        
        # Escalate sensitive operations
        if operation_result.get("operation_type") in ["transfer", "data"]:
            return True
        
        return False
