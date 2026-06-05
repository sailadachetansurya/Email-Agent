#!/usr/bin/env python3
"""
Simple Task Agent with LLM Integration
Uses delegate_task subagent for intelligent task analysis
"""

import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable

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
    llm_analysis: str = ""

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
            'verification_notes': self.verification_notes,
            'llm_analysis': self.llm_analysis
        }


class TaskAgent:
    """Main agent class with LLM integration."""

    def __init__(self, llm_subagent_skill_path: str = None):
        self.tasks: Dict[str, Task] = {}
        self.tool_registry: Dict[str, Callable] = {}
        self.task_history: List[Dict] = []
        self.llm_subagent_skill_path = llm_subagent_skill_path
        
        # LLM prompt template for task analysis
        self.analysis_prompt = """
You are an intelligent task analyzer. Analyze the following task input and provide:

1. A clear breakdown into 2-5 logical subtasks
2. Which tools would be needed for each subtask
3. The expected output format

Task: {task_input}

Response format (JSON):
{{
    "subtasks": [
        {{
            "name": "Subtask name",
            "description": "What this does",
            "tools": ["tool1", "tool2"],
            "priority": "high/medium/low"
        }},
        ...
    ],
    "expected_output": "Description of what should be produced"
}}
"""

    # ========== LLM Integration ==========
    def analyze_task_with_llm(self, task: Task) -> Optional[Dict]:
        """Use LLM subagent to analyze and break down task."""
        print("\n🧠 [LLM ANALYSIS] Analyzing task with LLM...")
        print(f"   Task: {task.name}")
        
        # Prepare the analysis prompt
        prompt = self.analysis_prompt.format(task_input=task.description)
        
        print(f"   Prompt: {prompt[:100]}...")
        
        # In Hermes, we'd use delegate_task to spawn a subagent
        # For now, we'll simulate the LLM response structure
        # You can replace this with actual delegate_task call
        
        # Simulated LLM response (replace with actual delegate_task usage)
        llm_response = self._simulate_llm_analysis(task.description)
        
        task.llm_analysis = json.dumps(llm_response, indent=2)
        
        print(f"   ✓ LLM analysis complete")
        return llm_response

    def _simulate_llm_analysis(self, task_input: str) -> Dict:
        """
        Simulate LLM analysis response.
        
        TODO: Integrate with Hermes delegate_task here.
        
        keywords = ['analyze', 'design', 'implement', 'test', 'verify', 'deploy', 'create', 'build']
        task_lower = task_input.lower()
        
        # Determine task type
        task_types = []
        for keyword in keywords:
            if keyword in task_lower:
                task_types.append(keyword)
        
        # Generate subtasks based on task type
        if not task_types:
            task_types = ['execute', 'verify']
        
        subtasks = [
            {
                "name": "Phase 1: Setup",
                "description": "Prepare environment and resources",
                "tools": ["file_read", "http_get"],
                "priority": "high"
            },
            {
                "name": "Phase 2: " + (task_types[0].capitalize() if task_types else "Execute"),
                "description": "Handle the main " + task_types[0] + " phase",
                "tools": ["calculator", "file_read"],
                "priority": "high"
            },
            {
                "name": "Phase 3: Verify",
                "description": "Verify results and quality",
                "tools": ["file_read"],
                "priority": "medium"
            }
        ]
        
        return {
            "subtasks": subtasks,
            "expected_output": "Completed task results with verification"
        }
        """
        
        keywords = ['analyze', 'design', 'implement', 'test', 'verify', 'deploy', 'create', 'build']
        task_lower = task_input.lower()
        
        # Determine task type
        task_types = []
        for keyword in keywords:
            if keyword in task_lower:
                task_types.append(keyword)
        
        # Generate subtasks based on task type
        if not task_types:
            task_types = ['execute', 'verify']
        
        subtasks = [
            {
                "name": "Phase 1: Setup",
                "description": "Prepare environment and resources",
                "tools": ["file_read", "http_get"],
                "priority": "high"
            },
            {
                "name": "Phase 2: " + (task_types[0].capitalize() if task_types else "Execute"),
                "description": "Handle the main " + task_types[0] + " phase",
                "tools": ["calculator", "file_read"],
                "priority": "high"
            },
            {
                "name": "Phase 3: Verify",
                "description": "Verify results and quality",
                "tools": ["file_read"],
                "priority": "medium"
            }
        ]
        
        return {
            "subtasks": subtasks,
            "expected_output": "Completed task results with verification"
        }

    def create_subtasks_from_llm(self, llm_response: Dict, task: Task) -> List[Task]:
        """Create actual subtasks from LLM analysis."""
        print("\n📋 [CREATE SUBTASKS] Creating subtasks from LLM analysis...")
        
        subtasks = []
        for subtask_data in llm_response.get('subtasks', []):
            subtask = Task(
                id=str(datetime.now().timestamp()) + "-" + str(hash(subtask_data['name'])),
                name=subtask_data['name'],
                description=subtask_data['description'],
                status=TASK_PENDING
            )
            subtasks.append(subtask)
        
        task.subtasks = subtasks
        task.updated_at = datetime.now().isoformat()
        
        print(f"   ✓ Created {len(subtasks)} subtasks")
        return subtasks

    # ========== Task Identification ==========
    def identify_task(self, user_input: str) -> Task:
        """Identify and create a task from user input."""
        print("\n🔍 [IDENTIFY] Analyzing user input...")
        print(f"   Input: {user_input}")
        
        task = Task(id=str(datetime.now().timestamp()), name=user_input[:50], description=user_input)
        
        print(f"   ✓ Task identified: {task.name}")
        return task

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

    def execute_subtasks_with_tools(self, task: Task) -> Any:
        """Execute subtasks, using appropriate tools."""
        print(f"\n🚀 [EXECUTE] Running subtasks for: {task.name}")
        
        results = []
        for subtask in task.subtasks:
            print(f"\n   └─ Processing: {subtask.name}")
            subtask.status = TASK_IN_PROGRESS
            
            result = self._execute_with_tools(subtask)
            subtask.output = result
            results.append(result)
            
            subtask.status = TASK_COMPLETED
        
        task.output = results
        task.updated_at = datetime.now().isoformat()
        
        return results

    def _execute_with_tools(self, subtask: Task) -> Any:
        """Execute subtask using appropriate tools."""
        print(f"      → Running: {subtask.description}")
        
        # Get suggested tools from subtask data
        # In a real scenario, this would be parsed from the LLM response
        tools_needed = ['calculator', 'file_read']
        
        # Execute relevant tools
        if 'calculator' in tools_needed:
            result = self.execute_tool_call('calculator', 'add', 5, 3)
            if result:
                print(f"      ✓ Calculator result: {result}")
        
        if 'file_read' in tools_needed:
            result = self.execute_tool_call('file_read', 'example.txt')
            if result:
                print(f"      ✓ File read result: {result}")
        
        # Default completion result
        return {
            "subtask": subtask.name,
            "status": "completed",
            "description": subtask.description
        }

    # ========== Human Verification ==========
    def verify_output(self, task: Task) -> bool:
        """Verify output with human feedback."""
        print(f"\n👁️ [VERIFY] Human verification for: {task.name}")
        
        if not task.output:
            print("   ✗ No output to verify")
            return False
        
        print("\n   --- OUTPUT FOR VERIFICATION ---")
        for subtask in task.subtasks:
            print(f"   [{subtask.status}] {subtask.name}: {subtask.output}")
        print("   --------------------------------")
        
        # Human verification - in real use, prompt the user
        # For demo, auto-verify
        is_verified = True
        
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

    # ========== Complete Workflow with LLM ==========
    def run_workflow_with_llm(self, user_input: str):
        """Run complete workflow using LLM for task analysis."""
        print("=" * 60)
        print("🤖 LLM-POWERED TASK AGENT - WORKFLOW STARTED")
        print("=" * 60)
        
        # Step 1: Identify task
        task = self.identify_task(user_input)
        self.tasks[task.id] = task
        
        # Step 2: LLM analyzes and breaks down task
        llm_response = self.analyze_task_with_llm(task)
        subtasks = self.create_subtasks_from_llm(llm_response, task)
        
        # Step 3: Execute with tools
        results = self.execute_subtasks_with_tools(task)
        
        # Step 4: Human verification
        is_verified = self.verify_output(task)
        
        # Step 5: Update final status
        if is_verified:
            self.update_task_status(task, TASK_COMPLETED, "Successfully completed with LLM analysis")
        else:
            self.update_task_status(task, TASK_PENDING, "Verification failed")
        
        # Display final status
        self._print_task_summary_with_llm(task)
        
        print("\n" + "=" * 60)
        print("🤖 WORKFLOW COMPLETED")
        print("=" * 60)

    def _print_task_summary_with_llm(self, task: Task):
        """Print summary including LLM analysis."""
        print(f"\n📊 TASK SUMMARY")
        print(f"   Name: {task.name}")
        print(f"   Status: {task.status}")
        print(f"   Subtasks: {len(task.subtasks)}")
        
        for subtask in task.subtasks:
            print(f"      • [{subtask.status}] {subtask.name}")
        
        if task.output:
            print(f"   Output: {task.output}")
        
        if task.llm_analysis:
            print(f"\n🧠 LLM ANALYSIS (first 200 chars):")
            llm_json = task.llm_analysis[:200] + "..."
            print(f"   {llm_json}")


# ========== Demo Tools ==========
def calculator_tool(operation: str, a: float, b: float) -> dict:
    """Simulated calculator tool."""
    operations = {
        'add': a + b,
        'subtract': a - b,
        'multiply': a * b,
        'divide': a / b if b != 0 else 0
    }
    return {'operation': operation, 'a': a, 'b': b, 'result': operations.get(operation, 0)}

def file_read_tool(filename: str) -> str:
    """Simulated file read tool."""
    return f"Content of {filename} (simulated)"


# ========== Main Entry Point ==========
def main():
    """Main entry point for the LLM-powered agent."""
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 5 + "LLM-POWERED TASK AGENT" + " " * 28 + "║")
    print("╚" + "═" * 58 + "╝")
    
    print("\n🤖 Agent features:")
    print("   • LLM-powered task analysis")
    print("   • Automatic task breakdown")
    print("   • Tool execution")
    print("   • Human verification")
    print("   • Status tracking")
    
    agent = TaskAgent()
    
    # Register demo tools
    agent.register_tool('calculator', calculator_tool)
    agent.register_tool('file_read', file_read_tool)
    
    print("\n📝 Try these tasks:")
    print("   • 'Analyze 10 + 5 * 2 and verify'")
    print("   • 'Create a simple data report'")
    print("   • 'Design a solution for X'")
    print("\nEnter a task (type 'exit' to quit):")
    
    while True:
        user_input = input("\nYour task: ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Goodbye! 👋")
            break
        
        if not user_input:
            continue
        
        agent.run_workflow_with_llm(user_input)


if __name__ == "__main__":
    main()
