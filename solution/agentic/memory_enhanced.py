"""
Enhanced Memory System for Agent Workflows

Implements different types of memory in agent workflows:
- State memory: During multi-step interactions in one execution
- Session memory: Short-term context for conversation continuity
- Long-term memory: Resolved issues and customer preferences across sessions
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import uuid
from enum import Enum
from sqlalchemy import create_engine, and_, select, desc
from sqlalchemy.orm import Session

# Import Uda-hub ORM models
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data', 'models'))
from udahub import Base as UdaBase
from udahub import Account, User, Ticket, TicketMetadata, TicketMessage, RoleEnum

class MemoryType(Enum):
    STATE = "state"
    SESSION = "session"
    LONG_TERM = "long_term"

@dataclass
class MemoryEntry:
    """Individual memory entry"""
    memory_id: str
    memory_type: MemoryType
    key: str
    value: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0

@dataclass
class SessionContext:
    """Session-level context and state"""
    session_id: str
    thread_id: str
    user_id: str
    conversation_id: str
    start_time: datetime
    current_step: int = 0
    state_data: Dict[str, Any] = field(default_factory=dict)
    session_memory: Dict[str, Any] = field(default_factory=dict)
    tool_usage: List[Dict[str, Any]] = field(default_factory=list)
    messages: List[Dict[str, Any]] = field(default_factory=list)

class EnhancedMemoryManager:
    """
    Enhanced memory manager implementing state, session, and long-term memory
    with proper integration into agent decision-making.
    """
    
    def __init__(self, core_db_path: str):
        self.core_db_path = core_db_path
        self.engine = create_engine(f"sqlite:///{core_db_path}")
        UdaBase.metadata.create_all(self.engine)
        
        # In-memory storage for state and session memory
        self.state_memory: Dict[str, Dict[str, MemoryEntry]] = {}
        self.session_memory: Dict[str, SessionContext] = {}
        self.long_term_cache: Dict[str, Dict[str, MemoryEntry]] = {}
    
    # -------------------------- State Memory -------------------------- #
    
    def set_state(self, session_id: str, key: str, value: Any, metadata: Dict[str, Any] = None) -> str:
        """Set state memory for multi-step interactions"""
        if session_id not in self.state_memory:
            self.state_memory[session_id] = {}
        
        memory_id = f"state_{uuid.uuid4().hex[:8]}"
        entry = MemoryEntry(
            memory_id=memory_id,
            memory_type=MemoryType.STATE,
            key=key,
            value=value,
            metadata=metadata or {}
        )
        
        self.state_memory[session_id][key] = entry
        return memory_id
    
    def get_state(self, session_id: str, key: str, default: Any = None) -> Any:
        """Get state memory value"""
        if session_id in self.state_memory and key in self.state_memory[session_id]:
            entry = self.state_memory[session_id][key]
            entry.accessed_at = datetime.now()
            entry.access_count += 1
            return entry.value
        return default
    
    def update_state(self, session_id: str, key: str, value: Any) -> bool:
        """Update existing state memory"""
        if session_id in self.state_memory and key in self.state_memory[session_id]:
            entry = self.state_memory[session_id][key]
            entry.value = value
            entry.accessed_at = datetime.now()
            return True
        return False
    
    def clear_state(self, session_id: str, key: str = None) -> bool:
        """Clear state memory"""
        if session_id in self.state_memory:
            if key:
                if key in self.state_memory[session_id]:
                    del self.state_memory[session_id][key]
                    return True
            else:
                del self.state_memory[session_id]
                return True
        return False
    
    # -------------------------- Session Memory -------------------------- #
    
    def create_session(self, thread_id: str, user_id: str, conversation_id: str) -> str:
        """Create a new session context"""
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        session_context = SessionContext(
            session_id=session_id,
            thread_id=thread_id,
            user_id=user_id,
            conversation_id=conversation_id,
            start_time=datetime.now()
        )
        self.session_memory[session_id] = session_context
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Get session context"""
        return self.session_memory.get(session_id)
    
    def update_session_step(self, session_id: str, step: int) -> bool:
        """Update current step in session"""
        if session_id in self.session_memory:
            self.session_memory[session_id].current_step = step
            return True
        return False
    
    def add_session_message(self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """Add message to session memory"""
        if session_id in self.session_memory:
            message_id = f"msg_{uuid.uuid4().hex[:8]}"
            message = {
                "message_id": message_id,
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            self.session_memory[session_id].messages.append(message)
            return message_id
        return None
    
    def add_tool_usage(self, session_id: str, tool_name: str, parameters: Dict[str, Any], result: Any) -> str:
        """Record tool usage in session"""
        if session_id in self.session_memory:
            usage_id = f"tool_{uuid.uuid4().hex[:8]}"
            usage = {
                "usage_id": usage_id,
                "tool_name": tool_name,
                "parameters": parameters,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            self.session_memory[session_id].tool_usage.append(usage)
            return usage_id
        return None
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get session summary for context"""
        if session_id not in self.session_memory:
            return {}
        
        session = self.session_memory[session_id]
        return {
            "session_id": session.session_id,
            "thread_id": session.thread_id,
            "user_id": session.user_id,
            "conversation_id": session.conversation_id,
            "current_step": session.current_step,
            "message_count": len(session.messages),
            "tool_usage_count": len(session.tool_usage),
            "session_duration": (datetime.now() - session.start_time).total_seconds(),
            "recent_messages": session.messages[-5:] if session.messages else [],
            "recent_tools": session.tool_usage[-3:] if session.tool_usage else []
        }
    
    # -------------------------- Long-term Memory -------------------------- #
    
    def store_long_term(self, user_id: str, key: str, value: Any, metadata: Dict[str, Any] = None) -> str:
        """Store long-term memory (resolved issues, preferences)"""
        if user_id not in self.long_term_cache:
            self.long_term_cache[user_id] = {}
        
        memory_id = f"lt_{uuid.uuid4().hex[:8]}"
        entry = MemoryEntry(
            memory_id=memory_id,
            memory_type=MemoryType.LONG_TERM,
            key=key,
            value=value,
            metadata=metadata or {}
        )
        
        self.long_term_cache[user_id][key] = entry
        
        # Also persist to database for durability
        self._persist_long_term_memory(user_id, key, value, metadata)
        
        return memory_id
    
    def get_long_term(self, user_id: str, key: str, default: Any = None) -> Any:
        """Get long-term memory value"""
        # Try cache first
        if user_id in self.long_term_cache and key in self.long_term_cache[user_id]:
            entry = self.long_term_cache[user_id][key]
            entry.accessed_at = datetime.now()
            entry.access_count += 1
            return entry.value
        
        # Try database
        value = self._retrieve_long_term_memory(user_id, key)
        if value is not None:
            # Cache it
            if user_id not in self.long_term_cache:
                self.long_term_cache[user_id] = {}
            self.long_term_cache[user_id][key] = MemoryEntry(
                memory_id=f"lt_{uuid.uuid4().hex[:8]}",
                memory_type=MemoryType.LONG_TERM,
                key=key,
                value=value,
                accessed_at=datetime.now(),
                access_count=1
            )
            return value
        
        return default
    
    def _persist_long_term_memory(self, user_id: str, key: str, value: Any, metadata: Dict[str, Any] = None):
        """Persist long-term memory to database"""
        try:
            with Session(self.engine) as session:
                # Store as a special message in the database
                message_id = f"lt_{uuid.uuid4().hex[:8]}"
                message = TicketMessage(
                    message_id=message_id,
                    ticket_id=f"lt-{user_id}",  # Special ticket for long-term memory
                    role=RoleEnum.system,
                    content=json.dumps({
                        "type": "long_term_memory",
                        "key": key,
                        "value": value,
                        "metadata": metadata or {}
                    })
                )
                session.add(message)
                session.commit()
        except Exception:
            pass  # Fail gracefully
    
    def _retrieve_long_term_memory(self, user_id: str, key: str) -> Any:
        """Retrieve long-term memory from database"""
        try:
            with Session(self.engine) as session:
                messages = session.query(TicketMessage).filter(
                    and_(
                        TicketMessage.ticket_id == f"lt-{user_id}",
                        TicketMessage.role == RoleEnum.system
                    )
                ).order_by(desc(TicketMessage.created_at)).all()
                
                for msg in messages:
                    try:
                        data = json.loads(msg.content)
                        if data.get("type") == "long_term_memory" and data.get("key") == key:
                            return data.get("value")
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        return None
    
    # -------------------------- Agent Decision Integration -------------------------- #
    
    def get_context_for_agent(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Get comprehensive context for agent decision-making"""
        context = {
            "session": self.get_session_summary(session_id),
            "state": {},
            "long_term": {},
            "conversation_history": []
        }
        
        # Add state memory
        if session_id in self.state_memory:
            context["state"] = {
                key: {
                    "value": entry.value,
                    "metadata": entry.metadata,
                    "access_count": entry.access_count
                }
                for key, entry in self.state_memory[session_id].items()
            }
        
        # Add long-term memory
        if user_id in self.long_term_cache:
            context["long_term"] = {
                key: {
                    "value": entry.value,
                    "metadata": entry.metadata,
                    "access_count": entry.access_count
                }
                for key, entry in self.long_term_cache[user_id].items()
            }
        
        # Add conversation history from database
        try:
            with Session(self.engine) as session:
                # Get recent conversations for this user
                tickets = session.query(Ticket).filter(Ticket.user_id == user_id).order_by(desc(Ticket.created_at)).limit(3).all()
                
                for ticket in tickets:
                    messages = session.query(TicketMessage).filter(
                        TicketMessage.ticket_id == ticket.ticket_id
                    ).order_by(TicketMessage.created_at.desc()).limit(10).all()
                    
                    conversation = {
                        "ticket_id": ticket.ticket_id,
                        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                        "messages": [
                            {
                                "role": msg.role.value,
                                "content": msg.content,
                                "timestamp": msg.created_at.isoformat() if msg.created_at else None
                            }
                            for msg in messages
                        ]
                    }
                    context["conversation_history"].append(conversation)
        except Exception:
            pass
        
        return context
    
    def update_agent_context(self, session_id: str, user_id: str, agent_decision: Dict[str, Any]) -> None:
        """Update context based on agent decisions"""
        # Store agent decision in state memory
        self.set_state(session_id, "last_agent_decision", agent_decision, {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_decision.get("agent"),
            "confidence": agent_decision.get("confidence")
        })
        
        # Update session step
        current_step = self.get_state(session_id, "current_step", 0)
        self.update_session_step(session_id, current_step + 1)
        
        # Store in long-term memory if it's a resolved issue
        if agent_decision.get("resolved", False):
            issue_key = f"resolved_issue_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.store_long_term(user_id, issue_key, {
                "issue": agent_decision.get("issue"),
                "resolution": agent_decision.get("resolution"),
                "agent": agent_decision.get("agent"),
                "resolved_at": datetime.now().isoformat()
            })
    
    def get_memory_statistics(self, user_id: str = None) -> Dict[str, Any]:
        """Get memory usage statistics"""
        stats = {
            "state_memory_sessions": len(self.state_memory),
            "session_memory_sessions": len(self.session_memory),
            "long_term_users": len(self.long_term_cache)
        }
        
        if user_id:
            stats["user_state_entries"] = len(self.state_memory.get(user_id, {}))
            stats["user_long_term_entries"] = len(self.long_term_cache.get(user_id, {}))
        
        return stats
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up expired session memory"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        expired_sessions = []
        
        for session_id, session in self.session_memory.items():
            if session.start_time < cutoff_time:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.session_memory[session_id]
            if session_id in self.state_memory:
                del self.state_memory[session_id]
        
        return len(expired_sessions)
