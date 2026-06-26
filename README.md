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

- **Interactive TUI**: Claude Code-style terminal interface with auto-completion and rich panels
- **Gmail Integration**: OAuth 2.0 login, fetch unread, send emails directly from terminal
- **LLM-Powered Classification**: Automatically classifies emails into `urgent`, `medium`, or `low` priority
- **Context-Aware Reply Generation**: Uses RAG (Retrieval Augmented Generation) to generate professional responses
- **Workflow State Machine**: 5-state workflow engine with persistent state tracking
- **Human Approval Flow**: Urgent emails require human intervention before auto-reply
- **Async Batch Processing**: Process multiple emails concurrently with ThreadPoolExecutor
- **File-Based Input**: Read emails from `.txt` or `.json` files (no typing huge text)
- **Audit Trail**: Hash-chain integrity verification for compliance
- **SQLite Persistence**: Complete workflow history and state management
- **Ticket System**: Auto-generated tickets for tracking
- **Docker Deployment**: Containerized setup for easy deployment

## Project Structure

```
task_agent/
├── tui.py                    # Interactive TUI (main entry point)
├── cli.py                    # CLI entry point (9 commands)
├── main.py                   # Programmatic entry point
├── auth/
│   ├── gmail_oauth.py        # OAuth 2.0 flow with local callback
│   └── gmail_client.py       # Gmail API wrapper (read/send/search)
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
│   └── client.py             # LLM API client (multi-provider)
├── models/
│   └── schemas.py            # EmailTask data model
├── dataset/
│   ├── emails_structured.py  # 50 sample emails
│   └── dataset.md            # Sample emails for testing
├── Dockerfile                # Container deployment
├── docker-compose.yml        # Docker orchestration
├── requirements.txt          # Dependencies
├── gmail_credentials.json    # OAuth credentials (gitignored)
├── gmail_token.json          # OAuth tokens (gitignored)
└── llm_config.json           # LLM provider config (gitignored)
```

## Installation & Setup

> **Requirements:** Python 3.10+ | Local LLM endpoint (port 8080) | Google Cloud project (for Gmail)

### Quick Start

```bash
git clone https://github.com/yourusername/task_agent.git
cd task_agent
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python tui.py
```

### Gmail OAuth Setup (Optional)

> **Each user must do this once** — same as `gh auth login` for GitHub CLI.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Gmail API**
3. Go to **Credentials** → Create **OAuth 2.0 Client ID**
4. Set redirect URI to `http://localhost:8085/callback`
5. Download credentials JSON
6. In TUI, run:

```
inbox-pilot [local] $ /gmail login
```

Browser opens → authorize → done. Tokens stored locally in `gmail_token.json`.

### LLM Provider Setup

```bash
# Use local LLM (default)
python tui.py

# Switch to Google AI Studio
# In TUI:
/models
/provider google --api-key YOUR_GOOGLE_API_KEY
```

### Docker Setup

```bash
docker-compose build
docker-compose run email-agent
```

### Environment Variables

```bash
export LLM_ENDPOINT="http://127.0.0.1:8080/chat/completions"
export DB_PATH="workflow.db"
export LOG_DIR="logs"
```

## Usage

### Interactive TUI (Recommended)

```bash
python tui.py
```

```
  ╔╦╗╔═╗╔╦╗╦═╗╦╔═╗╔═╗╦ ╦  ╦ ╦╔═╗╔═╗╦╔═
   ║ ║╣  ║ ╠╦╝║╠═╣║  ╠═╣  ╠═╣║╣ ╚═╗╠╩╗
   ╩ ╚═╝ ╩ ╩╚═╩╩ ╩╚═╝╩ ╩  ╩ ╩╚═╝╚═╝╩ ╩

inbox-pilot [local] $ /help
```

**TUI Commands:**

| Command | Description |
|---------|-------------|
| `/process <text\|@file>` | Process email from text or file |
| `/batch @emails.json` | Process multiple emails from JSON |
| `/classify <text\|@file>` | Classify email only |
| `/draft <text\|@file>` | Generate reply draft |
| `/gmail login` | Login to Gmail via OAuth |
| `/gmail unread` | Fetch unread emails |
| `/gmail fetch 5` | Fetch last 5 emails |
| `/gmail send to@x.com` | Send email |
| `/list` | List all tasks |
| `/status <id>` | Show task details |
| `/resume <id>` | Resume paused workflow |
| `/audit <ticket>` | View audit trail |
| `/stats` | Workflow statistics |
| `/models` | View/switch LLM providers |
| `/provider google` | Switch to Google AI Studio |
| `/clear` | Clear terminal |
| `/exit` | Exit |

**File Input (no typing huge text):**

```bash
# Read email from file
/inbox-pilot [local] $ /process @email.txt

# Batch from JSON
/inbox-pilot [local] $ /batch @emails.json
```

### CLI Commands

```bash
python cli.py process "Our production server is down"
python cli.py batch --file emails.json
python cli.py classify "Invoice approval needed"
python cli.py draft "Meeting at 3pm"
python cli.py list --status pending
python cli.py status 1
python cli.py audit TICKET-1719412345
python cli.py models
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
- ✅ Interactive TUI with auto-completion
- ✅ Gmail OAuth integration
- ✅ Multi-provider LLM support (local + Google AI Studio)
- ✅ File-based email input
- 🔲 Error handling & retry logic
- 🔲 API layer (FastAPI)
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
| Agent skills | Interactive TUI with 16 commands + file input + Gmail integration |
| Async / Concurrency | asyncio + ThreadPoolExecutor for parallel email processing |

## License

MIT License

---

**Last Updated**: 2026-06-26
