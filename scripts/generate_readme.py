#!/usr/bin/env python3
"""
Generate human-readable README from latest.json
"""

import json
from datetime import datetime
from pathlib import Path

def load_brief():
    """Load the latest brief."""
    with open("data/latest.json") as f:
        return json.load(f)

def format_date(iso_string):
    """Format ISO date to readable."""
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.strftime("%B %d, %Y")
    except:
        return iso_string[:10]

def generate_urgent_section(brief):
    """Generate urgent alerts section."""
    alerts = brief.get("urgent_alerts", [])
    if not alerts:
        return "_No urgent alerts at this time._"
    
    lines = ["| Severity | Alert | Impact | Action |", "|----------|-------|--------|--------|"]
    for alert in alerts:
        severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(alert.get("severity"), "⚪")
        lines.append(f"| {severity_emoji} {alert['severity'].upper()} | [{alert['title'][:40]}...]({alert.get('url', '#')}) | {alert.get('impact', 'N/A')[:30]}... | {alert.get('action', 'Review')[:30]}... |")
    
    return "\n".join(lines)

def generate_github_section(brief):
    """Generate GitHub trending section."""
    repos = brief.get("hot_this_week", {}).get("github_trending", [])
    if not repos:
        return "_No trending repos this cycle._"
    
    lines = ["| Project | Stars | Why It Matters | FDE Angle |", "|---------|-------|----------------|-----------|"]
    for repo in repos[:5]:
        name = repo['name'].split('/')[-1][:20]
        stars = f"⭐ {repo['stars']:,}"
        relevance = repo.get('fde_relevance', '')[:35] + "..." if len(repo.get('fde_relevance', '')) > 35 else repo.get('fde_relevance', '')
        use_case = repo.get('fde_use_case', '')[:30] + "..." if len(repo.get('fde_use_case', '')) > 30 else repo.get('fde_use_case', '')
        lines.append(f"| [{name}]({repo['url']}) | {stars} | {relevance} | {use_case} |")
    
    return "\n".join(lines)

def generate_research_section(brief):
    """Generate research roundup section."""
    papers = brief.get("research_roundup", [])
    if not papers:
        return "_No new papers this cycle._"
    
    lines = []
    for paper in papers[:3]:
        title = paper.get('title', 'Untitled')[:60]
        tldr = paper.get('tldr', 'No summary available')[:150]
        takeaway = paper.get('fde_takeaway', 'Review for applicability')
        lines.append(f"### {title}")
        lines.append(f"**TL;DR:** {tldr}")
        lines.append(f"**FDE Takeaway:** {takeaway}")
        if paper.get('url'):
            lines.append(f"**[Read Paper]({paper['url']})**")
        lines.append("")
    
    return "\n".join(lines)

def generate_community_section(brief):
    """Generate community pulse section."""
    reddit = brief.get("community_pulse", {}).get("reddit", [])
    if not reddit:
        return "_No significant discussions this cycle._"
    
    lines = []
    for post in reddit[:3]:
        title = post.get('title', '')[:70]
        insight = post.get('fde_insight', '')
        lines.append(f"**[{title}]({post.get('url', '#')})** — {insight}")
        lines.append("")
    
    return "\n".join(lines)

def generate_opportunities_section(brief):
    """Generate FDE opportunities section."""
    opportunities = brief.get("fde_opportunities", [])
    if not opportunities:
        return "_No specific opportunities identified this cycle._"
    
    lines = ["| Opportunity | Client Type | Your Move | Potential Value |", "|-------------|-------------|-----------|-----------------|"]
    for opp in opportunities[:5]:
        title = opp.get('title', '')[:35] + "..." if len(opp.get('title', '')) > 35 else opp.get('title', '')
        client = opp.get('client_type', 'Various')[:25]
        move = opp.get('your_move', 'Evaluate')[:30] + "..." if len(opp.get('your_move', '')) > 30 else opp.get('your_move', '')
        value = opp.get('potential_value', 'TBD')
        lines.append(f"| {title} | {client} | {move} | {value} |")
    
    return "\n".join(lines)

def generate_deep_dive_section(brief):
    """Generate deep dive section."""
    deep_dive = brief.get("deep_dive", {})
    topic = deep_dive.get('topic', 'Deep Dive Topic')
    summary = deep_dive.get('summary', 'Summary coming soon...')
    takeaway = deep_dive.get('fde_takeaway', 'Review for applicability')
    sources = deep_dive.get('sources', [])
    
    sources_md = " • ".join([f"[Source]({s})" for s in sources[:3]]) if sources else ""
    
    return f"""## 🔬 Deep Dive: {topic}

{summary}

**FDE Takeaway:** {takeaway}

{sources_md}"""

def generate_readme(brief):
    """Generate complete README."""
    generated_at = format_date(brief.get('generated_at', datetime.now().isoformat()))
    next_update = format_date(brief.get('metadata', {}).get('next_update', ''))
    
    readme = f"""# FDE Brief — {generated_at}

> Curated intelligence for Forward Deployed Engineers

[![GitHub](https://img.shields.io/badge/GitHub-Repo-blue?logo=github)](https://github.com/feelgood4everai/fde-feed)
[![Hugging Face](https://img.shields.io/badge/🤗-Dashboard-yellow)](https://huggingface.co/spaces/AnandGeetha/fde-feed)

---

## 📊 At a Glance

| Metric | Count |
|--------|-------|
| 🚨 Urgent Alerts | {brief['summary']['urgent_alerts']} |
| 🔥 Hot Projects | {brief['summary']['hot_projects']} |
| 📚 Research Papers | {brief['summary']['research_papers']} |
| 💬 Community Discussions | {brief['summary']['community_discussions']} |
| 💼 FDE Opportunities | {brief['summary']['fde_opportunities']} |

**Next Update:** {next_update}

---

## 🚨 Urgent Alerts

<!-- URGENT -->
{generate_urgent_section(brief)}
<!-- END_URGENT -->

---

## 🔥 Hot This Week

### GitHub Trending: AI/ML Projects

{generate_github_section(brief)}

---

## 📚 Research Roundup

{generate_research_section(brief)}

---

## 💬 Community Pulse

**What's Breaking on Reddit:**

{generate_community_section(brief)}

---

## 💼 FDE Opportunities This Week

{generate_opportunities_section(brief)}

---

{generate_deep_dive_section(brief)}

---

## 🛠️ How to Use This Brief

### For Client Conversations
1. Scan **Urgent Alerts** — anything your clients need to know NOW
2. Check **FDE Opportunities** — conversation starters for outreach
3. Review **Deep Dive** — impress clients with forward knowledge

### For Proactive Outreach
- **Hot Projects** = demo opportunities
- **Research Roundup** = thought leadership content
- **Community Pulse** = real-world validation

### For Your Own Development
- Stay current without 5+ hours of reading
- Identify patterns across client engagements
- Build reusable frameworks from trends

---

## 🔄 Automation

This brief is auto-generated every 2 days by:
- **GitHub Actions** at 9am UTC
- **Sources:** GitHub, Hugging Face, Reddit, API changelogs
- **Code:** [scripts/fetch_feed.py](scripts/fetch_feed.py)

[View Full Archive →](data/archive/)

---

## 💼 Enterprise Support

Need help deploying AI systems in production?

- **Availability**: Q2 2026
- **Contact**: [LinkedIn](https://linkedin.com/in/anandbg)

---

*Built by [Anand](https://github.com/feelgood4everai) • Forward Deployed Engineer • 26 years delivering production systems*

*Generated: {brief.get('generated_at', 'Unknown')[:19]}*
"""
    
    return readme

def main():
    """Main entry point."""
    print("📝 Generating README...")
    
    brief = load_brief()
    readme = generate_readme(brief)
    
    with open("README.md", "w") as f:
        f.write(readme)
    
    print("  ✅ README.md updated")

if __name__ == "__main__":
    main()
