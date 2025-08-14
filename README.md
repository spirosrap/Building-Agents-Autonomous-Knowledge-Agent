# Advanced Agentic Techniques - Multi-Agent Support System

A comprehensive multi-agent customer support system demonstrating advanced agentic AI techniques including task routing, knowledge retrieval, support operations, and enhanced memory systems.

## 🎯 Project Overview

This project implements a sophisticated multi-agent customer support system for CultPass, a cultural experiences platform. The system demonstrates advanced agentic AI techniques including:

- **Multi-Agent Architecture**: Supervisor, Knowledge Base, Technical Support, Billing, Account Management, and RAG agents
- **Intelligent Task Routing**: Content-based classification and metadata-driven routing
- **Knowledge Retrieval**: Semantic search with confidence scoring and escalation logic
- **Support Operations**: Database abstraction for account lookup, subscription management, and refund processing
- **Enhanced Memory Systems**: State, session, and long-term memory for personalized interactions
- **End-to-End Workflow**: Complete ticket processing with structured logging and error handling

## 🏗️ System Architecture

### Multi-Agent Design
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Supervisor    │───▶│  Knowledge Base │    │   Technical     │
│   (Coordinator) │    │     Agent       │    │   Support       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Billing     │    │     Account     │    │      RAG        │
│     Agent       │    │   Management    │    │     Agent       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components
- **LangGraph Workflow**: Orchestrates agent coordination and state management
- **Ticket Router**: Intelligent classification and routing based on content and metadata
- **Knowledge Retrieval**: Semantic search with confidence-based escalation
- **Support Tools**: Database abstraction for customer operations
- **Memory Systems**: Multi-layered memory for context and personalization
- **Structured Logging**: Comprehensive audit trail and monitoring

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- OpenAI API key (for Vocareum environment)
- SQLite (included with Python)

### Dependencies
```
langchain>=0.1.0
langgraph>=0.0.20
langchain-openai>=0.0.5
sqlalchemy>=2.0.0
pydantic>=2.0.0
```

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "advanced agentic techniques"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # For Vocareum environment
   export OPENAI_API_KEY="voc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxabcd.xxxxxxxx"
   ```

4. **Initialize databases**
   ```bash
   cd solution
   python setup_databases.py
   ```

## 🧪 Testing

The project includes comprehensive test suites for each component:

### Database Setup Tests
```bash
# Test database initialization and knowledge base population
python test_database_setup.py
```

### Multi-Agent System Tests
```bash
# Test complete multi-agent system (requires API key)
python test_multi_agent_system.py

# Test system architecture (no API key required)
python test_multi_agent_system_mock.py
```

### Task Routing Tests
```bash
# Test intelligent ticket routing and role assignment
python test_ticket_routing.py
```

### Knowledge Retrieval Tests
```bash
# Test knowledge retrieval and tool usage
python test_knowledge_retrieval.py
```

### Support Operations Tests
```bash
# Test support operation tools with database abstraction
python test_support_operations.py
```

### Enhanced Memory Tests
```bash
# Test enhanced memory system (state, session, long-term)
python test_enhanced_memory.py
```

### End-to-End Workflow Tests
```bash
# Test complete end-to-end ticket processing workflow
python test_end_to_end_workflow.py
```

## 📋 Project Specifications

### 1. Knowledge Base Population
- ✅ Populate knowledge base with at least 14 articles
- ✅ Articles cover various topics (technical, billing, account, events)
- ✅ Database initialization and verification

### 2. Multi-Agent Architecture Design
- ✅ Comprehensive architecture documentation
- ✅ Workflow diagrams and state management
- ✅ Agent interaction patterns and communication protocols

### 3. Multi-Agent Implementation
- ✅ LangGraph-based workflow orchestration
- ✅ Agent state management and message passing
- ✅ Vocareum configuration for OpenAI API

### 4. Task Routing and Role Assignment
- ✅ Intelligent ticket classification and routing
- ✅ Content-based and metadata-driven decisions
- ✅ Routing statistics and analysis

### 5. Knowledge Retrieval and Tool Usage
- ✅ Semantic search with confidence scoring
- ✅ Escalation logic based on confidence thresholds
- ✅ Response generation based on knowledge base content

### 6. Support Operation Tools
- ✅ Database abstraction for CultPass operations
- ✅ Account lookup, subscription management, refund processing
- ✅ Structured responses with error handling

### 7. Enhanced Memory System
- ✅ State memory for multi-step interactions
- ✅ Session memory for conversation continuity
- ✅ Long-term memory for resolved issues and preferences

### 8. End-to-End Workflow
- ✅ Complete ticket processing pipeline
- ✅ Structured logging and error handling
- ✅ Tool integration and monitoring

## 🗂️ Project Structure

```
advanced agentic techniques/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── starter/                     # Initial project files
│   ├── 01_external_db_setup.ipynb
│   ├── 02_core_db_setup.ipynb
│   ├── 03_agentic_app.ipynb
│   ├── agentic/
│   ├── data/
│   └── utils.py
└── solution/                    # Complete implementation
    ├── README.md               # Detailed solution documentation
    ├── requirements.txt        # Updated dependencies
    ├── setup_databases.py      # Database initialization
    ├── agentic/               # Multi-agent system
    │   ├── agents/            # Individual agent implementations
    │   ├── tools/             # Support operation tools
    │   ├── workflow.py        # LangGraph workflow
    │   ├── ticket_router.py   # Intelligent routing
    │   ├── knowledge_retrieval.py
    │   ├── memory_enhanced.py # Enhanced memory system
    │   └── workflow_logger.py # Structured logging
    ├── data/                  # Database models and data
    │   ├── core/             # Uda-hub database
    │   ├── external/         # CultPass database
    │   └── models/           # SQLAlchemy models
    ├── logs/                 # Workflow logs
    └── test_*.py             # Comprehensive test suites
```

## 🔧 Key Features

### Multi-Agent Coordination
- **Supervisor Agent**: Central coordinator for intent analysis and routing
- **Specialist Agents**: Domain-specific agents for different support areas
- **LangGraph Workflow**: State management and agent orchestration

### Intelligent Routing
- **Content Classification**: Analyze ticket content for categorization
- **Metadata Routing**: Consider user type, account status, ticket history
- **Priority Assessment**: Determine urgency and complexity
- **Agent Selection**: Route to appropriate specialist agents

### Knowledge Management
- **Semantic Search**: Find relevant knowledge base articles
- **Confidence Scoring**: Assess response quality and relevance
- **Escalation Logic**: Automatic escalation for complex issues
- **Response Generation**: Context-aware responses based on knowledge

### Support Operations
- **Account Lookup**: Retrieve user account information
- **Subscription Management**: Handle billing and subscription operations
- **Refund Processing**: Process refunds with proper validation
- **Database Abstraction**: Secure database operations with error handling

### Memory Systems
- **State Memory**: Maintain context during multi-step interactions
- **Session Memory**: Track conversation continuity within sessions
- **Long-term Memory**: Store resolved issues and user preferences
- **Agent Integration**: Memory-aware decision making

### Monitoring and Logging
- **Structured Logging**: JSON-formatted logs with metadata
- **Search Capabilities**: Query logs by various criteria
- **Error Tracking**: Comprehensive error handling and logging
- **Performance Monitoring**: Processing time and success rate tracking

## 📊 Performance and Results

### Test Results Summary
- ✅ **Database Setup**: All tests passed
- ✅ **Multi-Agent System**: All tests passed
- ✅ **Task Routing**: All tests passed
- ✅ **Knowledge Retrieval**: All tests passed
- ✅ **Support Operations**: All tests passed
- ✅ **Enhanced Memory**: All tests passed
- ✅ **End-to-End Workflow**: All tests passed

### Specification Compliance
All 8 project specifications successfully implemented and tested:
1. Knowledge Base Population ✅
2. Multi-Agent Architecture Design ✅
3. Multi-Agent Implementation ✅
4. Task Routing and Role Assignment ✅
5. Knowledge Retrieval and Tool Usage ✅
6. Support Operation Tools ✅
7. Enhanced Memory System ✅
8. End-to-End Workflow ✅

## 🛠️ Built With

* [LangChain](https://www.langchain.com/) - Agent framework and tool integration
* [LangGraph](https://github.com/langchain-ai/langgraph) - Workflow orchestration and state management
* [OpenAI GPT](https://openai.com/) - Large language models for agent reasoning
* [SQLAlchemy](https://www.sqlalchemy.org/) - Database abstraction and ORM
* [Pydantic](https://pydantic.dev/) - Data validation and settings management
* [Python](https://www.python.org/) - Core programming language

## 📚 Documentation

### Solution Documentation
- **`solution/README.md`** - Comprehensive solution overview and usage instructions
- **`solution/*_SUMMARY.md`** - Detailed implementation summaries for each specification

### Architecture Documentation
- **`solution/agentic/design/`** - Multi-agent architecture design documents
- **`solution/agentic/design/architecture.md`** - System architecture overview
- **`solution/agentic/design/workflow_diagram.md`** - Workflow and interaction diagrams

### Test Documentation
- **`test_*.py`** - Comprehensive test suites with detailed comments
- **Test results** - Automated validation of all specification requirements

## 🎓 Learning Objectives

This project demonstrates advanced agentic AI techniques:

1. **Multi-Agent Systems**: Design and implement coordinated agent architectures
2. **Task Routing**: Intelligent classification and routing based on content and context
3. **Knowledge Management**: Semantic search and retrieval with confidence assessment
4. **Tool Integration**: Database abstraction and support operation tools
5. **Memory Systems**: Multi-layered memory for context and personalization
6. **Workflow Orchestration**: State management and agent coordination
7. **Error Handling**: Robust error handling and graceful degradation
8. **Monitoring**: Structured logging and performance tracking

## 🤝 Contributing

This project is designed for educational purposes to demonstrate advanced agentic AI techniques. The implementation provides a production-ready foundation for multi-agent customer support systems.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE.md) file for details.

---

**Note**: This project is configured for the Vocareum learning environment. Ensure your `OPENAI_API_KEY` is set with the Vocareum format (`voc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxabcd.xxxxxxxx`) for full functionality.
