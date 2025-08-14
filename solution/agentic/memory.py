"""
Persistent Conversation Memory Manager

Stores and retrieves customer interaction history using the core (Uda-hub)
SQLite database. Provides utilities to:
- Ensure an account and user exist
- Create/retrieve a conversation ticket
- Persist user/AI messages as `ticket_messages`
- Retrieve historical context for personalization
"""
from __future__ import annotations

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid

from sqlalchemy import create_engine, and_, select
from sqlalchemy.orm import Session

# Import Uda-hub ORM models
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data', 'models'))
from udahub import Base as UdaBase  # type: ignore
from udahub import Account, User, Ticket, TicketMetadata, TicketMessage, RoleEnum  # type: ignore


@dataclass
class ConversationStats:
    user_id: str
    total_tickets: int
    total_messages: int
    last_interaction_at: Optional[datetime]


class ConversationMemoryManager:
    def __init__(self, core_db_path: str):
        self.core_db_path = core_db_path
        self.engine = create_engine(f"sqlite:///{core_db_path}")
        # Ensure metadata is available (tables are created elsewhere during setup)
        UdaBase.metadata.create_all(self.engine)

    # -------------------------- Ensurers -------------------------- #
    def ensure_account(self, account_id: str = "acc-default", account_name: str = "Default Account") -> str:
        with Session(self.engine) as session:
            account = session.get(Account, account_id)
            if not account:
                account = Account(account_id=account_id, account_name=account_name)
                session.add(account)
                session.commit()
            return account.account_id

    def ensure_user(self, user_id: str, account_id: str = "acc-default", user_name: Optional[str] = None) -> str:
        self.ensure_account(account_id)
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            if not user:
                user = User(
                    user_id=user_id,
                    account_id=account_id,
                    external_user_id=user_id,
                    user_name=user_name or f"User {user_id}"
                )
                session.add(user)
                session.commit()
            return user.user_id

    def ensure_conversation(self, user_id: str, conversation_id: Optional[str] = None, channel: str = "app") -> str:
        """Get or create a `tickets` row representing the conversation."""
        ticket_id = conversation_id or f"conv-{uuid.uuid4().hex[:8]}"
        with Session(self.engine) as session:
            ticket = session.get(Ticket, ticket_id)
            if not ticket:
                # Ensure user exists (and default account)
                self.ensure_user(user_id)
                # Create ticket
                user = session.get(User, user_id)
                ticket = Ticket(
                    ticket_id=ticket_id,
                    account_id=user.account_id,
                    user_id=user.user_id,
                    channel=channel,
                )
                session.add(ticket)
                # Create metadata with default status
                metadata = TicketMetadata(
                    ticket_id=ticket_id,
                    status="open",
                    main_issue_type="general",
                    tags="[]"
                )
                session.add(metadata)
                session.commit()
            return ticket.ticket_id

    # -------------------------- Writes --------------------------- #
    def add_user_message(self, ticket_id: str, content: str) -> str:
        return self._add_message(ticket_id, RoleEnum.user, content)

    def add_ai_message(self, ticket_id: str, content: str) -> str:
        return self._add_message(ticket_id, RoleEnum.ai, content)

    def _add_message(self, ticket_id: str, role: RoleEnum, content: str) -> str:
        with Session(self.engine) as session:
            message_id = f"msg-{uuid.uuid4().hex[:10]}"
            message = TicketMessage(
                message_id=message_id,
                ticket_id=ticket_id,
                role=role,
                content=content,
            )
            session.add(message)
            session.commit()
            return message_id

    # -------------------------- Reads ---------------------------- #
    def get_conversation_messages(self, ticket_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with Session(self.engine) as session:
            q = (
                session.query(TicketMessage)
                .filter(TicketMessage.ticket_id == ticket_id)
                .order_by(TicketMessage.created_at.asc())
            )
            if limit:
                q = q.limit(limit)
            rows = q.all()
            return [
                {
                    "message_id": r.message_id,
                    "role": r.role.value,
                    "content": r.content,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]

    def get_user_stats(self, user_id: str) -> ConversationStats:
        with Session(self.engine) as session:
            tickets = session.query(Ticket).filter(Ticket.user_id == user_id).all()
            if not tickets:
                return ConversationStats(user_id=user_id, total_tickets=0, total_messages=0, last_interaction_at=None)
            ticket_ids = [t.ticket_id for t in tickets]
            msg_count = session.query(TicketMessage).filter(TicketMessage.ticket_id.in_(ticket_ids)).count()
            last_msg = (
                session.query(TicketMessage)
                .filter(TicketMessage.ticket_id.in_(ticket_ids))
                .order_by(TicketMessage.created_at.desc())
                .first()
            )
            return ConversationStats(
                user_id=user_id,
                total_tickets=len(tickets),
                total_messages=msg_count,
                last_interaction_at=last_msg.created_at if last_msg else None,
            )

    def summarize_history(self, ticket_id: str, max_messages: int = 10) -> str:
        messages = self.get_conversation_messages(ticket_id, limit=max_messages)
        if not messages:
            return ""
        lines = []
        for m in messages[-max_messages:]:
            role = "User" if m["role"] == "user" else "Assistant"
            content = (m["content"] or "").strip().replace("\n", " ")
            if len(content) > 180:
                content = content[:180] + "..."
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    # ---------------------- High-level helpers ------------------- #
    def prepare_context(self, user_id: str, ticket_id: str) -> Dict[str, Any]:
        stats = self.get_user_stats(user_id)
        history_preview = self.summarize_history(ticket_id, max_messages=8)
        return {
            "previous_interactions_count": stats.total_messages,
            "previous_tickets": stats.total_tickets,
            "last_interaction_at": stats.last_interaction_at.isoformat() if stats.last_interaction_at else None,
            "history_preview": history_preview,
        }
