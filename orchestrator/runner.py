#!/usr/bin/env python3
"""
FDE Job Orchestrator - Core Runner
Handles job execution with retries, logging, and notifications
"""

import os
import sys
import json
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
import traceback

# Configuration
DB_PATH = Path(__file__).parent / "jobs.db"
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Telegram notification settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6410873758")  # Your chat ID

def init_db():
    """Initialize database with schema."""
    conn = sqlite3.connect(DB_PATH)
    with open(Path(__file__).parent / "schema.sql") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_job(job_name, job_type="cron", metadata=None):
    """Log job start and return job ID."""
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO jobs (job_name, job_type, status, metadata)
           VALUES (?, ?, 'running', ?)""",
        (job_name, job_type, json.dumps(metadata or {}))
    )
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return job_id

def update_job_status(job_id, status, error_message=None, log_output=None):
    """Update job status."""
    conn = get_db()
    
    if status in ['success', 'failed']:
        conn.execute(
            """UPDATE jobs 
               SET status = ?, completed_at = CURRENT_TIMESTAMP,
                   error_message = ?, log_output = ?
               WHERE id = ?""",
            (status, error_message, log_output, job_id)
        )
    else:
        conn.execute(
            "UPDATE jobs SET status = ? WHERE id = ?",
            (status, job_id)
        )
    
    # Calculate duration
    conn.execute(
        """UPDATE jobs 
           SET duration_seconds = ROUND((julianday(completed_at) - julianday(started_at)) * 86400, 2)
           WHERE id = ? AND completed_at IS NOT NULL""",
        (job_id,)
    )
    
    conn.commit()
    conn.close()

def send_telegram_notification(message, job_id=None):
    """Send notification to Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        print("[Notification] No Telegram token configured")
        return
    
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        
        # Log notification
        conn = get_db()
        conn.execute(
            "INSERT INTO notifications (job_id, channel, message) VALUES (?, 'telegram', ?)",
            (job_id, message)
        )
        conn.commit()
        conn.close()
        
        return response.status_code == 200
    except Exception as e:
        print(f"[Notification Error] {e}")
        return False

def with_retry(max_retries=3, notify_on="failure"):
    """Decorator to add retry logic to jobs."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            job_name = func.__name__
            job_id = log_job(job_name, "manual" if kwargs.get('manual') else "cron")
            
            log_file = LOG_DIR / f"{job_name}_{job_id}.log"
            log_output = []
            
            for attempt in range(1, max_retries + 1):
                try:
                    print(f"[Job {job_id}] Attempt {attempt}/{max_retries}")
                    
                    # Run the function
                    result = func(*args, **kwargs)
                    
                    # Success
                    update_job_status(job_id, "success", log_output="\n".join(log_output))
                    
                    if notify_on in ["always", "success"]:
                        send_telegram_notification(
                            f"✅ *Job Success: {job_name}*\n\nCompleted in {attempt} attempt(s)",
                            job_id
                        )
                    
                    return result
                    
                except Exception as e:
                    error_msg = str(e)
                    tb = traceback.format_exc()
                    log_output.append(f"Attempt {attempt} failed: {error_msg}\n{tb}")
                    
                    print(f"[Job {job_id}] Attempt {attempt} failed: {error_msg}")
                    
                    if attempt < max_retries:
                        # Update status to retrying
                        update_job_status(job_id, "retrying", error_message=error_msg)
                        # Wait before retry (exponential backoff)
                        import time
                        wait_time = 2 ** attempt
                        print(f"[Job {job_id}] Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        # Final failure
                        update_job_status(job_id, "failed", 
                                        error_message=error_msg,
                                        log_output="\n".join(log_output))
                        
                        if notify_on in ["always", "failure"]:
                            send_telegram_notification(
                                f"❌ *Job Failed: {job_name}*\n\nError: {error_msg[:200]}...\n\nCheck dashboard for details",
                                job_id
                            )
                        
                        raise
            
        return wrapper
    return decorator

def run_command(command, cwd=None, timeout=300):
    """Run shell command and return output."""
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    
    if result.returncode != 0:
        raise Exception(f"Command failed with code {result.returncode}:\n{result.stderr}")
    
    return result.stdout

# ============ JOB DEFINITIONS ============

@with_retry(max_retries=3, notify_on="failure")
def fetch_fde_feed():
    """Fetch FDE Feed data."""
    print("[Job] Starting FDE Feed fetch...")
    
    # Run the fetch script
    script_path = Path(__file__).parent.parent / "scripts" / "fetch_feed.py"
    output = run_command(f"python3 {script_path}")
    
    print("[Job] Fetch complete")
    return output

@with_retry(max_retries=2, notify_on="failure")
def generate_readme():
    """Generate README from brief."""
    print("[Job] Generating README...")
    
    script_path = Path(__file__).parent.parent / "scripts" / "generate_readme.py"
    output = run_command(f"python3 {script_path}")
    
    print("[Job] README generated")
    return output

@with_retry(max_retries=2, notify_on="failure")
def push_to_github():
    """Push changes to GitHub."""
    print("[Job] Pushing to GitHub...")
    
    repo_path = Path(__file__).parent.parent
    run_command("git add -A", cwd=repo_path)
    run_command(f'git commit -m "Update FDE Brief: {datetime.now().isoformat()}"', cwd=repo_path)
    run_command("git push origin main", cwd=repo_path)
    
    print("[Job] Push complete")
    return "Pushed successfully"

@with_retry(max_retries=3, notify_on="always")
def full_update_pipeline():
    """Complete pipeline: fetch, generate, push."""
    print("="*60)
    print("[Pipeline] Starting full FDE Feed update")
    print("="*60)
    
    # Step 1: Fetch
    fetch_fde_feed()
    
    # Step 2: Generate README
    generate_readme()
    
    # Step 3: Generate LinkedIn posts
    script_path = Path(__file__).parent.parent / "scripts" / "generate_posts.py"
    run_command(f"python3 {script_path}")
    
    # Step 4: Push to GitHub
    push_to_github()
    
    print("="*60)
    print("[Pipeline] Complete!")
    print("="*60)
    
    return "Pipeline completed successfully"

# ============ CLI INTERFACE ============

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FDE Job Orchestrator")
    parser.add_argument("command", choices=["init", "run", "status", "history", "dashboard"])
    parser.add_argument("--job", help="Job name to run")
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_db()
        print("✅ Database initialized")
    
    elif args.command == "run":
        if args.job == "fetch":
            fetch_fde_feed()
        elif args.job == "readme":
            generate_readme()
        elif args.job == "push":
            push_to_github()
        elif args.job == "full" or not args.job:
            full_update_pipeline()
        else:
            print(f"Unknown job: {args.job}")
    
    elif args.command == "status":
        conn = get_db()
        cursor = conn.execute(
            """SELECT job_name, status, started_at, duration_seconds, error_message 
               FROM jobs ORDER BY started_at DESC LIMIT 10"""
        )
        rows = cursor.fetchall()
        
        print("\n📊 Recent Jobs:")
        print("-" * 80)
        for row in rows:
            status_emoji = {
                "success": "✅",
                "failed": "❌",
                "running": "🔄",
                "retrying": "⏳",
                "pending": "⏸️"
            }.get(row["status"], "❓")
            
            print(f"{status_emoji} {row['job_name']:<20} | {row['status']:<10} | {row['started_at']}")
            if row["duration_seconds"]:
                print(f"   Duration: {row['duration_seconds']:.1f}s")
            if row["error_message"]:
                print(f"   Error: {row['error_message'][:50]}...")
        
        conn.close()
    
    elif args.command == "history":
        conn = get_db()
        
        # Success rate
        cursor = conn.execute(
            """SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
               FROM jobs"""
        )
        stats = cursor.fetchone()
        
        print("\n📈 Job Statistics (All Time):")
        print(f"  Total: {stats['total']}")
        print(f"  Success: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
        print(f"  Failed: {stats['failed']}")
        
        # Recent failures
        cursor = conn.execute(
            """SELECT job_name, started_at, error_message 
               FROM jobs WHERE status = 'failed' 
               ORDER BY started_at DESC LIMIT 5"""
        )
        failures = cursor.fetchall()
        
        if failures:
            print("\n❌ Recent Failures:")
            for row in failures:
                print(f"  {row['job_name']} at {row['started_at']}")
                print(f"    {row['error_message'][:100]}...")
        
        conn.close()
    
    elif args.command == "dashboard":
        print("\n🌐 Starting dashboard...")
        print("Open http://localhost:8501 in your browser")
        
        dashboard_path = Path(__file__).parent / "dashboard.py"
        os.system(f"streamlit run {dashboard_path}")
