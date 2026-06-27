#!/usr/bin/env python3
import os
import sys
import json
import asyncio
from datetime import datetime
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from memory.sqlite_store import DataBase
from workflows import email_workflow
from workflows.async_workflow import process_batch
from llm.client import list_providers, set_provider, get_provider, set_google_api_key, set_model

console = Console()
DB_PATH = os.environ.get("DB_PATH", "workflow.db")

COMMANDS = [
    "/help", "/process", "/batch", "/classify", "/draft",
    "/list", "/status", "/resume", "/audit", "/stats",
    "/models", "/provider", "/gmail", "/import", "/outputs",
    "/dashboard", "/metrics", "/clear", "/exit"
]

# BANNER = """
BANNER = r"""
[bold cyan]
    ███████╗███╗   ███╗ █████╗ ██╗██╗
    ██╔════╝████╗ ████║██╔══██╗██║██║
    █████╗  ██╔████╔██║███████║██║██║
    ██╔══╝  ██║╚██╔╝██║██╔══██║██║██║
    ███████╗██║ ╚═╝ ██║██║  ██║██║███████╗
    ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝
[/bold cyan]
[bold white]Email Agent[/bold white]  •  [green]AI-powered Gmail Assistant[/green]
[dim]Type [bold]/help[/bold] to get started[/dim]
"""
# """


class EmailCompleter(Completer):
    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor(WORD=True)
        if word.startswith("/"):
            for cmd in COMMANDS:
                if cmd.startswith(word):
                    yield Completion(cmd, start_position=-len(word))


def get_db():
    return DataBase(DB_PATH)


def print_output(content):
    console.print()
    if isinstance(content, str):
        console.print(content)
    else:
        console.print(content)
    console.print()


def read_input_source(args):
    if not args:
        return None, "No input provided. Usage: /process <text> or /process @file.txt"

    if args[0].startswith("@"):
        filepath = args[0][1:]
        if not os.path.exists(filepath):
            return None, f"File not found: {filepath}"
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
        return content, None

    return " ".join(args), None


def cmd_help():
    table = Table(title="Commands", box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("Command", style="bold")
    table.add_column("Description")
    table.add_column("Example", style="dim")

    commands = [
        ("/help", "Show this help menu", "/help"),
        ("/process <text|@file>", "Process email from text or file", "/process @email.txt"),
        ("/batch @file", "Process multiple emails from file", "/batch @emails.txt"),
        ("/classify <text|@file>", "Classify email only", "/classify @email.txt"),
        ("/draft <text|@file>", "Generate reply draft", "/draft @email.txt"),
        ("/import <file>", "Import emails (one per line)", "/import emails.txt"),
        ("/list [--status S]", "List all tasks", "/list --status pending"),
        ("/status <id>", "Show task details", "/status 1"),
        ("/resume <id>", "Resume paused workflow", "/resume 1"),
        ("/audit <ticket>", "View audit trail", "/audit TICKET-123"),
        ("/stats", "Workflow statistics", "/stats"),
        ("/models", "View/switch LLM providers", "/models"),
        ("/provider <name>", "Switch provider", "/provider google"),
        ("/gmail login", "Login to Gmail via OAuth", "/gmail login"),
        ("/gmail unread", "Fetch unread emails", "/gmail unread"),
        ("/gmail fetch <n>", "Fetch last n emails", "/gmail fetch 5"),
        ("/gmail send <to> <subject>", "Send email", "/gmail send user@test.com"),
        ("/gmail logout", "Logout from Gmail", "/gmail logout"),
        ("/outputs", "List saved results in output/", "/outputs"),
        ("/dashboard", "Open Streamlit dashboard", "/dashboard"),
        ("/metrics", "Show performance metrics", "/metrics"),
        ("/clear", "Clear terminal", "/clear"),
        ("/exit", "Exit application", "/exit"),
    ]

    for cmd, desc, example in commands:
        table.add_row(cmd, desc, example)

    print_output(table)
    console.print("[dim]  File format (.txt): One email per line, each line is a string[/dim]")
    console.print("[dim]  File format (.json): [{\"email_text\": \"...\"}, ...] or [\"email1\", \"email2\"]")
    console.print("[dim]  Example emails.txt:[/dim]")
    console.print("[dim]    Our server is down[/dim]")
    console.print("[dim]    Please approve the budget[/dim]")
    console.print("[dim]    Meeting at 3pm tomorrow[/dim]")


def cmd_process(args):
    content, err = read_input_source(args)
    if err:
        print_output(f"[red]{err}[/red]")
        return
    db = get_db()
    from tools.ticket_manager import create_Ticket
    from tools.output_writer import start_job, end_job
    from models.schemas import EmailTask

    job_file = start_job()
    task = EmailTask(content)
    task.db = db
    create_Ticket(task)

    console.print(f"\n  [cyan]Ticket {task.Ticket_id}[/cyan] — processing...")
    console.print(f"  [dim]Email:[/dim] {content[:70]}")

    email_workflow.process_email(content, db)
    end_job()

    console.print(f"  [green]✓[/green] Completed")
    console.print(f"  [dim]Output: {job_file}[/dim]\n")


def cmd_batch(args):
    if not args:
        print_output("[red]Usage:[/red] /batch @emails.txt or /batch @emails.json")
        return

    if args[0].startswith("@"):
        filepath = args[0][1:]
        if not os.path.exists(filepath):
            print_output(f"[red]File not found: {filepath}[/red]")
            return
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if filepath.endswith(".json"):
            data = json.loads(content)
            if isinstance(data, list):
                emails = [item if isinstance(item, str) else item.get("email_text", "") for item in data]
            else:
                print_output("[red]JSON must be a list of strings or objects with email_text field[/red]")
                return
        else:
            emails = [line.strip() for line in content.splitlines() if line.strip()]
    else:
        emails = args

    total = len(emails)
    console.print(f"\n[bold cyan]Spawning {total} sub-agents...[/bold cyan]\n")

    from tools.output_writer import start_job, end_job
    job_file = start_job()

    results = []
    completed = 0
    import threading

    def process_one(idx, email_text):
        nonlocal completed
        try:
            from memory.sqlite_store import DataBase
            from tools.ticket_manager import create_Ticket
            from models.schemas import EmailTask
            from workflows.async_workflow import _process_sync

            db = DataBase("workflow.db")
            task = EmailTask(email_text)
            task.db = db
            create_Ticket(task)
            console.print(f"  [dim]({idx + 1}/{total})[/dim] [cyan]Ticket {task.Ticket_id}[/cyan] — processing: {email_text[:50]}...")

            result = _process_sync(email_text)
            completed += 1
            console.print(f"  [dim]({completed}/{total})[/dim] [green]✓[/green] {task.Ticket_id} — {result.get('classification', 'done')}")
            return result
        except Exception as e:
            completed += 1
            console.print(f"  [dim]({completed}/{total})[/dim] [red]✗[/red] Error: {str(e)[:40]}")
            return {"email": email_text, "error": str(e)}

    threads = []
    for i, email in enumerate(emails):
        t = threading.Thread(target=lambda idx=i, e=email: results.append(process_one(idx, e)))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    end_job()

    table = Table(title="Batch Results", box=box.ROUNDED)
    table.add_column("#", style="dim")
    table.add_column("Ticket", style="cyan")
    table.add_column("Classification", style="yellow")
    table.add_column("Status", style="green")

    for i, r in enumerate(results):
        if r is None:
            table.add_row(str(i + 1), "-", "-", "[dim]no result[/dim]")
        elif "error" in r:
            table.add_row(str(i + 1), "-", "-", f"[red]ERROR[/red]")
        else:
            table.add_row(str(i + 1), r.get("Ticket_id", "-"), r.get("classification", "-"), r.get("status", "-"))

    print_output(table)
    console.print(f"[green]✓[/green] Processed {completed}/{total} emails.")
    console.print(f"[dim]  Output saved to: {job_file}[/dim]\n")


def cmd_classify(args):
    content, err = read_input_source(args)
    if err:
        print_output(f"[red]{err}[/red]")
        return
    from my_agents import classifier_agent
    with console.status("[bold green]Classifying...[/bold green]"):
        result = classifier_agent.classify(content)
    print_output(Panel(f"[bold yellow]{result}[/bold yellow]", title="Classification"))


def cmd_draft(args):
    content, err = read_input_source(args)
    if err:
        print_output(f"[red]{err}[/red]")
        return
    from my_agents import reply_agent
    with console.status("[bold green]Generating draft...[/bold green]"):
        reply = reply_agent.generate_reply(content)
    print_output(Panel(reply, title="Generated Reply", border_style="green"))


def cmd_import(args):
    if not args:
        print_output("[red]Usage:[/red] /import <file>")
        return
    filepath = args[0]
    if not os.path.exists(filepath):
        print_output(f"[red]File not found: {filepath}[/red]")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    emails = [line.strip() for line in content.splitlines() if line.strip()]
    cmd_batch(["@"] + [filepath])


def cmd_list(args):
    db = get_db()
    query = "SELECT ticket_id, email_text, classification, status FROM tasks"
    if args and args[0] == "--status" and len(args) > 1:
        query += f" WHERE status = '{args[1]}'"
    query += " ORDER BY ticket_id DESC LIMIT 20"

    rows = db.conn.execute(query).fetchall()
    if not rows:
        print_output("[dim]No tasks found.[/dim]")
        return

    table = Table(title="Recent Tasks", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Email", max_width=40)
    table.add_column("Class", style="yellow")
    table.add_column("Status", style="green")

    for row in rows:
        table.add_row(str(row[0]), (row[1] or "")[:40], row[2] or "-", row[3])

    print_output(table)


def cmd_status(args):
    if not args:
        print_output("[red]Usage:[/red] /status <task_id>")
        return
    db = get_db()
    task_dict = db.get_workflow_state(args[0])
    if not task_dict:
        print_output(f"[red]Task {args[0]} not found.[/red]")
        return
    lines = "\n".join(f"[bold]{k}:[/bold] {v}" for k, v in task_dict.items())
    print_output(Panel(lines, title=f"Task {args[0]}"))


def cmd_resume(args):
    if not args:
        print_output("[red]Usage:[/red] /resume <ticket_id>")
        return
    db = get_db()
    task_dict = db.get_workflow_state(args[0])
    if not task_dict:
        print_output(f"[red]Task {args[0]} not found.[/red]")
        return
    with console.status("[bold green]Resuming...[/bold green]"):
        email_workflow.resume_workflow(db, task_dict)
    print_output("[green]✓[/green] Workflow resumed.")


def cmd_audit(args):
    if not args:
        print_output("[red]Usage:[/red] /audit <ticket_id>")
        return
    from my_agents.audit_agent import AuditAgent
    db = get_db()
    agent = AuditAgent(db)
    history = agent.get_history(args[0])

    if not history:
        print_output(f"[red]No audit entries for {args[0]}.[/red]")
        return

    import time
    table = Table(title=f"Audit Trail: {args[0]}", box=box.ROUNDED)
    table.add_column("Action", style="cyan")
    table.add_column("Details", max_width=30)
    table.add_column("Time", style="yellow")
    table.add_column("Hash", style="dim")

    for action, details, ts, h in history:
        table.add_row(action, details or "-", time.strftime("%H:%M:%S", time.localtime(ts)), h[:10])

    print_output(table)


def cmd_stats():
    db = get_db()
    rows = db.conn.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status").fetchall()
    if not rows:
        print_output("[dim]No tasks in database.[/dim]")
        return
    table = Table(title="Statistics", box=box.ROUNDED)
    table.add_column("Status", style="cyan")
    table.add_column("Count", style="green")
    for row in rows:
        table.add_row(row[0], str(row[1]))
    print_output(table)


def cmd_models():
    providers, current = list_providers()
    table = Table(title="LLM Providers", box=box.ROUNDED)
    table.add_column("Provider", style="cyan")
    table.add_column("Model", style="yellow")
    table.add_column("Status")

    for p in providers:
        status = "[green]● active[/green]" if p["active"] else "[dim]○[/dim]"
        table.add_row(p["name"], p["model"], status)

    print_output(table)
    console.print("[dim]  /provider <name>  — switch provider[/dim]")


def cmd_provider(args):
    if not args:
        cmd_models()
        return
    provider_name = args[0]
    api_key = None
    if "--api-key" in args:
        idx = args.index("--api-key")
        if idx + 1 < len(args):
            api_key = args[idx + 1]
    if api_key and provider_name == "google":
        set_google_api_key(api_key)
        print_output(f"[green]✓[/green] Google API key saved.")
    try:
        settings = set_provider(provider_name)
        print_output(f"[green]✓[/green] Switched to [bold]{provider_name}[/bold] (model: {settings.get('model', 'default')})")
    except ValueError as e:
        print_output(f"[red]✗[/red] {e}")


def cmd_outputs(args):
    from tools.output_writer import list_results
    files = list_results()
    if not files:
        print_output("[dim]No output files yet. Process some emails first.[/dim]")
        return
    table = Table(title=f"Output Files ({len(files)})", box=box.ROUNDED)
    table.add_column("#", style="dim")
    table.add_column("Filename", style="cyan")
    table.add_column("Modified", style="yellow")
    import time
    for i, f in enumerate(files[:20]):
        mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(f.stat().st_mtime))
        table.add_row(str(i + 1), f.name, mtime)
    print_output(table)
    console.print(f"[dim]  Output directory: {os.path.abspath('output')}[/dim]")


def cmd_gmail(args):
    from auth.gmail_oauth import login, logout, is_logged_in
    from auth.gmail_client import get_profile, get_unread, list_messages, get_message, send_message

    if not args:
        print_output("[dim]Usage: /gmail <login|logout|unread|fetch|send|profile>[/dim]")
        return

    subcmd = args[0].lower()

    if subcmd == "login":
        if is_logged_in():
            profile, err = get_profile()
            if not err:
                print_output(f"[green]✓[/green] Already logged in as [bold]{profile['email']}[/bold]")
                return
        console.print("[dim]Opening browser for Gmail login...[/dim]")
        token, err = login()
        if err:
            print_output(f"[red]✗[/red] {err}")
            return
        profile, err = get_profile()
        if err:
            print_output(f"[green]✓[/green] Logged in, but couldn't fetch profile.")
        else:
            print_output(f"[green]✓[/green] Logged in as [bold]{profile['email']}[/bold] ({profile['messages_total']} messages)")

    elif subcmd == "logout":
        logout()
        print_output("[green]✓[/green] Logged out from Gmail.")

    elif subcmd == "profile":
        profile, err = get_profile()
        if err:
            print_output(f"[red]✗[/red] {err}")
            return
        print_output(Panel(f"Email: {profile['email']}\nTotal Messages: {profile['messages_total']}", title="Gmail Profile"))

    elif subcmd == "unread":
        emails, err = get_unread(10)
        if err:
            print_output(f"[red]✗[/red] {err}")
            return
        if not emails:
            print_output("[dim]No unread emails.[/dim]")
            return
        table = Table(title=f"Unread Emails ({len(emails)})", box=box.ROUNDED)
        table.add_column("From", style="cyan", max_width=30)
        table.add_column("Subject", style="yellow", max_width=40)
        table.add_column("Snippet", max_width=50)
        for e in emails:
            table.add_row(e["from"][:30], e["subject"][:40], e["snippet"][:50])
        print_output(table)

    elif subcmd == "fetch":
        count = int(args[1]) if len(args) > 1 else 5
        emails, err = list_messages("", count)
        if err:
            print_output(f"[red]✗[/red] {err}")
            return
        results = []
        for msg in emails[:count]:
            email, err = get_message(msg["id"])
            if not err:
                results.append(email)
        table = Table(title=f"Last {len(results)} Emails", box=box.ROUNDED)
        table.add_column("From", style="cyan", max_width=30)
        table.add_column("Subject", style="yellow", max_width=40)
        table.add_column("Date", style="dim")
        for e in results:
            table.add_row(e["from"][:30], e["subject"][:40], e["date"][:20])
        print_output(table)

    elif subcmd == "send":
        if len(args) < 3:
            print_output("[red]Usage:[/red] /gmail send <to> <subject>")
            return
        to = args[1]
        subject = args[2]
        console.print("[dim]Enter email body (Ctrl+D to send):[/dim]")
        body_lines = []
        try:
            while True:
                line = input()
                body_lines.append(line)
        except EOFError:
            pass
        body = "\n".join(body_lines)
        result, err = send_message(to, subject, body)
        if err:
            print_output(f"[red]✗[/red] {err}")
        else:
            print_output(f"[green]✓[/green] Email sent to {to}")

    else:
        print_output(f"[red]Unknown gmail subcommand: {subcmd}[/dim]")


def cmd_dashboard():
    import subprocess
    import sys
    console.print("[bold cyan]Starting Streamlit dashboard...[/bold cyan]")
    console.print("[dim]Opening in browser at http://localhost:8501[/dim]")
    subprocess.Popen([sys.executable, "-m", "streamlit", "run", "dashboard.py", "--server.headless", "true"])


def cmd_metrics():
    from tools.metrics import get_stats
    stats = get_stats()
    if not stats:
        print_output("[dim]No metrics recorded yet. Process some emails first.[/dim]")
        return
    table = Table(title="Performance Metrics", box=box.ROUNDED)
    table.add_column("Operation", style="cyan")
    table.add_column("Count", style="green")
    table.add_column("Avg (ms)", style="yellow")
    table.add_column("P95 (ms)", style="yellow")
    table.add_column("Errors", style="red")
    table.add_column("Error %", style="red")
    for name, data in stats.items():
        table.add_row(
            name,
            str(data["count"]),
            str(data["avg_ms"]),
            str(data["p95_ms"]),
            str(data["errors"]),
            f"{data['error_rate']}%"
        )
    print_output(table)


def process_command(user_input):
    parts = user_input.strip().split()
    if not parts:
        return

    cmd = parts[0].lower()
    args = parts[1:]

    handlers = {
        "/help": lambda: cmd_help(),
        "/process": lambda: cmd_process(args),
        "/batch": lambda: cmd_batch(args),
        "/outputs": lambda: cmd_outputs(args),
        "/classify": lambda: cmd_classify(args),
        "/draft": lambda: cmd_draft(args),
        "/import": lambda: cmd_import(args),
        "/list": lambda: cmd_list(args),
        "/status": lambda: cmd_status(args),
        "/resume": lambda: cmd_resume(args),
        "/audit": lambda: cmd_audit(args),
        "/stats": lambda: cmd_stats(),
        "/models": lambda: cmd_models(),
        "/provider": lambda: cmd_provider(args),
        "/gmail": lambda: cmd_gmail(args),
        "/dashboard": lambda: cmd_dashboard(),
        "/metrics": lambda: cmd_metrics(),
        "/clear": lambda: os.system("cls" if os.name == "nt" else "clear"),
    }

    if cmd in ("/exit", "/quit", "/q"):
        return False

    if cmd in handlers:
        try:
            handlers[cmd]()
        except Exception as e:
            print_output(f"[red]Error:[/red] {str(e)}")
    else:
        print_output(f"[dim]Unknown command: {cmd}. Type /help for available commands.[/dim]")

    return True


def main():
    os.system("cls" if os.name == "nt" else "clear")
    console.print(BANNER)

    session = PromptSession(
        completer=EmailCompleter(),
        history=InMemoryHistory(),
        complete_while_typing=True,
    )

    provider = get_provider()
    prompt_text = HTML(f'<ansimagenta>inbox-pilot</ansimagenta> <ansigreen>[{provider}]</ansigreen> <ansiwhite>$</ansiwhite> ')

    while True:
        try:
            user_input = session.prompt(prompt_text)
            if not user_input.strip():
                continue

            result = process_command(user_input)
            if result is False:
                print_output("[dim]Goodbye![/dim]")
                break

            provider = get_provider()
            prompt_text = HTML(f'<ansimagenta>inbox-pilot</ansimagenta> <ansigreen>[{provider}]</ansigreen> <ansiwhite>$</ansiwhite> ')

        except KeyboardInterrupt:
            continue
        except EOFError:
            break


if __name__ == "__main__":
    main()
