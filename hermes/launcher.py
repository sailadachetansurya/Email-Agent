#!/usr/bin/env python3
"""
Launcher script for Simple Task Agent
"""
import sys
sys.path.insert(0, '/home/chetansurya/task_agent')

from hermes.agent import main as agent_main

if __name__ == "__main__":
    agent_main()
