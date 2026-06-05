#!/usr/bin/env python3
"""
Launcher script for LLM-Integrated Task Agent
"""
import sys
sys.path.insert(0, '/home/chetansurya/task_agent')

from hermes.agent_llm import main as agent_main

if __name__ == "__main__":
    agent_main()
