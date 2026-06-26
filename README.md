# Email Agent: LLM-Powered Email Workflow Automation

## Problem Statement

Email overload is a universal productivity killer. Teams spend hours triaging, classifying, and responding to emails that often fall into repetitive categories: status updates, approval requests, technical support tickets, and complaints. The core problem is not just volume—it's the cognitive overhead of context-switching between different types of requests, each requiring different response strategies.

Traditional email filters and rules-based systems fail because they cannot understand intent. A rule like "if subject contains 'urgent' mark as important" misses emails like "production server is down" which carry urgency in semantics, not keywords. Meanwhile, AI chatbots handle individual messages but lack workflow awareness—they don't know that an urgent email should pause for human review while a routine request can be auto-replied.

## Solution

An autonomous email processing agent that reads emails, understands their intent and urgency, routes them through appropriate workflows, and generates context-aware responses—all while maintaining a complete audit trail and supporting human-in-the-loop approval for critical decisions.

**Why Agents?** Email processing is not a single-shot classification task—it's a multi-step workflow requiring different capabilities at each stage:

1. **Classification Agent**: Understands email intent and urgency
2. **Reply Agent**: Generates context-aware professional responses
3. **Audit Agent**: Maintains tamper-proof execution logs
4. **Orchestrator**: Routes emails through the appropriate workflow path

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI / API Layer                          │
│  python cli.py process "email" | batch --file emails.json      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Async Orchestrator                           │
│              (ThreadPoolExecutor + asyncio)                     │
│         Spawns concurrent agents per email                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ Classifier  │ │ Reply Agent │ │ Audit Agent │
    │   Agent     │ │             │ │             │
    │             │ │  Uses RAG   │ │ Hash-chain  │
    │ LLM call:   │ │  context    │ │ integrity   │
    │ "urgent?"   │ │  for reply  │ │ verification│
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
           ▼               ▼               ▼
    ┌─────────────────────────────────────────────────┐
    │              SQLite Persistence                  │
    │  workflow_state │ tasks │ audit_log │ chunks    │
    └─────────────────────────────────────────────────┘
```

### Workflow State Machine

```
PENDING → CLASSIFIED → [urgent?] → AWAITING_HUMAN_RESPONSE
                      [not urgent] → COMPLETED → LOGGED & COMPLETED
```

## Features

- **LLM-Powered Classification**: Automatically classifies emails into `urgent`, `medium`, or `low` priority
- **Context-Aware Reply Generation**: Uses RAG (Retrieval Augmented Generation) to generate professional responses
- **Workflow State Machine**: 5-state workflow engine with persistent state tracking
- **Human Approval Flow**: Urgent emails require human intervention before auto-reply
- **Async Batch Processing**: Process multiple emails concurrently with ThreadPoolExecutor
- **Audit Trail**: Hash-chain integrity verification for compliance
- **SQLite Persistence**: Complete workflow history and state management
- **Ticket System**: Auto-generated tickets for tracking
- **Docker Deployment**: Containerized setup for easy deployment

## Project Structure

```
task_agent/
├── cli.py                    # CLI entry point (9 commands)
├── main.py                   # Programmatic entry point
├── workflows/
│   ├── email_workflow.py     # Sync workflow engine
│   └── async_workflow.py     # Async batch processing
├── my_agents/
│   ├── agent.py              # Tool-using agent
│   ├── classifier_agent.py   # Email classification
│   ├── reply_agent.py        # Reply generation
│   └── audit_agent.py        # Audit trail with integrity
├── tools/
│   ├── rag.py                # RAG context retrieval
│   ├── tools.py              # NLP + vector tools
│   ├── filetools.py          # File system tools
│   ├── ticket_manager.py     # Ticket ID generation
│   ├── logger.py             # Structured JSON logging
│   └── hash.py               # SHA-256 hashing
├── memory/
│   └── sqlite_store.py       # Database operations
├── llm/
│   └── client.py             # LLM API client
├── models/
│   └── schemas.py            # EmailTask data model
├── dataset/
│   ├── emails_structured.py  # 50 sample emails
│   └── dataset.md            # Sample emails for testing
├── hermes/                   # Experimental task agent
├── Dockerfile                # Container deployment
├── docker-compose.yml        # Docker orchestration
├── requirements.txt          # Dependencies
├── workflow.db               # SQLite database (runtime)
└── To-do.md                  # Roadmap with 50+ items
```

## Installation & Setup

### Requirements

- Python 3.10+
- Local LLM endpoint (e.g., llama.cpp, Ollama) running on port 8080

### Local Setup

```bash
# Clone repository
git clone https://github.com/yourusername/task_agent.git
cd task_agent

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Configure LLM endpoint (optional, defaults to http://127.0.0.1:8080/chat/completions)
export LLM_ENDPOINT="http://127.0.0.1:8080/chat/completions"
```

### Docker Setup

```bash
# Build and run
docker-compose build
docker-compose run email-agent process "Our server is down"

# Or use CLI directly
docker-compose run email-agent batch "Email 1" "Email 2" "Email 3"
```

### Configuration

LLM endpoint is configurable via environment variable:

```bash
# Default: http://127.0.0.1:8080/chat/completions
export LLM_ENDPOINT="http://your-llm-server:8080/chat/completions"
export DB_PATH="workflow.db"
export LOG_DIR="logs"
```

## Usage

### CLI Commands

```bash
# Process a single email
python cli.py process "Our production server is down"

# Process multiple emails concurrently
python cli.py batch "Server down" "Approve budget" "Meeting at 3pm"

# Process emails from JSON file
python cli.py batch --file emails.json

# Classify without full workflow
python cli.py classify "Invoice approval needed"

# Generate reply draft only
python cli.py draft "Meeting at 3pm"

# List all tasks
python cli.py list
python cli.py list --status pending

# Show task details
python cli.py status 1

# Resume paused workflow
python cli.py resume 1

# View audit trail
python cli.py audit TICKET-1719412345

# View statistics
python cli.py stats
```

### Programmatic Usage

```python
import asyncio
from memory.sqlite_store import DataBase
from workflows import email_workflow
from workflows.async_workflow import process_batch

db = DataBase("workflow.db")

# Single email
email_workflow.process_email("Server is down", db)

# Batch processing
emails = ["Email 1", "Email 2", "Email 3"]
results = asyncio.run(process_batch(emails))
```

### Workflow States

1. **PENDING**: Email received, awaiting classification
2. **CLASSIFIED**: Email classified as urgent/medium/low
3. **AWAITING_HUMAN_RESPONSE**: Urgent emails pause here for human approval
4. **COMPLETED**: Reply generated and task completed
5. **LOGGED & COMPLETED**: Final logging step

### Resume Paused Workflow

```python
from memory.sqlite_store import DataBase
from workflows import email_workflow

db = DataBase("workflow.db")
task_dict = db.get_workflow_state(ticket_id)
email_workflow.resume_workflow(db, task_dict)
```

## How It Works

### 1. Email Classification

```python
# agents/classifier_agent.py
def classify(email_text):
    prompt = f"Classify the following email into three categories 'low', 'medium', 'urgent'..."
    return chat(prompt)
```

### 2. Context Retrieval (RAG)

```python
# tools/rag.py
def add_context(email_text):
    intent = get_intent(email_text)  # Classify intent
    context = INTENT_CONTENT_MAP[intent]  # Retrieve relevant context
    return {"intent": intent, "context": context, "email": email_text}
```

### 3. Reply Generation

```python
# agents/reply_agent.py
def generate_reply(email_text):
    context = rag.add_context(email_text)
    prompt = f"Generate a concise and professional reply..."
    return chat(prompt)
```

### 4. Workflow Routing

```python
# workflows/email_workflow.py
def route_task(task):
    match task.status:
        case "pending":
            return _start_workflow
        case "classified":
            return _check_urgent
        case "awaiting_human_response":
            return _awaiting_human_response  # PAUSE
        case "completed":
            return _log_task
```

## Sample Dataset

The `dataset/dataset.md` contains 50 diverse sample emails covering:
- Project updates
- Meeting requests
- Technical issues
- Invoice approvals
- Customer complaints
- HR requests
- Budget approvals
- And more...

Use these to test classification accuracy and reply generation.

## Current Limitations

- ⚠️ No input validation on email text
- ⚠️ No unit tests
- 🔲 API layer (FastAPI)
- 🔲 External email integration (IMAP/SMTP)
- 🔲 Approval dashboard (Streamlit/FastAPI)

## Roadmap

See `To-do.md` for 50+ improvement items including:
- ✅ Workflow pause/resume
- ✅ State machine formalization
- ✅ Audit agent with integrity verification
- ✅ Structured JSON logging
- ✅ Async batch processing
- ✅ Docker deployment
- ✅ CLI with 9 commands
- 🔲 Error handling & retry logic
- 🔲 API layer (FastAPI)
- 🔲 External email integration (IMAP/SMTP)
- 🔲 Approval dashboard (Streamlit/FastAPI)

## Development Notes

- Python 3.10+
- SQLite for persistence
- LLM endpoint configurable via `LLM_ENDPOINT` env var (default: `http://127.0.0.1:8080/chat/completions`)
- SentenceTransformer for embeddings (`all-MiniLM-L6-v2`)
- spaCy for NLP (`en_core_web_sm`)
- State machine pattern with `match/case`
- JSON serialization for workflow state
- ThreadPoolExecutor for concurrent email processing
- SHA-256 hash-chain for audit trail integrity

## Evaluation Mapping

| Key Concept | Implementation |
|-------------|----------------|
| Agent / Multi-agent system | classifier_agent, reply_agent, audit_agent, orchestrator |
| MCP Server | Tool registry pattern (tools.py, filetools.py) with structured I/O |
| Security features | Hash-chain audit trail with integrity verification |
| Deployability | Dockerfile + docker-compose.yml with env var configuration |
| Agent skills | CLI with 9 commands: process, batch, classify, draft, list, status, resume, audit, stats |
| Async / Concurrency | asyncio + ThreadPoolExecutor for parallel email processing |

## License

MIT License

---

**Last Updated**: 2026-06-26
