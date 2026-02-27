import streamlit as st
import requests
import json
from datetime import datetime

# Configuration
GITHUB_RAW_URL = "https://raw.githubusercontent.com/feelgood4everai/fde-feed/main/data/latest.json"

st.set_page_config(
    page_title="FDE-Feed Dashboard",
    page_icon="🚀",
    layout="wide",
)

@st.cache_data(ttl=3600)
def load_latest_brief():
    """Load latest brief from GitHub."""
    try:
        resp = requests.get(GITHUB_RAW_URL, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.error(f"Error loading brief: {e}")
    return None

def main():
    st.title("🚀 FDE-Feed Dashboard")
    st.markdown("*Curated intelligence for Forward Deployed Engineers*")
    
    brief = load_latest_brief()
    
    if not brief:
        st.error("Could not load FDE brief. Please try again later.")
        return
    
    summary = brief.get('summary', {})
    generated = brief.get('generated_at', 'Unknown')[:10]
    next_update = brief.get('metadata', {}).get('next_update', 'Unknown')[:10]
    
    # Summary metrics
    st.header(f"📊 Brief Summary — {generated}")
    
    cols = st.columns(5)
    metrics = [
        ("🚨 Urgent", summary.get('urgent_alerts', 0)),
        ("🔥 Projects", summary.get('hot_projects', 0)),
        ("📚 Papers", summary.get('research_papers', 0)),
        ("💬 Community", summary.get('community_discussions', 0)),
        ("💼 Opportunities", summary.get('fde_opportunities', 0)),
    ]
    
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)
    
    st.info(f"**Next Update:** {next_update}")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚨 Alerts", "🔥 Hot Projects", "📚 Research", "💼 Opportunities", "🔬 Deep Dive"])
    
    with tab1:
        st.subheader("Urgent Alerts")
        alerts = brief.get('urgent_alerts', [])
        if alerts:
            for alert in alerts:
                severity = alert.get('severity', 'medium').upper()
                color = {'CRITICAL': 'red', 'HIGH': 'orange', 'MEDIUM': 'blue'}.get(severity, 'gray')
                with st.container():
                    st.markdown(f"### :{color}[🚨 {severity}: {alert.get('title', 'Alert')}]")
                    st.write(f"**Impact:** {alert.get('impact', 'N/A')}")
                    st.write(f"**Action:** {alert.get('action', 'Check details')}")
                    if alert.get('url'):
                        st.link_button("View Details", alert['url'])
        else:
            st.success("✅ No urgent alerts at this time.")
    
    with tab2:
        st.subheader("GitHub Trending")
        repos = brief.get('hot_this_week', {}).get('github_trending', [])
        if repos:
            for repo in repos:
                with st.container():
                    st.markdown(f"### ⭐ {repo.get('name', 'Unknown')} ({repo.get('stars', 0):,} stars)")
                    st.write(repo.get('description', 'No description'))
                    st.write(f"**Why FDEs Care:** {repo.get('fde_relevance', '')}")
                    st.write(f"**Use Case:** {repo.get('fde_use_case', '')}")
                    st.link_button("View on GitHub", repo.get('url', '#'))
        else:
            st.info("No trending repos this cycle.")
    
    with tab3:
        st.subheader("Research Papers")
        papers = brief.get('research_roundup', [])
        if papers:
            for paper in papers:
                with st.container():
                    st.markdown(f"### 📄 {paper.get('title', 'Untitled')}")
                    st.write(f"**TL;DR:** {paper.get('tldr', 'No summary')}")
                    st.info(f"**FDE Takeaway:** {paper.get('fde_takeaway', '')}")
                    if paper.get('url'):
                        st.link_button("Read Paper", paper['url'])
        else:
            st.info("No new papers this cycle.")
    
    with tab4:
        st.subheader("FDE Opportunities")
        opportunities = brief.get('fde_opportunities', [])
        if opportunities:
            for opp in opportunities:
                with st.container():
                    st.markdown(f"### 💼 {opp.get('title', 'Opportunity')}")
                    st.write(opp.get('description', ''))
                    st.write(f"**Client Type:** {opp.get('client_type', 'Various')}")
                    st.write(f"**Your Move:** {opp.get('your_move', 'Evaluate')}")
                    st.success(f"**Potential Value:** {opp.get('potential_value', 'TBD')}")
        else:
            st.info("No specific opportunities identified this cycle.")
    
    with tab5:
        st.subheader("Deep Dive")
        deep_dive = brief.get('deep_dive', {})
        if deep_dive:
            st.markdown(f"## 🔬 {deep_dive.get('topic', 'Deep Dive')}")
            st.write(deep_dive.get('summary', 'Summary coming soon...'))
            st.info(f"**FDE Takeaway:** {deep_dive.get('fde_takeaway', '')}")
            for source in deep_dive.get('sources', []):
                st.link_button("Source", source)
        else:
            st.info("Deep dive content coming soon.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    **Data Sources:** GitHub • Hugging Face • Reddit • API Changelogs  
    **Update Schedule:** Every 2 days at 9am UTC  
    **GitHub:** [feelgood4everai/fde-feed](https://github.com/feelgood4everai/fde-feed)  
    **Built by:** [Anand](https://github.com/feelgood4everai) • Forward Deployed Engineer
    """)

if __name__ == "__main__":
    main()
