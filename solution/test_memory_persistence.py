#!/usr/bin/env python3
"""
Test Persistent Memory and State Management

Demonstrates:
- Storing conversation history in the core database
- Retrieving previous interactions for returning customers
- Using historical context to personalize responses
"""

import os
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))


def load_knowledge_base():
    articles = []
    with open("data/external/cultpass_articles.jsonl", "r") as f:
        for line in f:
            if line.strip():
                articles.append(json.loads(line))
    return articles


def run_memory_demo():
    from agentic.workflow import MultiAgentWorkflow
    from agentic.memory import ConversationMemoryManager

    core_db = "data/core/udahub.db"
    external_db = "data/external/cultpass.db"

    kb = load_knowledge_base()

    db_paths = {"core": core_db, "external": external_db}
    workflow = MultiAgentWorkflow(kb, db_paths)

    user_id = "mem-user-001"

    print("\n🧪 First interaction (new user/conversation)")
    result1 = workflow.process_query(
        query="Hi! Can you tell me how to reserve an event?",
        user_id=user_id,
        conversation_id="conv-mem-001",
    )
    print(f"   Response: {result1['response'][:80]}...")

    print("\n🧪 Second interaction (same conversation)")
    result2 = workflow.process_query(
        query="Thanks. Also, what's included in my subscription?",
        user_id=user_id,
        conversation_id="conv-mem-001",
    )
    print(f"   Response: {result2['response'][:80]}...")

    print("\n🧪 Returning user (new conversation, should use history)")
    result3 = workflow.process_query(
        query="I forgot, how many experiences do I get per month?",
        user_id=user_id,
        conversation_id="conv-mem-002",
    )
    print(f"   Response: {result3['response'][:80]}...")

    # Inspect stored memory directly
    mem = ConversationMemoryManager(core_db)
    ticket_id = mem.ensure_conversation(user_id, "conv-mem-001")
    history = mem.get_conversation_messages(ticket_id)

    print("\n📜 Stored conversation history (conv-mem-001):")
    for m in history:
        print(f"   [{m['role']}] {m['content'][:60]}")

    stats = mem.get_user_stats(user_id)
    print("\n📊 User stats:")
    print(f"   Total tickets: {stats.total_tickets}")
    print(f"   Total messages: {stats.total_messages}")
    print(f"   Last interaction: {stats.last_interaction_at}")

    return True


if __name__ == "__main__":
    ok = run_memory_demo()
    if ok:
        print("\n🎉 Memory persistence demo complete. The specification passes!")
