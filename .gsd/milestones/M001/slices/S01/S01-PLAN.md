# Slice 1: Core Pipeline

## Goal
Complete the data pipeline and orchestrator.

## Tasks

### T01: Verify Fetcher
**Status**: completed

Run fetch_feed.py and verify output.

**Plan:**
Test script execution.

**Must-Haves:**
- [x] Script runs without errors
- [x] data/latest.json is created
- [x] All 8 sources return data

**Summary:**
Fetcher works. Generates brief with 10 hot projects, 8 papers, 2 framework updates.

### T02: Fix Orchestrator
**Status**: completed

Fix runner.py to work with --job flag.

**Plan:**
Update run-orchestrated.sh and test.

**Must-Haves:**
- [x] runner.py accepts --job argument
- [x] Cron job runs successfully
- [x] Errors are logged

**Summary:**
Fixed syntax error. Changed `run full` to `run --job full`.

### T03: Generate Markdown
**Status**: completed

Create markdown brief generator.

**Plan:**
Build scripts/generate_readme.py

**Must-Haves:**
- [x] Script converts JSON to Markdown
- [x] Output is human-readable
- [x] Links work correctly

**Summary:**
Created generate_readme.py. Produces formatted markdown brief.

### T04: Add Notifications
**Status**: completed

Add Telegram notifications on success/failure.

**Plan:**
Update runner.py with notification logic.

**Must-Haves:**
- [x] Success notifications sent
- [x] Failure notifications sent
- [x] Includes summary stats

**Summary:**
Notifications working. Sends Telegram messages with job status.

## Verification

Run test:
```bash
cd /home/openclaw/.openclaw/workspace/fde-feed
python3 scripts/fetch_feed.py
```

Expected: Brief generated in data/latest.json and data/latest.md

## Summary

All tasks complete. Pipeline works end-to-end.
- Fetcher: ✅ Working
- Orchestrator: ✅ Fixed
- Markdown generator: ✅ Created
- Notifications: ✅ Working
