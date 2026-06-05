#!/usr/bin/env python3
"""
Test script for Simple Task Agent
Demonstrates all workflow steps with example tasks.
"""

import sys
sys.path.insert(0, '/home/chetansurya/task_agent')

from hermes.agent import TaskAgent, TASK_COMPLETED, TASK_PENDING

def test_task_identification():
    """Test task identification step."""
    print("\n" + "=" * 60)
    print("TEST 1: Task Identification")
    print("=" * 60)
    
    agent = TaskAgent()
    test_input = "Analyze this file and summarize its contents"
    
    task = agent.identify_task(test_input)
    print(f"\nOriginal task: {task.name}")
    print(f"Description: {task.description}")
    print(f"Task ID: {task.id}")
    
    return agent, task

def test_task_breakdown():
    """Test task breakdown into subtasks."""
    print("\n" + "=" * 60)
    print("TEST 2: Task Breakdown")
    print("=" * 60)
    
    agent = TaskAgent()
    test_input = "Design a solution for processing user data"
    task = agent.identify_task(test_input)
    
    print(f"\nBreaking down: {task.name}")
    print()
    
    subtasks = agent.break_down_task(task)
    
    print("\nSubtasks created:")
    for i, subtask in enumerate(subtasks, 1):
        print(f"  {i}. [{subtask.status}] {subtask.name}")
        print(f"     → {subtask.description}")
    
    return agent, task

def test_tool_registration():
    """Test tool registration and execution."""
    print("\n" + "=" * 60)
    print("TEST 3: Tool Execution")
    print("=" * 60)
    
    agent = TaskAgent()
    
    # Register a custom tool
    def my_custom_tool(param1, param2):
        return f"Result of {param1} and {param2}"
    
    agent.register_tool('custom_tool', my_custom_tool)
    print(f"\nRegistered tool: custom_tool")
    
    # Execute the tool
    result = agent.execute_tool_call('custom_tool', 'hello', 'world')
    print(f"Tool result: {result}")
    
    return agent

def test_full_workflow():
    """Test the complete agent workflow."""
    print("\n" + "=" * 60)
    print("TEST 4: Full Workflow (Interactive Demo)")
    print("=" * 60)
    
    agent = TaskAgent()
    
    # Register demo tools
    agent.register_tool('calculator', lambda op, a, b: {'op': op, 'a': a, 'b': b, 'result': a+b if op=='add' else a-b if op=='subtract' else a*b if op=='multiply' else a/b if op=='divide' and b!=0 else 0})
    agent.register_tool('file_read', lambda filename: f"Content of {filename}")
    
    test_cases = [
        "Calculate 5 + 3 * 2",
        "Read and summarize example.txt",
        "Test the calculator and verify results"
    ]
    
    for task_input in test_cases:
        print(f"\n{'─' * 60}")
        print(f"TASK INPUT: {task_input}")
        print(f"{'─' * 60}")
        
        agent.run_workflow(task_input)
    
    return agent

def test_status_tracking():
    """Test task status tracking."""
    print("\n" + "=" * 60)
    print("TEST 5: Status Tracking")
    print("=" * 60)
    
    agent = TaskAgent()
    test_input = "Verify the output and report status"
    
    task = agent.identify_task(test_input)
    agent.tasks[task.id] = task
    
    # Test status transitions
    statuses = [TASK_COMPLETED, TASK_PENDING]
    
    for status in statuses:
        agent.update_task_status(task, status, f"Test status: {status}")
        current_status = agent.get_task_status(task.id)
        print(f"Current status: {current_status}")
    
    return agent

def main():
    """Run all tests."""
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 2 + "SIMPLE TASK AGENT - TEST SUITE" + " " * 26 + "║")
    print("╚" + "═" * 58 + "╝")
    
    tests = [
        ("Task Identification", test_task_identification),
        ("Task Breakdown", test_task_breakdown),
        ("Tool Registration", test_tool_registration),
        ("Full Workflow", test_full_workflow),
        ("Status Tracking", test_status_tracking),
    ]
    
    print("\nRunning tests...\n")
    print("-" * 60)
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"\n✓ {name} PASSED\n")
        except Exception as e:
            print(f"\n✗ {name} FAILED: {e}\n")
    
    print("-" * 60)
    print("\nAll tests completed! 🎉")

if __name__ == "__main__":
    main()
