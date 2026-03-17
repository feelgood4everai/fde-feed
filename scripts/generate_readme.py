#!/usr/bin/env python3
"""
Generate human-readable brief from JSON data
"""
import json
from datetime import datetime
from pathlib import Path

def generate_markdown_brief():
    """Generate Markdown brief from latest.json."""
    
    data_file = Path(__file__).parent.parent / "data" / "latest.json"
    output_file = Path(__file__).parent.parent / "data" / "latest.md"
    
    if not data_file.exists():
        print("❌ No latest.json found")
        return
    
    with open(data_file) as f:
        brief = json.load(f)
    
    md = f"""# FDE Brief — {brief.get('generated_at', 'Unknown')[:10]}

> Forward Deployed Intelligence for AI Engineers

---

## 📊 At a Glance

| Metric | Count |
|--------|-------|
| 🚨 Urgent Alerts | {brief.get('summary', {}).get('urgent_alerts', 0)} |
| 🔥 Hot Projects | {brief.get('summary', {}).get('hot_projects', 0)} |
| 📚 Research Papers | {brief.get('summary', {}).get('research_papers', 0)} |
| 💬 Community Posts | {brief.get('summary', {}).get('community_discussions', 0)} |
| 💼 FDE Opportunities | {brief.get('summary', {}).get('fde_opportunities', 0)} |
| 🔧 Framework Updates | {brief.get('summary', {}).get('framework_updates', 0)} |

---

## 🚨 Urgent Alerts

"""
    
    # Add alerts
    alerts = brief.get('urgent_alerts', [])
    if alerts:
        for alert in alerts:
            emoji = "🚨" if alert.get('severity') == 'critical' else "⚠️"
            md += f"""### {emoji} {alert.get('title', 'Unknown')}

- **Source:** {alert.get('source', 'Unknown')}
- **Impact:** {alert.get('impact', 'Unknown')}
- **Action:** {alert.get('action', 'Review')}
- **Link:** {alert.get('url', 'N/A')}

"""
    else:
        md += "✅ No urgent alerts today. All systems nominal.\n\n"
    
    md += "---\n\n## 🔥 Hot Projects\n\n"
    
    # Add hot projects
    projects = brief.get('hot_this_week', {}).get('github_trending', [])
    for project in projects[:5]:
        md += f"""### [{project.get('name', 'Unknown')}]({project.get('url', '#')}) ⭐ {project.get('stars', 0):,}

{project.get('description', 'No description')}

- **Language:** {project.get('language', 'N/A')}
- **FDE Relevance:** {project.get('fde_relevance', 'Unknown')}
- **Use Case:** {project.get('fde_use_case', 'Evaluate')}

"""
    
    md += "---\n\n## 📚 Research Roundup\n\n"
    
    # Add papers
    papers = brief.get('research_roundup', [])
    if papers:
        for paper in papers[:5]:
            md += f"""### {paper.get('title', 'Untitled')}

**Authors:** {', '.join(paper.get('authors', ['Unknown'])[:3])}

{paper.get('tldr', 'No summary available.')}

*FDE Takeaway: {paper.get('fde_takeaway', 'Review for applicability')}*

[Read Paper]({paper.get('url', '#')})

"""
    else:
        md += "No research papers in this edition.\n\n"
    
    md += "---\n\n## 💼 FDE Opportunities\n\n"
    
    # Add opportunities
    opportunities = brief.get('fde_opportunities', [])
    if opportunities:
        for opp in opportunities:
            md += f"""### {opp.get('title', 'Unknown')}

{opp.get('description', '')}

- **Type:** {opp.get('type', 'General')}
- **Client Type:** {opp.get('client_type', 'General')}
- **Your Move:** {opp.get('your_move', 'Evaluate')}
- **Potential Value:** {opp.get('potential_value', 'TBD')}

"""
    else:
        md += "No specific opportunities identified in this edition.\n\n"
    
    md += "---\n\n## 🔍 Deep Dive\n\n"
    
    # Add deep dive
    deep_dive = brief.get('deep_dive', {})
    if deep_dive:
        md += f"""### {deep_dive.get('topic', 'No Topic')}

{deep_dive.get('summary', 'No summary available.')}

**FDE Takeaway:** {deep_dive.get('fde_takeaway', 'Review for applicability')}

"""
    else:
        md += "No deep dive in this edition.\n\n"
    
    md += """---

## 🔧 Framework Updates

"""
    
    # Add framework updates
    updates = brief.get('hot_this_week', {}).get('framework_updates', [])
    if updates:
        for update in updates:
            md += f"- **{update.get('framework', 'Unknown')}** {update.get('version', '')}: {update.get('fde_relevance', 'Review')}\n"
    else:
        md += "No framework updates today.\n"
    
    md += f"""

---

## 📡 Sources

This brief was compiled from:
{chr(10).join(['- ' + source for source in brief.get('metadata', {}).get('sources_checked', [])])}

---

*Generated: {brief.get('generated_at', 'Unknown')} | Next Update: {brief.get('metadata', {}).get('next_update', 'Unknown')[:10]}*

---

<div align="center">

**[GitHub](https://github.com/feelgood4everai/fde-feed) | [Hugging Face](https://huggingface.co/spaces/AnandGeetha/fde-feed)**

*Built for Forward Deployed Engineers*

</div>
"""
    
    # Write output
    with open(output_file, 'w') as f:
        f.write(md)
    
    print(f"✅ Generated: {output_file}")

if __name__ == "__main__":
    generate_markdown_brief()
