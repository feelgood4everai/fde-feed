#!/usr/bin/env python3
"""
Railway-compatible Streamlit dashboard for FDE Job Orchestrator
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="FDE Job Orchestrator",
    page_icon="🎛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database path - use /tmp for Railway (ephemeral) or persist if volume mounted
DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).parent / "jobs.db"))

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============ UI ============

def sidebar():
    with st.sidebar:
        st.title("🎛️ FDE Orchestrator")
        st.markdown("*Job scheduling with observability*")
        
        st.markdown("---")
        
        page = st.radio("Navigation", [
            "📊 Dashboard",
            "🔄 Job History", 
            "📋 Job Definitions",
            "🔔 Notifications",
            "⚙️ Settings"
        ])
        
        st.markdown("---")
        
        st.markdown("**Quick Actions**")
        if st.button("🚀 Run Full Pipeline", use_container_width=True):
            st.info("Pipeline triggered! Check Job History for status.")
            # In production, this would trigger the actual job
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("**Links**")
        st.markdown("[📁 FDE-Feed Repo](https://github.com/feelgood4everai/fde-feed)")
        st.markdown("[🌐 Public Dashboard](https://anandgeetha-fde-feed.hf.space)")
        
    return page

# ============ DASHBOARD PAGE ============

def dashboard_page():
    st.header("Dashboard Overview")
    
    try:
        conn = get_db()
        
        # Time range filter
        col1, col2 = st.columns([1, 3])
        with col1:
            days_back = st.selectbox("Time Range", [7, 14, 30, 90], index=0)
        
        since = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        # Metrics
        cursor = conn.execute(
            """SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
                AVG(duration_seconds) as avg_duration
               FROM jobs WHERE started_at > ?""",
            (since,)
        )
        stats = cursor.fetchone()
        
        cols = st.columns(4)
        metrics = [
            ("Total Jobs", stats["total"] or 0, "📊", "blue"),
            ("Success Rate", f"{(stats['success'] or 0) / (stats['total'] or 1) * 100:.1f}%", "✅", "green"),
            ("Failures", stats["failed"] or 0, "❌", "red"),
            ("Avg Duration", f"{stats['avg_duration'] or 0:.1f}s", "⏱️", "orange"),
        ]
        
        for col, (label, value, emoji, color) in zip(cols, metrics):
            with col:
                st.metric(f"{emoji} {label}", value)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Job Status Distribution")
            status_data = {
                'Status': ['Success', 'Failed', 'Running', 'Retrying'],
                'Count': [
                    stats['success'] or 0,
                    stats['failed'] or 0,
                    stats['running'] or 0,
                    0  # Would need to query separately
                ]
            }
            df_status = pd.DataFrame(status_data)
            fig = px.pie(df_status, values='Count', names='Status', 
                        color_discrete_sequence=['#10B981', '#EF4444', '#3B82F6', '#F59E0B'])
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Jobs Over Time")
            cursor = conn.execute(
                """SELECT 
                    date(started_at) as day,
                    COUNT(*) as count
                   FROM jobs 
                   WHERE started_at > datetime('now', '-7 days')
                   GROUP BY day
                   ORDER BY day"""
            )
            rows = cursor.fetchall()
            if rows:
                df_time = pd.DataFrame([
                    {"Date": row["day"], "Jobs": row["count"]} for row in rows
                ])
                fig = px.bar(df_time, x='Date', y='Jobs', color_discrete_sequence=['#3B82F6'])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data for the selected period")
        
        # Recent activity
        st.subheader("Recent Activity")
        
        cursor = conn.execute(
            """SELECT job_name, status, started_at, duration_seconds, error_message
               FROM jobs ORDER BY started_at DESC LIMIT 10"""
        )
        
        for row in cursor:
            status_emoji = {
                "success": "✅",
                "failed": "❌",
                "running": "🔄",
                "retrying": "⏳"
            }.get(row["status"], "❓")
            
            with st.container():
                cols = st.columns([3, 2, 2, 2])
                with cols[0]:
                    st.write(f"{status_emoji} **{row['job_name']}**")
                with cols[1]:
                    st.write(f"`{row['status']}`")
                with cols[2]:
                    st.write(f"{row['started_at'][:16]}")
                with cols[3]:
                    if row["duration_seconds"]:
                        st.write(f"{row['duration_seconds']:.1f}s")
                    else:
                        st.write("-")
                
                if row["error_message"] and row["status"] == "failed":
                    st.error(row["error_message"][:200])
        
        conn.close()
        
    except Exception as e:
        st.error(f"Database error: {e}")
        st.info("Make sure the database is initialized. Run: `python runner.py init`")

# ============ JOB HISTORY PAGE ============

def history_page():
    st.header("Job History")
    
    try:
        conn = get_db()
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Status", ["All", "success", "failed", "running", "retrying"])
        with col2:
            job_filter = st.text_input("Job Name")
        with col3:
            limit = st.number_input("Show", min_value=10, max_value=500, value=50)
        
        # Query
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []
        
        if status_filter != "All":
            query += " AND status = ?"
            params.append(status_filter)
        
        if job_filter:
            query += " AND job_name LIKE ?"
            params.append(f"%{job_filter}%")
        
        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        # Display as dataframe
        if rows:
            df_data = []
            for row in rows:
                df_data.append({
                    "ID": row["id"],
                    "Job": row["job_name"],
                    "Status": row["status"],
                    "Started": row["started_at"][:16] if row["started_at"] else "",
                    "Duration": f"{row['duration_seconds']:.1f}s" if row["duration_seconds"] else "-",
                    "Retries": row["retry_count"],
                })
            
            df = pd.DataFrame(df_data)
            
            # Color code status
            def color_status(val):
                colors = {
                    'success': 'background-color: #10B981; color: white',
                    'failed': 'background-color: #EF4444; color: white',
                    'running': 'background-color: #3B82F6; color: white',
                    'retrying': 'background-color: #F59E0B; color: white'
                }
                return colors.get(val, '')
            
            styled_df = df.style.applymap(color_status, subset=['Status'])
            st.dataframe(styled_df, use_container_width=True)
            
            # Detail view
            st.subheader("Job Details")
            selected_job = st.selectbox("Select job for details", 
                                       [f"#{r['id']} - {r['job_name']} ({r['started_at'][:16]})" for r in rows])
            
            if selected_job:
                job_id = int(selected_job.split("#")[1].split("-")[0])
                cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
                job = cursor.fetchone()
                
                if job:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Status:** {job['status']}")
                        st.write(f"**Type:** {job['job_type']}")
                        st.write(f"**Retries:** {job['retry_count']}/{job['max_retries']}")
                    with col2:
                        st.write(f"**Started:** {job['started_at']}")
                        if job["completed_at"]:
                            st.write(f"**Completed:** {job['completed_at']}")
                        if job["duration_seconds"]:
                            st.write(f"**Duration:** {job['duration_seconds']:.2f}s")
                    
                    if job["error_message"]:
                        st.error(f"**Error:** {job['error_message']}")
                    
                    if job["log_output"]:
                        with st.expander("View Logs"):
                            st.code(job["log_output"][:5000], language="text")
        else:
            st.info("No jobs found matching your criteria")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error: {e}")

# ============ JOB DEFINITIONS PAGE ============

def definitions_page():
    st.header("Job Definitions")
    
    st.info("Job definitions are configured in the database. These are the currently scheduled jobs:")
    
    jobs = [
        {
            "name": "fetch_fde_feed",
            "description": "Fetches FDE-Feed data from GitHub, HF, Reddit, etc.",
            "schedule": "Every 2 days at 9am UTC",
            "max_retries": 3,
            "notify_on": "failure"
        },
        {
            "name": "generate_readme",
            "description": "Generates README.md from latest.json",
            "schedule": "After fetch completes",
            "max_retries": 2,
            "notify_on": "failure"
        },
        {
            "name": "push_to_github",
            "description": "Commits and pushes changes to GitHub",
            "schedule": "After README generation",
            "max_retries": 2,
            "notify_on": "failure"
        },
        {
            "name": "full_update_pipeline",
            "description": "Complete pipeline: fetch → generate → push",
            "schedule": "Every 2 days (cron)",
            "max_retries": 3,
            "notify_on": "always"
        }
    ]
    
    for job in jobs:
        with st.expander(f"⚙️ {job['name']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Description:** {job['description']}")
                st.write(f"**Schedule:** {job['schedule']}")
            with col2:
                st.write(f"**Max Retries:** {job['max_retries']}")
                st.write(f"**Notify On:** {job['notify_on']}")

# ============ NOTIFICATIONS PAGE ============

def notifications_page():
    st.header("Notification History")
    
    try:
        conn = get_db()
        cursor = conn.execute(
            """SELECT n.*, j.job_name 
               FROM notifications n
               LEFT JOIN jobs j ON n.job_id = j.id
               ORDER BY n.sent_at DESC LIMIT 50"""
        )
        
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                with st.container():
                    st.write(f"📨 **{row['channel']}** - {row['job_name'] or 'System'}")
                    st.write(row['message'][:300])
                    st.caption(f"Sent: {row['sent_at']}")
                    st.divider()
        else:
            st.info("No notifications sent yet")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error: {e}")
    
    # Test notification
    st.subheader("Test Notification")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Send Test to Telegram"):
            st.success("Test notification would be sent!")
    with col2:
        if st.button("Test Email"):
            st.info("Email notifications not configured")

# ============ SETTINGS PAGE ============

def settings_page():
    st.header("Settings")
    
    st.subheader("Database Info")
    
    try:
        conn = get_db()
        
        # Table sizes
        cursor = conn.execute("SELECT COUNT(*) FROM jobs")
        job_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM notifications")
        notif_count = cursor.fetchone()[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Jobs Logged", job_count)
        with col2:
            st.metric("Notifications Sent", notif_count)
        
        # Database size
        if DB_PATH.exists():
            db_size = DB_PATH.stat().st_size / 1024  # KB
            st.write(f"Database Size: {db_size:.1f} KB")
            st.write(f"Database Path: {DB_PATH}")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Database error: {e}")
    
    st.subheader("Maintenance")
    if st.button("🗑️ Clear Old Logs (Keep 30 days)", type="secondary"):
        try:
            conn = get_db()
            cursor = conn.execute(
                "DELETE FROM jobs WHERE started_at < datetime('now', '-30 days')"
            )
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            st.success(f"Cleared {deleted} old job records")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.subheader("Environment")
    st.code(f"""
DB_PATH: {DB_PATH}
PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}
RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT', 'Not set')}
    """)

# ============ MAIN ============

def main():
    page = sidebar()
    
    if page == "📊 Dashboard":
        dashboard_page()
    elif page == "🔄 Job History":
        history_page()
    elif page == "📋 Job Definitions":
        definitions_page()
    elif page == "🔔 Notifications":
        notifications_page()
    elif page == "⚙️ Settings":
        settings_page()

if __name__ == "__main__":
    main()
