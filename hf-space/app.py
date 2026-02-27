import gradio as gr
import requests
import json
from datetime import datetime

# Configuration
GITHUB_RAW_URL = "https://raw.githubusercontent.com/feelgood4everai/fde-feed/main/data/latest.json"
ARCHIVE_URL_TEMPLATE = "https://raw.githubusercontent.com/feelgood4everai/fde-feed/main/data/archive/{}.json"

def load_latest_brief():
    """Load latest brief from GitHub."""
    try:
        resp = requests.get(GITHUB_RAW_URL, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Error loading brief: {e}")
    return None

def format_summary(brief):
    """Format summary section."""
    if not brief:
        return "Error loading brief"
    
    summary = brief.get('summary', {})
    generated = brief.get('generated_at', 'Unknown')[:10]
    next_update = brief.get('metadata', {}).get('next_update', 'Unknown')[:10]
    
    return f"""
## 📊 Brief Summary — {generated}

| Metric | Count |
|--------|-------|
| 🚨 Urgent Alerts | {summary.get('urgent_alerts', 0)} |
| 🔥 Hot Projects | {summary.get('hot_projects', 0)} |
| 📚 Research Papers | {summary.get('research_papers', 0)} |
| 💬 Community Posts | {summary.get('community_discussions', 0)} |
| 💼 Opportunities | {summary.get('fde_opportunities', 0)} |

**Next Update:** {next_update}
"""

def format_urgent_alerts(brief):
    """Format urgent alerts."""
    alerts = brief.get('urgent_alerts', [])
    if not alerts:
        return "✅ No urgent alerts at this time."
    
    lines = []
    for alert in alerts:
        severity = alert.get('severity', 'medium').upper()
        title = alert.get('title', 'Alert')
        impact = alert.get('impact', 'Review required')
        action = alert.get('action', 'Check details')
        url = alert.get('url', '#')
        
        lines.append(f"### 🚨 {severity}: {title}")
        lines.append(f"**Impact:** {impact}")
        lines.append(f"**Action:** {action}")
        if url != '#':
            lines.append(f"**[Details]({url})**")
        lines.append("")
    
    return "\n".join(lines)

def format_github_trending(brief):
    """Format GitHub trending repos."""
    repos = brief.get('hot_this_week', {}).get('github_trending', [])
    if not repos:
        return "No trending repos this cycle."
    
    lines = []
    for repo in repos:
        name = repo.get('name', 'Unknown')
        stars = repo.get('stars', 0)
        desc = repo.get('description', 'No description')
        url = repo.get('url', '#')
        relevance = repo.get('fde_relevance', '')
        use_case = repo.get('fde_use_case', '')
        
        lines.append(f"### ⭐ {name} ({stars:,} stars)")
        lines.append(f"{desc}")
        lines.append(f"**Why FDEs Care:** {relevance}")
        lines.append(f"**Use Case:** {use_case}")
        lines.append(f"**[View on GitHub]({url})**")
        lines.append("")
    
    return "\n".join(lines)

def format_research(brief):
    """Format research papers."""
    papers = brief.get('research_roundup', [])
    if not papers:
        return "No new papers this cycle."
    
    lines = []
    for paper in papers:
        title = paper.get('title', 'Untitled')
        tldr = paper.get('tldr', 'No summary')
        takeaway = paper.get('fde_takeaway', 'Review for applicability')
        url = paper.get('url', '#')
        
        lines.append(f"### 📄 {title}")
        lines.append(f"**TL;DR:** {tldr}")
        lines.append(f"**FDE Takeaway:** {takeaway}")
        if url != '#':
            lines.append(f"**[Read Paper]({url})**")
        lines.append("")
    
    return "\n".join(lines)

def format_community(brief):
    """Format community discussions."""
    reddit = brief.get('community_pulse', {}).get('reddit', [])
    if not reddit:
        return "No significant discussions this cycle."
    
    lines = []
    for post in reddit:
        title = post.get('title', 'Untitled')
        insight = post.get('fde_insight', '')
        url = post.get('url', '#')
        score = post.get('score', 0)
        
        lines.append(f"### 💬 {title}")
        lines.append(f"**Score:** {score} upvotes")
        lines.append(f"**FDE Insight:** {insight}")
        lines.append(f"**[View Discussion]({url})**")
        lines.append("")
    
    return "\n".join(lines)

def format_opportunities(brief):
    """Format FDE opportunities."""
    opportunities = brief.get('fde_opportunities', [])
    if not opportunities:
        return "No specific opportunities identified this cycle."
    
    lines = []
    for opp in opportunities:
        title = opp.get('title', 'Opportunity')
        desc = opp.get('description', '')
        client_type = opp.get('client_type', 'Various')
        move = opp.get('your_move', 'Evaluate')
        value = opp.get('potential_value', 'TBD')
        
        lines.append(f"### 💼 {title}")
        lines.append(f"{desc}")
        lines.append(f"**Client Type:** {client_type}")
        lines.append(f"**Your Move:** {move}")
        lines.append(f"**Potential Value:** {value}")
        lines.append("")
    
    return "\n".join(lines)

def format_deep_dive(brief):
    """Format deep dive section."""
    deep_dive = brief.get('deep_dive', {})
    topic = deep_dive.get('topic', 'Deep Dive')
    summary = deep_dive.get('summary', 'Summary coming soon...')
    takeaway = deep_dive.get('fde_takeaway', 'Review for applicability')
    
    return f"""## 🔬 {topic}

{summary}

**FDE Takeaway:** {takeaway}"""

def create_dashboard():
    """Create Gradio dashboard."""
    
    # Load data
    brief = load_latest_brief()
    
    if not brief:
        return gr.Markdown("# Error\n\nCould not load FDE brief. Please try again later.")
    
    with gr.Blocks(title="FDE-Feed Dashboard", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🚀 FDE-Feed Dashboard")
        gr.Markdown("*Curated intelligence for Forward Deployed Engineers*")
        
        # Summary
        with gr.Tab("📊 Summary"):
            gr.Markdown(format_summary(brief))
            
            with gr.Row():
                refresh_btn = gr.Button("🔄 Refresh Data", variant="primary")
                status_text = gr.Textbox(label="Status", value="Data loaded from GitHub", interactive=False)
            
            def refresh():
                new_brief = load_latest_brief()
                if new_brief:
                    return format_summary(new_brief), "Data refreshed successfully"
                return "Error refreshing data", "Failed to refresh"
            
            refresh_btn.click(refresh, outputs=[gr.Markdown(), status_text])
        
        # Urgent Alerts
        with gr.Tab("🚨 Alerts"):
            gr.Markdown(format_urgent_alerts(brief))
        
        # Hot Projects
        with gr.Tab("🔥 Hot Projects"):
            gr.Markdown(format_github_trending(brief))
        
        # Research
        with gr.Tab("📚 Research"):
            gr.Markdown(format_research(brief))
        
        # Community
        with gr.Tab("💬 Community"):
            gr.Markdown(format_community(brief))
        
        # Opportunities
        with gr.Tab("💼 Opportunities"):
            gr.Markdown(format_opportunities(brief))
        
        # Deep Dive
        with gr.Tab("🔬 Deep Dive"):
            gr.Markdown(format_deep_dive(brief))
        
        # Footer
        gr.Markdown("---")
        gr.Markdown("""
**Data Sources:** GitHub • Hugging Face • Reddit • API Changelogs  
**Update Schedule:** Every 2 days at 9am UTC  
**GitHub:** [feelgood4everai/fde-feed](https://github.com/feelgood4everai/fde-feed)  
**Built by:** [Anand](https://github.com/feelgood4everai) • Forward Deployed Engineer
        """)
    
    return app

# Create and launch
app = create_dashboard()

if __name__ == "__main__":
    app.launch()
