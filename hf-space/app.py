import streamlit as st
import json
from datetime import datetime
from pathlib import Path
import pandas as pd

# Page config
st.set_page_config(
    page_title="FDE-Feed | Forward Deployed Intelligence",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
    }
    .alert-critical {
        background: #fee2e2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .alert-medium {
        background: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .opportunity-card {
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .project-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data(ttl=300)
def load_brief():
    """Load the latest FDE brief."""
    data_file = Path(__file__).parent.parent / "data" / "latest.json"
    if data_file.exists():
        with open(data_file) as f:
            return json.load(f)
    return None

brief = load_brief()

if not brief:
    st.error("❌ No brief data found. Please run the fetcher first.")
    st.stop()

# Sidebar
st.sidebar.markdown("## 🚀 FDE-Feed")
st.sidebar.markdown("*Forward Deployed Intelligence*")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "🔥 Hot Projects", "📚 Research", "💼 Opportunities", "🚨 Alerts", "📜 History"]
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Edition:** {brief.get('edition', 'Unknown')}")
st.sidebar.markdown(f"**Generated:** {brief.get('generated_at', 'Unknown')[:10]}")

# Main content based on page
if page == "📊 Dashboard":
    st.markdown('<p class="main-header">FDE-Feed Dashboard</p>', unsafe_allow_html=True)
    st.markdown("*Curated intelligence for Forward Deployed Engineers*")
    st.markdown("---")
    
    # Metrics
    cols = st.columns(6)
    metrics = brief.get('summary', {})
    
    with cols[0]:
        st.metric("🚨 Alerts", metrics.get('urgent_alerts', 0))
    with cols[1]:
        st.metric("🔥 Projects", metrics.get('hot_projects', 0))
    with cols[2]:
        st.metric("📚 Papers", metrics.get('research_papers', 0))
    with cols[3]:
        st.metric("💬 Discussions", metrics.get('community_discussions', 0))
    with cols[4]:
        st.metric("💼 Opportunities", metrics.get('fde_opportunities', 0))
    with cols[5]:
        st.metric("🔧 Updates", metrics.get('framework_updates', 0))
    
    st.markdown("---")
    
    # Two column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Urgent alerts
        st.subheader("🚨 Urgent Alerts")
        alerts = brief.get('urgent_alerts', [])
        if alerts:
            for alert in alerts[:3]:
                severity_class = "alert-critical" if alert.get('severity') == 'critical' else "alert-medium"
                st.markdown(f'''
                <div class="{severity_class}">
                    <strong>{alert.get('title', 'Unknown')}</strong><br>
                    <small>Impact: {alert.get('impact', 'Unknown')}</small><br>
                    <small>Action: {alert.get('action', 'Review')}</small>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.info("No urgent alerts today. ✨")
        
        # Deep dive
        st.subheader("🔍 Deep Dive")
        deep_dive = brief.get('deep_dive', {})
        if deep_dive:
            st.markdown(f"**{deep_dive.get('topic', 'No topic')}**")
            st.markdown(deep_dive.get('summary', 'No summary available.'))
            st.markdown(f"*FDE Takeaway: {deep_dive.get('fde_takeaway', 'Review for applicability')}*")
    
    with col2:
        # FDE Opportunities
        st.subheader("💼 Top Opportunities")
        opportunities = brief.get('fde_opportunities', [])
        if opportunities:
            for opp in opportunities[:3]:
                st.markdown(f'''
                <div class="opportunity-card">
                    <strong>{opp.get('title', 'Unknown')}</strong><br>
                    <small>{opp.get('description', '')[:100]}...</small><br>
                    <small>💰 Potential: {opp.get('potential_value', 'TBD')}</small>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.info("No opportunities identified yet.")
        
        # Framework updates
        st.subheader("🔧 Framework Updates")
        updates = brief.get('hot_this_week', {}).get('framework_updates', [])
        if updates:
            for update in updates[:2]:
                st.markdown(f"• **{update.get('framework', 'Unknown')}** {update.get('version', '')}")
        else:
            st.info("No updates today.")

elif page == "🔥 Hot Projects":
    st.markdown('<p class="main-header">Hot Projects</p>', unsafe_allow_html=True)
    
    projects = brief.get('hot_this_week', {}).get('github_trending', [])
    
    # Filter options
    search = st.text_input("🔍 Search projects", "")
    
    filtered = projects
    if search:
        filtered = [p for p in projects if search.lower() in p.get('name', '').lower() or 
                    search.lower() in p.get('description', '').lower()]
    
    st.markdown(f"Showing {len(filtered)} projects")
    
    for project in filtered:
        with st.container():
            st.markdown(f'''
            <div class="project-card">
                <h4><a href="{project.get('url', '#')}" target="_blank">{project.get('name', 'Unknown')}</a> 
                ⭐ {project.get('stars', 0):,}</h4>
                <p>{project.get('description', 'No description')}</p>
                <p><small><strong>FDE Relevance:</strong> {project.get('fde_relevance', 'Unknown')}</small></p>
                <p><small><strong>Use Case:</strong> {project.get('fde_use_case', 'Evaluate')}</small></p>
                {f"<span style='background: #e0e7ff; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;'>{project.get('language')}</span>" if project.get('language') else ""}
            </div>
            ''', unsafe_allow_html=True)

elif page == "📚 Research":
    st.markdown('<p class="main-header">Research Roundup</p>', unsafe_allow_html=True)
    
    papers = brief.get('research_roundup', [])
    
    for paper in papers:
        with st.expander(f"📄 {paper.get('title', 'Untitled')[:60]}..."):
            st.markdown(f"**Authors:** {', '.join(paper.get('authors', ['Unknown'])[:3])}")
            st.markdown(f"**Summary:** {paper.get('tldr', 'No summary')}")
            st.markdown(f"**FDE Takeaway:** *{paper.get('fde_takeaway', 'Review for applicability')}*")
            if paper.get('url'):
                st.markdown(f"[Read Paper]({paper['url']})")

elif page == "💼 Opportunities":
    st.markdown('<p class="main-header">FDE Opportunities</p>', unsafe_allow_html=True)
    
    opportunities = brief.get('fde_opportunities', [])
    
    if not opportunities:
        st.info("No opportunities identified in this edition.")
    else:
        for opp in opportunities:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f'''
                <div class="opportunity-card">
                    <h4>{opp.get('title', 'Unknown')}</h4>
                    <p>{opp.get('description', '')}</p>
                    <p><strong>Client Type:</strong> {opp.get('client_type', 'General')}</p>
                    <p><strong>Your Move:</strong> {opp.get('your_move', 'Evaluate')}</p>
                </div>
                ''', unsafe_allow_html=True)
            with col2:
                st.metric("Potential Value", opp.get('potential_value', 'TBD'))
                st.caption(f"Type: {opp.get('type', 'general')}")

elif page == "🚨 Alerts":
    st.markdown('<p class="main-header">Urgent Alerts</p>', unsafe_allow_html=True)
    
    alerts = brief.get('urgent_alerts', [])
    
    if not alerts:
        st.success("✅ No urgent alerts. All systems nominal.")
    else:
        for alert in alerts:
            severity = alert.get('severity', 'medium')
            if severity == 'critical':
                st.error(f'''
                ### 🚨 CRITICAL: {alert.get('title', 'Unknown')}
                
                **Source:** {alert.get('source', 'Unknown')}
                
                **Impact:** {alert.get('impact', 'Unknown')}
                
                **Action Required:** {alert.get('action', 'Review immediately')}
                
                [More Info]({alert.get('url', '#')})
                ''')
            else:
                st.warning(f'''
                ### ⚠️ {alert.get('title', 'Unknown')}
                
                **Source:** {alert.get('source', 'Unknown')}
                
                **Impact:** {alert.get('impact', 'Unknown')}
                
                **Action:** {alert.get('action', 'Review')}
                ''')

elif page == "📜 History":
    st.markdown('<p class="main-header">Brief History</p>', unsafe_allow_html=True)
    
    archive_dir = Path(__file__).parent.parent / "data" / "archive"
    
    if archive_dir.exists():
        archives = sorted(archive_dir.glob("*.json"), reverse=True)
        
        if archives:
            selected = st.selectbox(
                "Select edition",
                options=archives,
                format_func=lambda x: x.stem
            )
            
            if selected:
                with open(selected) as f:
                    old_brief = json.load(f)
                
                st.json(old_brief.get('summary', {}))
        else:
            st.info("No archived editions yet.")
    else:
        st.info("Archive directory not found.")

# Footer
st.markdown("---")
st.markdown(
    "<center>Generated with ❤️ for Forward Deployed Engineers | "
    "<a href='https://github.com/feelgood4everai/fde-feed'>GitHub</a> | "
    "<a href='https://huggingface.co/spaces/AnandGeetha/fde-feed'>Hugging Face</a></center>",
    unsafe_allow_html=True
)
