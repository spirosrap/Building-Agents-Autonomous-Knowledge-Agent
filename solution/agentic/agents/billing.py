"""
Billing Agent - Expert in Payment, Subscription, and Billing Matters

This agent is responsible for:
- Handling subscription inquiries
- Processing payment updates
- Managing refund requests
- Explaining billing policies
- Handling premium event pricing
"""

from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import json
import re

class BillingAgent:
    def __init__(self, llm: ChatOpenAI, knowledge_base_agent=None):
        self.llm = llm
        self.knowledge_base_agent = knowledge_base_agent
        self.system_prompt = self._create_system_prompt()
        self.billing_keywords = self._create_billing_keywords()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the billing agent"""
        return """You are the Billing Agent for Uda-hub, a customer support system for CultPass users. Your role is to:

1. HANDLE subscription inquiries and explain benefits
2. PROCESS payment information updates
3. MANAGE refund requests according to policy
4. EXPLAIN billing policies and pricing
5. HANDLE premium event pricing questions

Important billing policies:
- Subscriptions are billed monthly and include 4 experiences
- Premium events may have additional costs
- Refunds require approval from support lead
- Payment updates require verification
- Subscription changes take effect at billing cycle end

Always be clear about policies and limitations. For refunds, explain the process but note that approval is required."""
    
    def _create_billing_keywords(self) -> Dict[str, List[str]]:
        """Create billing keywords for query classification"""
        return {
            "subscription": ["subscription", "plan", "monthly", "billing cycle", "renewal"],
            "payment": ["payment", "card", "credit", "debit", "billing", "charge"],
            "refund": ["refund", "money back", "cancel", "return", "reimbursement"],
            "premium": ["premium", "extra cost", "additional fee", "upgrade"],
            "pricing": ["cost", "price", "fee", "how much", "pricing"]
        }
    
    def handle_billing_inquiry(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle billing and subscription inquiries"""
        query_lower = query.lower()
        
        # Classify the billing inquiry
        inquiry_type = self._classify_inquiry(query_lower)
        
        # Get relevant billing articles
        billing_articles = []
        if self.knowledge_base_agent:
            billing_articles = self.knowledge_base_agent.get_articles_by_tag("billing")
        
        # Generate response
        response = self._generate_billing_response(query, inquiry_type, billing_articles, user_context)
        
        return {
            "inquiry_type": inquiry_type,
            "response": response,
            "articles": billing_articles,
            "requires_action": self._requires_action(inquiry_type)
        }
    
    def _classify_inquiry(self, query: str) -> str:
        """Classify the type of billing inquiry"""
        for inquiry_type, keywords in self.billing_keywords.items():
            if any(keyword in query for keyword in keywords):
                return inquiry_type
        
        return "general_billing"
    
    def _generate_billing_response(self, query: str, inquiry_type: str, articles: List[Dict[str, Any]], context: Dict[str, Any] = None) -> str:
        """Generate billing response based on inquiry type"""
        if inquiry_type == "subscription":
            return self._handle_subscription_inquiry(query, articles)
        elif inquiry_type == "payment":
            return self._handle_payment_inquiry(query, articles)
        elif inquiry_type == "refund":
            return self._handle_refund_inquiry(query, articles)
        elif inquiry_type == "premium":
            return self._handle_premium_inquiry(query, articles)
        elif inquiry_type == "pricing":
            return self._handle_pricing_inquiry(query, articles)
        else:
            return self._handle_general_billing(query, articles)
    
    def _handle_subscription_inquiry(self, query: str, articles: List[Dict[str, Any]]) -> str:
        """Handle subscription-related inquiries"""
        response = "Your CultPass subscription includes:\n\n"
        response += "• 4 cultural experiences per month\n"
        response += "• Access to museums, concerts, film events, and more\n"
        response += "• Premium events may have additional costs\n"
        response += "• Billing occurs monthly\n\n"
        
        if "cancel" in query.lower() or "pause" in query.lower():
            response += "To manage your subscription:\n"
            response += "• Go to 'My Account' > 'Manage Plan' in the app\n"
            response += "• Changes take effect at the end of your billing cycle\n"
            response += "• Pausing preserves your data and automatically resumes when reactivated\n"
        else:
            response += "You can view your current subscription status in the 'My Account' section of the app."
        
        return response
    
    def _handle_payment_inquiry(self, query: str, articles: List[Dict[str, Any]]) -> str:
        """Handle payment-related inquiries"""
        if "update" in query.lower() or "change" in query.lower():
            response = "To update your payment information:\n\n"
            response += "1. Go to 'My Account' > 'Payment Methods' in the app\n"
            response += "2. Tap 'Add New Card' or 'Edit' existing card\n"
            response += "3. Enter your new card details securely\n"
            response += "4. Ensure your billing address matches your card issuer's records\n\n"
            response += "Your payment information is encrypted and secure."
        else:
            response = "For payment-related questions, you can:\n\n"
            response += "• View your payment history in the app\n"
            response += "• Update payment methods in 'My Account' > 'Payment Methods'\n"
            response += "• Contact support for billing disputes\n"
        
        return response
    
    def _handle_refund_inquiry(self, query: str, articles: List[Dict[str, Any]]) -> str:
        """Handle refund requests"""
        response = "Regarding refunds:\n\n"
        response += "• Refunds require approval from our support lead\n"
        response += "• Please contact our support team with your refund request\n"
        response += "• Include details about your purchase and reason for refund\n"
        response += "• We'll review your request and respond within 24 hours\n\n"
        response += "Note: Premium event cancellations may have different refund policies."
        
        return response
    
    def _handle_premium_inquiry(self, query: str, articles: List[Dict[str, Any]]) -> str:
        """Handle premium event inquiries"""
        response = "Premium events:\n\n"
        response += "• Premium events have additional costs beyond your monthly subscription\n"
        response += "• The cost is clearly displayed when you reserve\n"
        response += "• Payment is processed immediately\n"
        response += "• Premium events count toward your monthly experience limit\n"
        response += "• No refunds for premium event cancellations\n\n"
        response += "You can see premium event pricing in the app when browsing experiences."
        
        return response
    
    def _handle_pricing_inquiry(self, query: str, articles: List[Dict[str, Any]]) -> str:
        """Handle general pricing inquiries"""
        response = "CultPass pricing:\n\n"
        response += "• Monthly subscription: $X (includes 4 experiences)\n"
        response += "• Premium events: Additional cost varies by event\n"
        response += "• No hidden fees or charges\n"
        response += "• Billing occurs monthly on your renewal date\n\n"
        response += "You can view detailed pricing in the app under 'Subscription' in your account settings."
        
        return response
    
    def _handle_general_billing(self, query: str, articles: List[Dict[str, Any]]) -> str:
        """Handle general billing inquiries"""
        response = "For billing and payment questions:\n\n"
        response += "• Check your subscription status in 'My Account'\n"
        response += "• View payment history and upcoming charges\n"
        response += "• Update payment methods as needed\n"
        response += "• Contact support for specific billing issues\n\n"
        response += "Is there a specific billing question I can help you with?"
        
        return response
    
    def _requires_action(self, inquiry_type: str) -> bool:
        """Determine if the inquiry requires a specific action"""
        action_required_types = ["payment", "refund"]
        return inquiry_type in action_required_types
    
    def process_payment_update(self, user_id: str, payment_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment information updates (placeholder for database integration)"""
        # In a real implementation, this would update the database
        return {
            "user_id": user_id,
            "status": "success",
            "message": "Payment information updated successfully",
            "updated_at": "2024-01-15T10:30:00Z",
            "requires_verification": True
        }
    
    def handle_refund_request(self, user_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle refund requests"""
        return {
            "user_id": user_id,
            "request_id": f"REF-{user_id}-{hash(str(request))}",
            "status": "pending_approval",
            "message": "Refund request submitted for approval",
            "estimated_response_time": "24 hours",
            "requires_support_lead": True
        }
    
    def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """Get user subscription status (placeholder for database integration)"""
        return {
            "user_id": user_id,
            "subscription_status": "active",
            "plan": "monthly",
            "experiences_used": 2,
            "experiences_remaining": 2,
            "next_billing_date": "2024-02-15",
            "monthly_cost": "$X"
        }
    
    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a billing query"""
        # Handle the billing inquiry
        inquiry_result = self.handle_billing_inquiry(query, context)
        
        # Check if escalation is needed
        needs_escalation = self._should_escalate_billing(query, inquiry_result)
        
        # Extract support operations if available
        support_operations = []
        if context and "support_tools" in context:
            support_tools = context["support_tools"]
            
            # Check for subscription management requests
            if "subscription" in query.lower() and "cancel" in query.lower():
                support_operations.append("subscription_cancellation")
            
            # Check for refund requests
            if "refund" in query.lower():
                support_operations.append("refund_processing")
        
        return {
            "agent": "BILLING",
            "response": inquiry_result["response"],
            "inquiry_type": inquiry_result["inquiry_type"],
            "requires_action": inquiry_result["requires_action"],
            "needs_escalation": needs_escalation,
            "confidence": 0.9 if inquiry_result.get("articles") else 0.7,
            "support_operations": support_operations
        }
    
    def _should_escalate_billing(self, query: str, inquiry_result: Dict[str, Any]) -> bool:
        """Determine if billing query should be escalated"""
        escalation_keywords = [
            "urgent", "emergency", "dispute", "fraud", "unauthorized", "wrong charge",
            "complaint", "escalate", "manager", "supervisor"
        ]
        
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in escalation_keywords):
            return True
        
        # Escalate refund requests
        if inquiry_result.get("inquiry_type") == "refund":
            return True
        
        return False
