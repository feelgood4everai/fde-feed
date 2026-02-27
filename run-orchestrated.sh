#!/bin/bash
# FDE-Feed Automation with Orchestrator
# Run by system cron every 2 days

export PYTHONPATH="/home/openclaw/.openclaw/workspace/fde-feed:$PYTHONPATH"
export TELEGRAM_CHAT_ID="6410873758"

cd /home/openclaw/.openclaw/workspace/fde-feed/orchestrator

# Run full pipeline through orchestrator
python3 runner.py run full >> /home/openclaw/logs/fde-feed-cron.log 2>&1
