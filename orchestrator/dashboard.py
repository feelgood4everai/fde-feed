import streamlit as st
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

# Page config
st.set_page_config(
    page_title="FDE Job Orchestrator",
    page_icon="🎛️",
    layout="wide",
)

# Database path
DB_PATH = Path(__file__).parent / "jobs.db"

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============ UI ============

st.title("🎛️ FDE Job Orchestrator")
st.markdown("*Local job scheduling with observability*")

# Sidebar
def sidebar():
    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Go to", [
        "📊 Dashboard",
        "🔄 Job History", 
        "📋 Job Definitions",
        "🔔 Notifications",
        "⚙️ Settings"
    ])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Quick Actions**")
    
    if st.sidebar.button("🚀 Run Full Pipeline"):
        import subprocess
        result = subprocess.run(
            ["python3", "runner.py", "run", "full"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        st.sidebar.success("Pipeline triggered! Check Job History.")
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.experimental_rerun()
    
    return page

page = sidebar()

# ============ DASHBOARD PAGE ============

if page == "📊 Dashboard":
    st.header("Dashboard Overview")
    
    # Get stats
    conn = get_db()
    
    # Time range filter
    col1, col2 = st.columns(2)
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
        ("Total Jobs", stats["total"] or 0, "📊"),
        ("Success Rate", f"{(stats['success'] or 0) / (stats['total'] or 1) * 100:.1f}%", "✅"),
        ("Failures", stats["failed"] or 0, "❌"),
        ("Avg Duration", f"{stats['avg_duration'] or 0:.1f}s", "⏱️"),
    ]
    
    for col, (label, value, emoji) in zip(cols, metrics):
        col.metric(f"{emoji} {label}", value)
    
    # Recent jobs chart
    st.subheader("Job History (Last 7 Days)")
    
    cursor = conn.execute(
        """SELECT 
            date(started_at) as day,
            status,
            COUNT(*) as count
           FROM jobs 
           WHERE started_at > datetime('now', '-7 days')
           GROUP BY day, status
           ORDER BY day"""
    )
    
    chart_data = {}
    for row in cursor:
        day = row["day"]
        if day not in chart_data:
            chart_data[day] = {"success": 0, "failed": 0, "running": 0}
        chart_data[day][row["status"]] = row["count"]
    
    if chart_data:
        import pandas as pd
        df = pd.DataFrame([
            {"Date": day, "Success": data["success"], "Failed": data["failed"], "Running": data["running"]}
            for day, data in sorted(chart_data.items())
        ])
        st.bar_chart(df.set_index("Date"))
    
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
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.write(f"{status_emoji} **{row['job_name']}**")
            with col2:
                st.write(f"Status: `{row['status']}`")
            with col3:
                st.write(f"{row['started_at'][:16]}")
            
            if row["duration_seconds"]:
                st.caption(f"Duration: {row['duration_seconds']:.1f}s")
            if row["error_message"] and row["status"] == "failed":
                st.error(row["error_message"][:200])
    
    conn.close()

# ============ JOB HISTORY PAGE ============

elif page == "🔄 Job History":
    st.header("Job History")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "success", "failed", "running", "retrying"])
    with col2:
        job_filter = st.text_input("Job Name")
    with col3:
        limit = st.number_input("Show", min_value=10, max_value=500, value=50)
    
    # Query
    conn = get_db()
    
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
    
    # Display
    for row in rows:
        status_emoji = {
            "success": "✅",
            "failed": "❌",
            "running": "🔄",
            "retrying": "⏳",
            "pending": "⏸️"
        }.get(row["status"], "❓")
        
        with st.expander(f"{status_emoji} {row['job_name']} - {row['started_at']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Status:** {row['status']}")
                st.write(f"**Type:** {row['job_type']}")
                st.write(f"**Retries:** {row['retry_count']}/{row['max_retries']}")
            with col2:
                st.write(f"**Started:** {row['started_at']}")
                if row["completed_at"]:
                    st.write(f"**Completed:** {row['completed_at']}")
                if row["duration_seconds"]:
                    st.write(f"**Duration:** {row['duration_seconds']:.2f}s")
            
            if row["error_message"]:
                st.error(f"**Error:** {row['error_message']}")
            
            if row["log_output"]:
                with st.expander("View Logs"):
                    st.code(row["log_output"][:2000], language="text")
    
    conn.close()

# ============ JOB DEFINITIONS PAGE ============

elif page == "📋 Job Definitions":
    st.header("Job Definitions")
    
    conn = get_db()
    cursor = conn.execute("SELECT * FROM job_definitions ORDER BY name")
    jobs = cursor.fetchall()
    
    if not jobs:
        st.info("No job definitions yet. Add them via the database or configuration.")
    
    for job in jobs:
        with st.expander(f"⚙️ {job['name']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Command:** `{job['command']}`")
                st.write(f"**Schedule:** {job['schedule'] or 'Manual'}")
                st.write(f"**Working Dir:** {job['working_dir'] or 'Default'}")
            with col2:
                st.write(f"**Max Retries:** {job['max_retries']}")
                st.write(f"**Notify On:** {job['notify_on']}")
                st.write(f"**Enabled:** {'Yes' if job['enabled'] else 'No'}")
            
            if st.button(f"Run {job['name']}", key=f"run_{job['id']}"):
                st.info(f"Triggering {job['name']}...")
                # Would trigger the job here
    
    conn.close()

# ============ NOTIFICATIONS PAGE ============

elif page == "🔔 Notifications":
    st.header("Notification History")
    
    conn = get_db()
    cursor = conn.execute(
        """SELECT n.*, j.job_name 
           FROM notifications n
           LEFT JOIN jobs j ON n.job_id = j.id
           ORDER BY n.sent_at DESC LIMIT 50"""
    )
    
    for row in cursor:
        with st.container():
            st.write(f"📨 **{row['channel']}** - {row['job_name'] or 'System'}")
            st.write(row['message'][:200])
            st.caption(f"Sent: {row['sent_at']}")
            st.divider()
    
    conn.close()
    
    # Test notification
    st.subheader("Test Notification")
    if st.button("Send Test to Telegram"):
        # Would send test notification
        st.success("Test notification sent!")

# ============ SETTINGS PAGE ============

elif page == "⚙️ Settings":
    st.header("Settings")
    
    st.subheader("Database Info")
    
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
    db_size = DB_PATH.stat().st_size / 1024  # KB
    st.write(f"Database Size: {db_size:.1f} KB")
    
    if st.button("🗑️ Clear Old Logs (Keep 30 days)"):
        cursor = conn.execute(
            "DELETE FROM jobs WHERE started_at < datetime('now', '-30 days')"
        )
        conn.commit()
        st.success(f"Cleared {cursor.rowcount} old job records")
    
    conn.close()
    
    # Environment
    st.subheader("Environment Variables")
    st.code(f"""
TELEGRAM_BOT_TOKEN: {'Set' if st.secrets.get('TELEGRAM_BOT_TOKEN') else 'Not set'}
TELEGRAM_CHAT_ID: {st.secrets.get('TELEGRAM_CHAT_ID', 'Not set')}
    """)
