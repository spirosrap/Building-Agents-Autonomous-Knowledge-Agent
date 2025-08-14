"""
Database Tools for Multi-Agent System

Tools for database operations including:
- User information retrieval
- Knowledge base queries
- Account status checks
- Ticket management
"""

from langchain.tools import BaseTool
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from typing import Dict, List, Any, Optional
import json

class DatabaseTool(BaseTool):
    name: str = "database_tool"
    description: str = "Tool for database operations including user info, knowledge base queries, and account management"
    core_engine: Any = None
    external_engine: Any = None
    
    def __init__(self, core_db_path: str, external_db_path: str):
        super().__init__()
        self.core_engine = create_engine(f"sqlite:///{core_db_path}")
        self.external_engine = create_engine(f"sqlite:///{external_db_path}")
    
    def _run(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute database operations"""
        try:
            if operation == "get_user":
                return self._get_user(kwargs.get("user_id"))
            elif operation == "get_knowledge_articles":
                return self._get_knowledge_articles(kwargs.get("query"))
            elif operation == "get_account_status":
                return self._get_account_status(kwargs.get("account_id"))
            elif operation == "get_user_tickets":
                return self._get_user_tickets(kwargs.get("user_id"))
            elif operation == "search_knowledge_by_tag":
                return self._search_knowledge_by_tag(kwargs.get("tag"))
            elif operation == "get_experiences":
                return self._get_experiences(kwargs.get("limit", 10))
            else:
                return {"error": f"Unknown operation: {operation}"}
        except Exception as e:
            return {"error": f"Database operation failed: {str(e)}"}
    
    def _get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user information from database"""
        with Session(self.core_engine) as session:
            # Query users table
            result = session.execute(
                text("SELECT * FROM users WHERE user_id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            
            if result:
                return {
                    "user_id": result.user_id,
                    "account_id": result.account_id,
                    "external_user_id": result.external_user_id,
                    "user_name": result.user_name,
                    "created_at": str(result.created_at),
                    "updated_at": str(result.updated_at)
                }
            else:
                return {"error": "User not found"}
    
    def _get_knowledge_articles(self, query: str) -> Dict[str, Any]:
        """Get knowledge base articles matching query"""
        with Session(self.core_engine) as session:
            # Simple text search in knowledge base
            result = session.execute(
                text("""
                    SELECT * FROM knowledge 
                    WHERE title LIKE :query OR content LIKE :query OR tags LIKE :query
                    LIMIT 5
                """),
                {"query": f"%{query}%"}
            ).fetchall()
            
            articles = []
            for row in result:
                articles.append({
                    "article_id": row.article_id,
                    "title": row.title,
                    "content": row.content,
                    "tags": row.tags,
                    "account_id": row.account_id
                })
            
            return {
                "articles": articles,
                "count": len(articles),
                "query": query
            }
    
    def _get_account_status(self, account_id: str) -> Dict[str, Any]:
        """Get account status and information"""
        with Session(self.core_engine) as session:
            result = session.execute(
                text("SELECT * FROM accounts WHERE account_id = :account_id"),
                {"account_id": account_id}
            ).fetchone()
            
            if result:
                return {
                    "account_id": result.account_id,
                    "account_name": result.account_name,
                    "created_at": str(result.created_at),
                    "updated_at": str(result.updated_at)
                }
            else:
                return {"error": "Account not found"}
    
    def _get_user_tickets(self, user_id: str) -> Dict[str, Any]:
        """Get user's support tickets"""
        with Session(self.core_engine) as session:
            result = session.execute(
                text("""
                    SELECT t.*, tm.status, tm.main_issue_type 
                    FROM tickets t 
                    LEFT JOIN ticket_metadata tm ON t.ticket_id = tm.ticket_id
                    WHERE t.user_id = :user_id
                    ORDER BY t.created_at DESC
                    LIMIT 10
                """),
                {"user_id": user_id}
            ).fetchall()
            
            tickets = []
            for row in result:
                tickets.append({
                    "ticket_id": row.ticket_id,
                    "channel": row.channel,
                    "status": row.status,
                    "issue_type": row.main_issue_type,
                    "created_at": str(row.created_at)
                })
            
            return {
                "tickets": tickets,
                "count": len(tickets),
                "user_id": user_id
            }
    
    def _search_knowledge_by_tag(self, tag: str) -> Dict[str, Any]:
        """Search knowledge base articles by tag"""
        with Session(self.core_engine) as session:
            result = session.execute(
                text("SELECT * FROM knowledge WHERE tags LIKE :tag"),
                {"tag": f"%{tag}%"}
            ).fetchall()
            
            articles = []
            for row in result:
                articles.append({
                    "article_id": row.article_id,
                    "title": row.title,
                    "content": row.content,
                    "tags": row.tags
                })
            
            return {
                "articles": articles,
                "count": len(articles),
                "tag": tag
            }
    
    def _get_experiences(self, limit: int = 10) -> Dict[str, Any]:
        """Get experiences from external database"""
        with Session(self.external_engine) as session:
            result = session.execute(
                text("SELECT * FROM experiences ORDER BY when DESC LIMIT :limit"),
                {"limit": limit}
            ).fetchall()
            
            experiences = []
            for row in result:
                experiences.append({
                    "experience_id": row.experience_id,
                    "title": row.title,
                    "description": row.description,
                    "location": row.location,
                    "when": str(row.when),
                    "slots_available": row.slots_available,
                    "is_premium": row.is_premium
                })
            
            return {
                "experiences": experiences,
                "count": len(experiences)
            }
    
    def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """Get user by email from external database"""
        with Session(self.external_engine) as session:
            result = session.execute(
                text("SELECT * FROM users WHERE email = :email"),
                {"email": email}
            ).fetchone()
            
            if result:
                return {
                    "user_id": result.user_id,
                    "name": result.full_name,
                    "email": result.email,
                    "is_blocked": result.is_blocked
                }
            else:
                return {"error": "User not found"}
    
    def create_ticket(self, user_id: str, account_id: str, channel: str = "chat") -> Dict[str, Any]:
        """Create a new support ticket"""
        import uuid
        from datetime import datetime
        
        ticket_id = str(uuid.uuid4())
        
        with Session(self.core_engine) as session:
            # Create ticket
            session.execute(
                text("""
                    INSERT INTO tickets (ticket_id, account_id, user_id, channel, created_at)
                    VALUES (:ticket_id, :account_id, :user_id, :channel, :created_at)
                """),
                {
                    "ticket_id": ticket_id,
                    "account_id": account_id,
                    "user_id": user_id,
                    "channel": channel,
                    "created_at": datetime.now()
                }
            )
            
            # Create ticket metadata
            session.execute(
                text("""
                    INSERT INTO ticket_metadata (ticket_id, status, created_at, updated_at)
                    VALUES (:ticket_id, 'open', :created_at, :updated_at)
                """),
                {
                    "ticket_id": ticket_id,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            )
            
            session.commit()
            
            return {
                "ticket_id": ticket_id,
                "status": "created",
                "user_id": user_id,
                "account_id": account_id,
                "channel": channel
            }
    
    def add_ticket_message(self, ticket_id: str, role: str, content: str) -> Dict[str, Any]:
        """Add a message to a ticket"""
        import uuid
        from datetime import datetime
        
        message_id = str(uuid.uuid4())
        
        with Session(self.core_engine) as session:
            session.execute(
                text("""
                    INSERT INTO ticket_messages (message_id, ticket_id, role, content, created_at)
                    VALUES (:message_id, :ticket_id, :role, :content, :created_at)
                """),
                {
                    "message_id": message_id,
                    "ticket_id": ticket_id,
                    "role": role,
                    "content": content,
                    "created_at": datetime.now()
                }
            )
            
            session.commit()
            
            return {
                "message_id": message_id,
                "ticket_id": ticket_id,
                "role": role,
                "content": content,
                "status": "added"
            }
