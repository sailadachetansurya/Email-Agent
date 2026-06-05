#!/usr/bin/env python3
"""
Simple Task Agent
- Identifies tasks from user input
- Breaks tasks into subtasks
- Executes tool calls
- Verifies with human
- Updates task status
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Callable, Dict, Any

# Task states
TASK_PENDING = "pending"
TASK_IN_PROGRESS = "in_progress"
TASK_VERIFICATION = "verification"
TASK_COMPLETED = "completed"
TASK_CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a task in the agent workflow."""
    id: str
    name: str
    description: str
    status: str = TASK_PENDING
    subtasks: List['Task'] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    output: Any = None
    tool_calls: List[Dict] = field(default_factory=list)
    verification_notes: str = ""

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'subtasks': [s.to_dict() for s in self.subtasks],
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'output': str(self.output) if self.output else None,
            'tool_calls': self.tool_calls,
            'verification_notes': self.verification_notes
        }


class TaskAgent:
    """Main agent class for task management and execution."""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.tool_registry: Dict[str, Callable] = {}
        self.task_history: List[Dict] = []
        
    # ========== Task Identification ==========
    def identify_task(self, user_input: str) -> Optional[Task]:
        """Identify and create a task from user input."""
        print("\n🔍 [IDENTIFY] Analyzing user input...")
        print(f"   Input: {user_input}")
        
        # Parse task from input
        task_name = user_input[:50]  # Limit name length
        description = user_input
        
        task = Task(id=str(uuid.uuid4()), name=task_name, description=description)
        
        print(f"   ✓ Task identified: {task.name}")
        print(f"   ID: {task.id[:8]}...")
        
        return task

    # ========== Task Breakdown ==========
    def break_down_task(self, task: Task) -> List[Task]:
        """Break a task into smaller subtasks."""
        print("\n📋 [BREAKDOWN] Decomposing task...")
        print(f"   Task: {task.name}")
        
        # Simple breakdown logic - can be enhanced
        breakdown_rules = [
            ("analyze", "Analyze requirements"),
            ("design", "Design solution"),
            ("implement", "Implement features"),
            ("test", "Write tests"),
            ("verify", "Verify output"),
            ("deploy", "Deploy changes"),
        ]
        
        subtasks = []
        keywords = ['analyze', 'design', 'implement', 'test', 'verify', 'deploy']
        
        for keyword in keywords:
            if keyword in task.description.lower() or keyword in task.name.lower():
                subtask = Task(
                    id=str(uuid.uuid4()),
                    name=f"Subtask: {keyword}",
                    description=f"Handle {keyword} phase",
                    status=TASK_PENDING
                )
                subtasks.append(subtask)
        
        # Default breakdown if no keywords found
        if not subtasks:
            subtasks = [
                Task(id=str(uuid.uuid4()), name="Phase 1: Setup", description="Set up environment", status=TASK_PENDING),
                Task(id=str(uuid.uuid4()), name="Phase 2: Execute", description="Execute main logic", status=TASK_PENDING),
                Task(id=str(uuid.uuid4()), name="Phase 3: Verify", description="Verify results", status=TASK_PENDING),
            ]
        
        task.subtasks = subtasks
        task.updated_at = datetime.now().isoformat()
        
        print(f"   ✓ Created {len(subtasks)} subtasks")
        return subtasks

    # ========== Tool Execution ==========
    def register_tool(self, name: str, func: Callable):
        """Register a tool for execution."""
        self.tool_registry[name] = func
        print(f"   🛠️  Tool registered: {name}")

    def execute_tool_call(self, tool_name: str, *args, **kwargs) -> Any:
        """Execute a tool call."""
        if tool_name not in self.tool_registry:
            print(f"   ✗ Tool not found: {tool_name}")
            return None
            
        print(f"\n   📦 [EXECUTE] Calling tool: {tool_name}")
        try:
            result = self.tool_registry[tool_name](*args, **kwargs)
            print(f"   ✓ Tool completed successfully")
            return result
        except Exception as e:
            print(f"   ✗ Tool error: {e}")
            return None

    def execute_subtasks(self, task: Task) -> Any:
        """Execute all subtasks in order."""
        print(f"\n🚀 [EXECUTE] Running subtasks for: {task.name}")
        
        results = []
        for subtask in task.subtasks:
            print(f"\n   └─ Processing: {subtask.name}")
            subtask.status = TASK_IN_PROGRESS
            
            # Simulate tool execution for demonstration
            result = self._execute_subtask_logic(subtask)
            subtask.output = result
            results.append(result)
            
            subtask.status = TASK_COMPLETED
        
        task.output = results
        task.updated_at = datetime.now().isoformat()
        
        return results

    def _execute_subtask_logic(self, subtask: Task) -> Any:
        """Execute logic for a subtask."""
        # This is where actual tool calls would happen
        # For demo, we'll simulate
        print(f"      → Running: {subtask.description}")
        
        # Simulate some tool calls based on task type
        if 'file' in subtask.description.lower():
            result = self.execute_tool_call('file_read', filename='example.txt')
        elif 'network' in subtask.description.lower():
            result = self.execute_tool_call('http_get', url='https://api.example.com/data')
        else:
            result = {"status": "completed", "subtask": subtask.name}
        
        subtask.tool_calls.append({
            "tool": "demo_tool",
            "args": {},
            "result": str(result)
        })
        
        return result

    # ========== Human Verification ==========
    def verify_output(self, task: Task) -> bool:
        """Verify output with human feedback."""
        print(f"\n👁️ [VERIFY] Human verification for: {task.name}")
        
        if not task.output:
            print("   ✗ No output to verify")
            return False
        
        # In a real scenario, this would prompt the user
        # For demo, we'll show the output and ask
        print("\n   --- OUTPUT FOR VERIFICATION ---")
        for subtask in task.subtasks:
            print(f"   [{subtask.status}] {subtask.name}: {subtask.output}")
        print("   --------------------------------")
        
        # Simulate verification (user can customize)
        # return input("Verify output? (y/n): ").lower() == 'y'
        is_verified = True  # Auto-verify for demo
        
        if is_verified:
            task.verification_notes = "Verified ✓"
            task.status = TASK_COMPLETED
            print("   ✓ Verification passed")
        else:
            task.verification_notes = "Rejected ✗"
            task.status = TASK_PENDING
            print("   ✗ Verification failed")
            
        return is_verified

    # ========== Status Update ==========
    def update_task_status(self, task: Task, status: str, notes: str = ""):
        """Update task status with optional notes."""
        task.status = status
        task.updated_at = datetime.now().isoformat()
        
        if notes:
            task.verification_notes = notes
        
        print(f"   ✓ Status updated: {status}")
        return task

    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get current status of a task."""
        task = self.tasks.get(task_id)
        return task.status if task else None

    # ========== Workflow ==========
    def run_workflow(self, user_input: str):
        """Run the complete agent workflow."""
        print("=" * 60)
        print("🤖 SIMPLE TASK AGENT - WORKFLOW STARTED")
        print("=" * 60)
        
        # Step 1: Identify task
        task = self.identify_task(user_input)
        if not task:
            print("✗ Failed to identify task")
            return
        
        self.tasks[task.id] = task
        
        # Step 2: Break down task
        subtasks = self.break_down_task(task)
        
        # Step 3: Execute subtasks
        results = self.execute_subtasks(task)
        
        # Step 4: Verify with human
        is_verified = self.verify_output(task)
        
        # Step 5: Update final status
        if is_verified:
            self.update_task_status(task, TASK_COMPLETED, "Successfully completed")
        else:
            self.update_task_status(task, TASK_PENDING, "Verification failed")
        
        # Display final status
        self._print_task_summary(task)
        
        print("\n" + "=" * 60)
        print("🤖 WORKFLOW COMPLETED")
        print("=" * 60)

    def _print_task_summary(self, task: Task):
        """Print a summary of the task."""
        print(f"\n📊 TASK SUMMARY")
        print(f"   Name: {task.name}")
        print(f"   Status: {task.status}")
        print(f"   Subtasks: {len(task.subtasks)}")
        
        for subtask in task.subtasks:
            print(f"      • [{subtask.status}] {subtask.name}")
        
        if task.output:
            print(f"   Output: {task.output}")

    def get_all_tasks(self) -> List[Dict]:
        """Get all task summaries."""
        return [t.to_dict() for t in self.tasks.values()]


# ========== Demo Tools ==========
def file_read_tool(filename: str) -> str:
    """Simulated file read tool."""
    return f"Content of {filename}"

def http_get_tool(url: str) -> dict:
    """Simulated HTTP GET tool."""
    return {"status": 200, "url": url}

def calculator_tool(operation: str, a: float, b: float) -> float:
    """Simulated calculator tool."""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        return b != 0 and a / b or 0
    return 0


# ========== Main Entry Point ==========
def main():
    """Main entry point for the agent."""
    print("\n" + "=" * 60)
    print("🤖 SIMPLE TASK AGENT")
    print("=" * 60)
    print("\nAvailable tools:")
    print("  • file_read(filename) - Read file content")
    print("  • http_get(url) - Simulated HTTP request")
    print("  • calculator(operation, a, b) - Basic math")
    print("\nUsage: Describe a task, and the agent will:")
    print("  1. Identify the task")
    print("  2. Break it into subtasks")
    print("  3. Execute tool calls")
    print("  4. Verify with you")
    print("  5. Update status")
    print("=" * 60)
    
    agent = TaskAgent()
    
    # Register demo tools
    agent.register_tool('file_read', file_read_tool)
    agent.register_tool('http_get', http_get_tool)
    agent.register_tool('calculator', calculator_tool)
    
    # Interactive mode
    print("\nEnter a task (type 'exit' to quit):")
    
    while True:
        user_input = input("\nYour task: ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Goodbye! 👋")
            break
        
        if not user_input:
            continue
        
        agent.run_workflow(user_input)


if __name__ == "__main__":
    main()
