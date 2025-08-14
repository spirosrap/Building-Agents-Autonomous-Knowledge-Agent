"""
Technical Support Agent - Expert in Technical Issues and Troubleshooting

This agent is responsible for:
- Diagnosing technical problems
- Providing step-by-step troubleshooting guidance
- Handling login and access issues
- Managing technical escalations
- Tracking technical issue patterns
"""

from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import json
import re

class TechnicalSupportAgent:
    def __init__(self, llm: ChatOpenAI, knowledge_base_agent=None):
        self.llm = llm
        self.knowledge_base_agent = knowledge_base_agent
        self.system_prompt = self._create_system_prompt()
        self.technical_keywords = self._create_technical_keywords()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the technical support agent"""
        return """You are the Technical Support Agent for Uda-hub, a customer support system for CultPass users. Your role is to:

1. DIAGNOSE technical problems accurately
2. PROVIDE step-by-step troubleshooting guidance
3. HANDLE login and access issues
4. MANAGE technical escalations when needed
5. TRACK technical issue patterns

Common technical issues you handle:
- Login problems (password reset, account lockout)
- App crashes and performance issues
- QR code problems for event entry
- Network connectivity issues
- Device compatibility problems
- Error messages and system failures

Always provide clear, actionable steps. If the issue is complex or requires system access, escalate to human support."""
    
    def _create_technical_keywords(self) -> Dict[str, List[str]]:
        """Create technical keywords for issue classification"""
        return {
            "login": ["login", "password", "sign in", "authentication", "access", "locked out"],
            "app_issues": ["crash", "freeze", "slow", "not responding", "error", "bug"],
            "qr_code": ["qr code", "scan", "entry", "ticket", "reservation"],
            "network": ["connection", "internet", "wifi", "network", "offline"],
            "device": ["phone", "android", "ios", "tablet", "device", "compatibility"],
            "performance": ["slow", "lag", "loading", "timeout", "performance"]
        }
    
    def diagnose_technical_issue(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Diagnose technical issues based on user query"""
        query_lower = query.lower()
        
        # Classify the technical issue
        issue_type = self._classify_issue(query_lower)
        
        # Get relevant technical articles
        technical_articles = []
        if self.knowledge_base_agent:
            technical_articles = self.knowledge_base_agent.get_articles_by_tag("technical")
        
        # Generate diagnosis
        diagnosis = self._generate_diagnosis(query, issue_type, technical_articles)
        
        return {
            "issue_type": issue_type,
            "diagnosis": diagnosis,
            "severity": self._assess_severity(issue_type, query_lower),
            "articles": technical_articles
        }
    
    def _classify_issue(self, query: str) -> str:
        """Classify the type of technical issue"""
        for issue_type, keywords in self.technical_keywords.items():
            if any(keyword in query for keyword in keywords):
                return issue_type
        
        return "general_technical"
    
    def _generate_diagnosis(self, query: str, issue_type: str, articles: List[Dict[str, Any]]) -> str:
        """Generate technical diagnosis"""
        diagnosis_prompt = f"""Analyze this technical issue: "{query}"

Issue Type: {issue_type}

Available Technical Articles:
{self._format_articles_for_diagnosis(articles)}

Provide a clear diagnosis of the problem and suggest initial troubleshooting steps."""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=diagnosis_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def _format_articles_for_diagnosis(self, articles: List[Dict[str, Any]]) -> str:
        """Format articles for diagnosis context"""
        if not articles:
            return "No specific technical articles available."
        
        formatted = ""
        for i, article in enumerate(articles[:3], 1):  # Limit to top 3 articles
            formatted += f"\n{i}. {article.get('title', 'No title')}\n"
            formatted += f"   {article.get('content', 'No content')[:200]}...\n"
        
        return formatted
    
    def _assess_severity(self, issue_type: str, query: str) -> str:
        """Assess the severity of the technical issue"""
        high_severity_keywords = ["urgent", "critical", "emergency", "broken", "not working", "failed"]
        medium_severity_keywords = ["problem", "issue", "trouble", "difficulty"]
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in high_severity_keywords):
            return "HIGH"
        elif any(keyword in query_lower for keyword in medium_severity_keywords):
            return "MEDIUM"
        else:
            return "LOW"
    
    def provide_troubleshooting_steps(self, diagnosis: Dict[str, Any]) -> List[str]:
        """Provide step-by-step troubleshooting"""
        issue_type = diagnosis.get("issue_type", "general_technical")
        severity = diagnosis.get("severity", "LOW")
        
        # Get relevant troubleshooting steps
        steps = self._get_troubleshooting_steps(issue_type, severity)
        
        # Generate custom steps if needed
        if not steps:
            steps = self._generate_custom_troubleshooting(diagnosis)
        
        return steps
    
    def _get_troubleshooting_steps(self, issue_type: str, severity: str) -> List[str]:
        """Get predefined troubleshooting steps"""
        steps_map = {
            "login": [
                "1. Try the 'Forgot Password' feature",
                "2. Check if your email is correct",
                "3. Clear browser cache and cookies",
                "4. Try logging in from a different device",
                "5. Contact support if the issue persists"
            ],
            "app_issues": [
                "1. Force close and restart the app",
                "2. Check for app updates",
                "3. Restart your device",
                "4. Clear app cache and data",
                "5. Reinstall the app if necessary"
            ],
            "qr_code": [
                "1. Ensure your QR code is clearly visible",
                "2. Check your phone's brightness",
                "3. Try refreshing the QR code in the app",
                "4. Contact the event organizer",
                "5. Bring a backup (email confirmation)"
            ],
            "network": [
                "1. Check your internet connection",
                "2. Try switching between WiFi and mobile data",
                "3. Restart your router/modem",
                "4. Check if other apps work",
                "5. Try again in a few minutes"
            ]
        }
        
        return steps_map.get(issue_type, [
            "1. Restart the application",
            "2. Check your internet connection",
            "3. Update the app to the latest version",
            "4. Contact customer support for assistance"
        ])
    
    def _generate_custom_troubleshooting(self, diagnosis: Dict[str, Any]) -> List[str]:
        """Generate custom troubleshooting steps"""
        diagnosis_text = diagnosis.get("diagnosis", "")
        
        prompt = f"""Based on this technical diagnosis, provide 3-5 specific troubleshooting steps:

Diagnosis: {diagnosis_text}

Provide clear, actionable steps that the user can follow."""
        
        messages = [
            SystemMessage(content="You are a technical support expert. Provide clear, step-by-step troubleshooting instructions."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse response into steps
        steps = []
        for line in response.content.split('\n'):
            line = line.strip()
            if line and (line.startswith(('1.', '2.', '3.', '4.', '5.')) or line.startswith(('•', '-'))):
                steps.append(line)
        
        return steps if steps else ["Contact technical support for assistance"]
    
    def check_user_status(self, user_id: str) -> Dict[str, Any]:
        """Check user technical status (placeholder for database integration)"""
        # In a real implementation, this would query the database
        return {
            "user_id": user_id,
            "account_status": "active",
            "last_login": "2024-01-15",
            "device_info": "iOS 17.0",
            "app_version": "2.1.0",
            "technical_issues": []
        }
    
    def should_escalate(self, diagnosis: Dict[str, Any]) -> bool:
        """Determine if technical issue should be escalated"""
        severity = diagnosis.get("severity", "LOW")
        issue_type = diagnosis.get("issue_type", "general_technical")
        
        # Escalate high severity issues
        if severity == "HIGH":
            return True
        
        # Escalate certain issue types
        if issue_type in ["security", "data_loss", "account_compromise"]:
            return True
        
        return False
    
    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a technical support query"""
        # Diagnose the issue
        diagnosis = self.diagnose_technical_issue(query, context)
        
        # Get troubleshooting steps
        troubleshooting_steps = self.provide_troubleshooting_steps(diagnosis)
        
        # Check if escalation is needed
        needs_escalation = self.should_escalate(diagnosis)
        
        # Generate response
        response = self._generate_technical_response(diagnosis, troubleshooting_steps, needs_escalation)
        
        return {
            "agent": "TECHNICAL",
            "response": response,
            "diagnosis": diagnosis,
            "troubleshooting_steps": troubleshooting_steps,
            "needs_escalation": needs_escalation,
            "confidence": 0.8 if diagnosis.get("articles") else 0.6
        }
    
    def _generate_technical_response(self, diagnosis: Dict[str, Any], steps: List[str], escalation: bool) -> str:
        """Generate technical support response"""
        issue_type = diagnosis.get("issue_type", "technical issue")
        severity = diagnosis.get("severity", "LOW")
        
        response = f"I understand you're experiencing a {issue_type} issue. "
        
        if escalation:
            response += "This appears to be a complex technical issue that requires immediate attention. "
            response += "I'm escalating this to our technical support team who will contact you shortly. "
            response += "In the meantime, here are some initial troubleshooting steps:\n\n"
        else:
            response += "Here are some troubleshooting steps to resolve this issue:\n\n"
        
        # Add troubleshooting steps
        for step in steps:
            response += f"{step}\n"
        
        if escalation:
            response += "\nOur technical team will provide more detailed assistance."
        else:
            response += "\nIf these steps don't resolve the issue, please contact our support team."
        
        return response
