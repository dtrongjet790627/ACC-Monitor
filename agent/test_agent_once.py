# -*- coding: utf-8 -*-
"""Single-shot test: collect metrics once, report once, then exit."""
import sys
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Reuse the agent code
from acc_monitor_agent_windows import load_config, AccMonitorAgent
import json

config = load_config()
if config["server_id"] == "CHANGE_ME":
    print("[ERROR] server_id not set in agent_config.json")
    sys.exit(1)

agent = AccMonitorAgent(config)
metrics = agent.collect()
print("\n=== Collected Metrics ===")
print(json.dumps(metrics, indent=2, ensure_ascii=False))

success = agent.report(metrics)
print(f"\n=== Report to {agent.monitor_url}: {'SUCCESS' if success else 'FAILED'} ===")
