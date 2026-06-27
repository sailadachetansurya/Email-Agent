#!/usr/bin/env python3
import os
import sys
import json
import asyncio
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from memory.sqlite_store import DataBase
from workflows import email_workflow
from workflows.async_workflow import process_batch
from models.schemas import EmailTask

console = Console()

DB_PATH = os.environ.get("DB_PATH", os.path.join("workflows", "workflow.db"))


def get_db():
    return DataBase(DB_PATH)


@click.group(invoke_without_command=True)
@click.version_option(version="1.0.0")
@click.pass_context
def cli(ctx):
    """Email Agent CLI - Automated email processing with LLM-powered classification."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument("email_text")
def process(email_text):
    """Process a single email through the workflow."""
    db = get_db()
    console.print(Panel(f"[bold]Processing email:[/bold]\n{email_text}", title="Email Agent"))
    email_workflow.process_email(email_text, db)
    console.print("[green]✓[/green] Email processed successfully.")


@cli.command()
@click.option("--status", "-s", default=None, help="Filter by status (pending, classified, completed, etc.)")
def list(status):
    """List all tasks in the database."""
    db = get_db()
    query = "SELECT ticket_id, email_text, classification, status FROM tasks"
    if status:
        query += f" WHERE status = '{status}'"
    query += " ORDER BY ticket_id DESC"

    rows = db.conn.execute(query).fetchall()

    table = Table(title="Email Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Email", style="white", max_width=50)
    table.add_column("Classification", style="yellow")
    table.add_column("Status", style="green")

    for row in rows:
        table.add_row(str(row[0]), row[1][:50], row[2] or "-", row[3])

    console.print(table)


@cli.command()
@click.argument("task_id", type=int)
def status(task_id):
    """Show status of a specific task."""
    db = get_db()
    task_dict = db.get_workflow_state(task_id)
    if not task_dict:
        console.print(f"[red]✗[/red] Task {task_id} not found.")
        return

    panel_content = "\n".join(f"[bold]{k}:[/bold] {v}" for k, v in task_dict.items())
    console.print(Panel(panel_content, title=f"Task {task_id}"))


@cli.command()
@click.argument("ticket_id", type=int)
def resume(ticket_id):
    """Resume a paused workflow."""
    db = get_db()
    task_dict = db.get_workflow_state(ticket_id)
    if not task_dict:
        console.print(f"[red]✗[/red] Task {ticket_id} not found.")
        return

    console.print(f"[yellow]Resuming task {ticket_id}...[/yellow]")
    email_workflow.resume_workflow(db, task_dict)
    console.print("[green]✓[/green] Workflow resumed.")


@cli.command()
def stats():
    """Show workflow statistics."""
    db = get_db()
    rows = db.conn.execute(
        "SELECT status, COUNT(*) FROM tasks GROUP BY status"
    ).fetchall()

    table = Table(title="Workflow Statistics")
    table.add_column("Status", style="cyan")
    table.add_column("Count", style="green")

    for row in rows:
        table.add_row(row[0], str(row[1]))

    console.print(table)


@cli.command()
@click.argument("email_text")
def classify(email_text):
    """Classify an email without running the full workflow."""
    from my_agents import classifier_agent
    result = classifier_agent.classify(email_text)
    console.print(f"[bold]Classification:[/bold] {result}")


@cli.command()
@click.argument("email_text")
def draft(email_text):
    """Generate a reply draft for an email."""
    from my_agents import reply_agent
    reply = reply_agent.generate_reply(email_text)
    console.print(Panel(reply, title="Generated Reply"))


@cli.command()
@click.argument("emails", nargs=-1)
@click.option("--file", "-f", "file_path", help="File with emails (JSON or TXT, one per line)")
def batch(emails, file_path):
    """Process multiple emails concurrently.

    Accepts emails as space-separated arguments or a file.
    TXT format: one email per line
    JSON format: ["email1", "email2"] or [{"email_text": "..."}]

    Example: python cli.py batch "Email 1" "Email 2"
    Example: python cli.py batch --file emails.txt
    Example: python cli.py batch --file emails.json
    """
    email_list = list(emails)

    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if file_path.endswith(".json"):
            data = json.loads(content)
            if isinstance(data, list):
                email_list = [item if isinstance(item, str) else item.get("email_text", "") for item in data]
            else:
                console.print("[red]✗[/red] JSON must be a list of strings or objects with email_text field.")
                return
        else:
            email_list = [line.strip() for line in content.splitlines() if line.strip()]

    if not email_list:
        console.print("[red]✗[/red] No emails provided. Pass emails as arguments or use --file.")
        return

    console.print(Panel(f"[bold]Processing {len(email_list)} emails concurrently...[/bold]", title="Batch Processing"))

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Processing...", total=None)
        results = asyncio.run(process_batch(email_list))
        progress.update(task, completed=True)

    table = Table(title="Batch Results")
    table.add_column("#", style="dim")
    table.add_column("Email", max_width=40)
    table.add_column("Ticket", style="cyan")
    table.add_column("Classification", style="yellow")
    table.add_column("Status", style="green")

    for i, result in enumerate(results):
        if "error" in result:
            table.add_row(str(i + 1), result["email"][:40], "-", "-", f"[red]ERROR: {result['error']}[/red]")
        else:
            table.add_row(
                str(i + 1),
                result.get("email_text", "")[:40],
                result.get("Ticket_id", "-"),
                result.get("classification", "-"),
                result.get("status", "-")
            )

    console.print(table)
    console.print(f"[green]✓[/green] Processed {len(results)} emails.")


@cli.command()
@click.argument("ticket_id")
def audit(ticket_id):
    """Show audit trail for a ticket."""
    from my_agents.audit_agent import AuditAgent
    db = get_db()
    agent = AuditAgent(db)
    history = agent.get_history(ticket_id)

    if not history:
        console.print(f"[red]✗[/red] No audit entries for ticket {ticket_id}.")
        return

    table = Table(title=f"Audit Trail: {ticket_id}")
    table.add_column("Action", style="cyan")
    table.add_column("Details", style="white")
    table.add_column("Timestamp", style="yellow")
    table.add_column("Hash", style="dim")

    import time
    for action, details, timestamp, entry_hash in history:
        table.add_row(action, details or "-", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)), entry_hash[:12])

    console.print(table)

    integrity = agent.verify_integrity(ticket_id)
    if integrity:
        console.print("[green]✓[/green] Audit trail integrity verified.")
    else:
        console.print("[red]✗[/red] Audit trail integrity FAILED.")


@cli.command()
@click.option("--set", "provider_name", help="Switch to provider (local, google)")
@click.option("--api-key", help="Set Google AI Studio API key")
@click.option("--model", help="Set model name for current provider")
def models(provider_name, api_key, model):
    """Manage LLM providers and models."""
    from llm.client import list_providers, set_provider, set_google_api_key, set_model, get_provider

    if api_key:
        set_google_api_key(api_key)
        console.print("[green]✓[/green] Google API key saved.")

    if model:
        set_model(model)
        console.print(f"[green]✓[/green] Model set to: {model}")

    if provider_name:
        try:
            settings = set_provider(provider_name)
            console.print(f"[green]✓[/green] Switched to [bold]{provider_name}[/bold] (model: {settings.get('model', 'default')})")
        except ValueError as e:
            console.print(f"[red]✗[/red] {e}")
            return

    providers, current = list_providers()
    table = Table(title="LLM Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Model", style="yellow")
    table.add_column("Status", style="green")

    for p in providers:
        status = "[green]● active[/green]" if p["active"] else "[dim]○[/dim]"
        table.add_row(p["name"], p["model"], status)

    console.print(table)
    console.print(f"[dim]Usage: python cli.py models --set google[/dim]")
    console.print(f"[dim]       python cli.py models --api-key YOUR_KEY[/dim]")
    console.print(f"[dim]       python cli.py models --model gemini-2.0-flash[/dim]")


if __name__ == "__main__":
    cli()
