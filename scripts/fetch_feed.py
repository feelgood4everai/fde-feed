#!/usr/bin/env python3
"""
FDE-Feed Fetcher
Monitors AI/LLM sources and generates structured brief for Forward Deployed Engineers
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
DATA_DIR = Path("data")
SOURCES_DIR = DATA_DIR / "sources"
ARCHIVE_DIR = DATA_DIR / "archive"
LATEST_FILE = DATA_DIR / "latest.json"

# API Tokens
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")

def ensure_dirs():
    """Ensure all directories exist."""
    for d in [DATA_DIR, SOURCES_DIR, ARCHIVE_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def fetch_github_trending():
    """Fetch trending AI/ML repos from GitHub."""
    print("📊 Fetching GitHub trending...")
    
    repos = []
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    
    # Search for trending AI/LLM repos (last 7 days)
    one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    queries = [
        "LLM language:python created:>" + one_week_ago,
        "RAG language:python created:>" + one_week_ago,
        "AI-agent language:python created:>" + one_week_ago,
        "MLOps language:python created:>" + one_week_ago,
    ]
    
    for query in queries[:2]:  # Limit API calls
        url = f"https://api.github.com/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 5
        }
        
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("items", []):
                    repos.append({
                        "name": item["full_name"],
                        "url": item["html_url"],
                        "stars": item["stargazers_count"],
                        "stars_gained": item["stargazers_count"],  # Approximation
                        "description": item["description"] or "No description",
                        "language": item["language"],
                        "created_at": item["created_at"],
                        "fde_relevance": analyze_fde_relevance(item["description"]),
                        "fde_use_case": generate_use_case(item["description"])
                    })
        except Exception as e:
            print(f"  ⚠️  Error fetching GitHub: {e}")
    
    # Deduplicate by name
    seen = set()
    unique = []
    for r in repos:
        if r["name"] not in seen:
            seen.add(r["name"])
            unique.append(r)
    
    return sorted(unique, key=lambda x: x["stars"], reverse=True)[:10]

def fetch_hf_papers():
    """Fetch recent papers from Hugging Face."""
    print("📚 Fetching Hugging Face papers...")
    
    papers = []
    url = "https://huggingface.co/api/daily_papers"
    
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            for p in data.get("papers", [])[:5]:
                papers.append({
                    "title": p.get("title", ""),
                    "authors": p.get("authors", []),
                    "url": f"https://arxiv.org/abs/{p.get('paper', {}).get('id', '')}",
                    "tldr": p.get("summary", "")[:200] + "..." if len(p.get("summary", "")) > 200 else p.get("summary", ""),
                    "fde_takeaway": extract_fde_takeaway(p.get("summary", "")),
                    "published_at": p.get("publishedAt", "")
                })
    except Exception as e:
        print(f"  ⚠️  Error fetching HF papers: {e}")
    
    return papers

def fetch_reddit_ml():
    """Fetch hot posts from r/MachineLearning."""
    print("💬 Fetching Reddit discussions...")
    
    posts = []
    url = "https://www.reddit.com/r/MachineLearning/hot.json"
    headers = {"User-Agent": "FDE-Feed/1.0"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            for post in data.get("data", {}).get("children", [])[:10]:
                p = post.get("data", {})
                # Filter for discussion posts (not just links)
                if p.get("selftext") and len(p.get("selftext", "")) > 100:
                    posts.append({
                        "subreddit": "MachineLearning",
                        "title": p.get("title", ""),
                        "url": f"https://reddit.com{p.get('permalink', '')}",
                        "score": p.get("score", 0),
                        "fde_insight": analyze_reddit_post(p.get("title", ""), p.get("selftext", "")[:500])
                    })
    except Exception as e:
        print(f"  ⚠️  Error fetching Reddit: {e}")
    
    return posts[:5]

def check_api_changelogs():
    """Check for API changelogs (OpenAI, Anthropic)."""
    print("🔔 Checking API changelogs...")
    
    alerts = []
    
    # OpenAI changelog (RSS)
    try:
        url = "https://openai.com/blog/rss.xml"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            # Simple check for deprecation keywords
            if "deprecat" in resp.text.lower() or "breaking" in resp.text.lower():
                alerts.append({
                    "severity": "high",
                    "title": "OpenAI API changes detected",
                    "source": "OpenAI Changelog",
                    "impact": "Client systems may need updates",
                    "action": "Review changelog and notify affected clients",
                    "url": "https://platform.openai.com/docs/changelog",
                    "detected_at": datetime.now().isoformat()
                })
    except Exception as e:
        print(f"  ⚠️  Error checking OpenAI: {e}")
    
    return alerts

def analyze_fde_relevance(description):
    """Analyze why this repo matters to FDEs."""
    if not description:
        return "General AI tooling"
    
    desc_lower = description.lower()
    
    if any(k in desc_lower for k in ["debug", "monitor", "observ", "trace"]):
        return "Debugging/Observability tool — helps diagnose client issues"
    elif any(k in desc_lower for k in ["cost", "price", "budget", "optim"]):
        return "Cost optimization — potential client value-add"
    elif any(k in desc_lower for k in ["rag", "retriev", "vector", "embed"]):
        return "RAG infrastructure — core to many client projects"
    elif any(k in desc_lower for k in ["agent", "autonomous", "workflow"]):
        return "AI agent tooling — emerging client need"
    elif any(k in desc_lower for k in ["eval", "benchmark", "metric"]):
        return "Evaluation framework — helps prove client ROI"
    else:
        return "Emerging tool — monitor for client relevance"

def generate_use_case(description):
    """Generate FDE use case from description."""
    if not description:
        return "Evaluate for client projects"
    
    desc_lower = description.lower()
    
    if "debug" in desc_lower:
        return "Demo to clients struggling with production issues"
    elif "cost" in desc_lower:
        return "Propose cost optimization engagement"
    elif "rag" in desc_lower:
        return "Architecture review for RAG-heavy clients"
    elif "agent" in desc_lower:
        return "Pilot program for multi-agent client needs"
    else:
        return "Share as thought leadership, gauge client interest"

def extract_fde_takeaway(summary):
    """Extract practical takeaway for FDEs from paper summary."""
    if not summary:
        return "Review for client applicability"
    
    # Simple keyword-based extraction
    summary_lower = summary.lower()
    
    if "production" in summary_lower or "deploy" in summary_lower:
        return "Production deployment insights — share with DevOps-minded clients"
    elif "efficient" in summary_lower or "speed" in summary_lower or "latency" in summary_lower:
        return "Performance optimization angle — relevant for scaling clients"
    elif "cost" in summary_lower or "cheap" in summary_lower:
        return "Cost reduction opportunity — propose optimization project"
    elif "eval" in summary_lower or "benchmark" in summary_lower:
        return "New evaluation method — improve client success metrics"
    else:
        return "Technical advance — monitor for production readiness"

def analyze_reddit_post(title, text):
    """Analyze Reddit post for FDE insights."""
    combined = (title + " " + text).lower()
    
    if any(k in combined for k in ["failed", "broke", "issue", "problem", "bug"]):
        return "Production failure pattern — alert clients using similar stacks"
    elif any(k in combined for k in ["migrated", "switched", "moved from"]):
        return "Technology shift detected — evaluate impact on client roadmap"
    elif any(k in combined for k in ["cost", "expensive", "bill", "pricing"]):
        return "Cost concern trending — propose optimization to similar clients"
    elif any(k in combined for k in ["production", "deploy", "scale"]):
        return "Real-world deployment insight — incorporate into client advice"
    else:
        return "Community sentiment check — note for client conversations"

def generate_fde_opportunities(github_repos, papers, reddit_posts):
    """Generate actionable opportunities for FDEs."""
    opportunities = []
    
    # Opportunity from trending repos
    for repo in github_repos[:3]:
        if "cost" in repo.get("fde_relevance", "").lower():
            opportunities.append({
                "type": "project_idea",
                "title": f"Cost Optimization: {repo['name']}",
                "description": f"New tool '{repo['name']}' for cost optimization is trending",
                "client_type": "Clients with high LLM bills",
                "your_move": f"Demo {repo['name']} and propose optimization engagement",
                "potential_value": "£5K-£15K"
            })
    
    # Opportunity from papers
    for paper in papers[:2]:
        if "production" in paper.get("fde_takeaway", "").lower():
            opportunities.append({
                "type": "client_conversation",
                "title": f"New Research: {paper['title'][:50]}...",
                "description": "Production-focused research paper published",
                "client_type": "CTOs and technical leaders",
                "your_move": "Share paper with insights on production readiness",
                "potential_value": "£2K-£5K (advisory)"
            })
    
    # Opportunity from Reddit
    for post in reddit_posts[:2]:
        if "production" in post.get("fde_insight", "").lower():
            opportunities.append({
                "type": "optimization",
                "title": "Production Issue Pattern Detected",
                "description": f"Reddit discussion: {post['title'][:60]}...",
                "client_type": "Clients with similar architecture",
                "your_move": "Proactive architecture review",
                "potential_value": "£3K-£8K"
            })
    
    return opportunities

def generate_deep_dive(github_repos, papers):
    """Generate deep dive section."""
    # Pick the most starred repo or most relevant paper
    if github_repos:
        top_repo = github_repos[0]
        return {
            "topic": f"Understanding {top_repo['name']}",
            "summary": f"{top_repo['name']} is a {top_repo['description']}. It has gained {top_repo['stars']} stars and represents a significant trend in {top_repo.get('language', 'AI')} tooling for production systems.",
            "fde_takeaway": f"Consider demoing {top_repo['name']} to clients interested in {top_repo.get('fde_relevance', 'AI tooling').lower()}. Early adoption of trending tools positions you as forward-thinking.",
            "sources": [top_repo['url']]
        }
    elif papers:
        top_paper = papers[0]
        return {
            "topic": top_paper['title'],
            "summary": top_paper.get('tldr', 'Research paper summary'),
            "fde_takeaway": top_paper.get('fde_takeaway', 'Review for client applicability'),
            "sources": [top_paper['url']]
        }
    else:
        return {
            "topic": "FDE Best Practices",
            "summary": "Focus on building reusable patterns from client engagements.",
            "fde_takeaway": "Document everything. Today's client solution is tomorrow's framework.",
            "sources": []
        }

def build_brief():
    """Build the complete FDE brief."""
    print("\n🔨 Building FDE Brief...")
    
    # Fetch all sources
    github_repos = fetch_github_trending()
    hf_papers = fetch_hf_papers()
    reddit_posts = fetch_reddit_ml()
    urgent_alerts = check_api_changelogs()
    
    # Generate insights
    opportunities = generate_fde_opportunities(github_repos, hf_papers, reddit_posts)
    deep_dive = generate_deep_dive(github_repos, hf_papers)
    
    # Build brief structure
    brief = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "edition": f"fde-brief-{datetime.now().strftime('%Y%m%d')}",
        "summary": {
            "urgent_alerts": len(urgent_alerts),
            "hot_projects": len(github_repos),
            "research_papers": len(hf_papers),
            "community_discussions": len(reddit_posts),
            "fde_opportunities": len(opportunities)
        },
        "urgent_alerts": urgent_alerts,
        "hot_this_week": {
            "github_trending": github_repos,
            "hf_papers": hf_papers,
            "framework_updates": []  # Placeholder
        },
        "research_roundup": hf_papers,
        "community_pulse": {
            "reddit": reddit_posts,
            "linkedin": []
        },
        "fde_opportunities": opportunities,
        "deep_dive": deep_dive,
        "metadata": {
            "sources_checked": ["GitHub", "Hugging Face Papers", "Reddit", "API Changelogs"],
            "fetch_duration_seconds": 0,
            "next_update": (datetime.now() + timedelta(days=2)).replace(hour=9, minute=0).isoformat()
        }
    }
    
    return brief

def save_brief(brief):
    """Save brief to files."""
    # Save as latest
    with open(LATEST_FILE, 'w') as f:
        json.dump(brief, f, indent=2)
    print(f"  ✅ Saved: {LATEST_FILE}")
    
    # Archive copy
    archive_name = f"{datetime.now().strftime('%Y-%m-%d')}.json"
    archive_path = ARCHIVE_DIR / archive_name
    with open(archive_path, 'w') as f:
        json.dump(brief, f, indent=2)
    print(f"  ✅ Archived: {archive_path}")
    
    # Save raw sources
    sources_meta = {
        "github": brief["hot_this_week"]["github_trending"],
        "papers": brief["hot_this_week"]["hf_papers"],
        "reddit": brief["community_pulse"]["reddit"]
    }
    for source_name, data in sources_meta.items():
        source_file = SOURCES_DIR / f"{source_name}-{datetime.now().strftime('%Y%m%d')}.json"
        with open(source_file, 'w') as f:
            json.dump(data, f, indent=2)

def main():
    """Main entry point."""
    print("="*60)
    print("🚀 FDE-Feed Fetcher")
    print("="*60)
    
    ensure_dirs()
    
    start_time = datetime.now()
    brief = build_brief()
    duration = (datetime.now() - start_time).total_seconds()
    brief["metadata"]["fetch_duration_seconds"] = round(duration, 2)
    
    save_brief(brief)
    
    print("\n" + "="*60)
    print("✅ FDE Brief Generated!")
    print("="*60)
    print(f"\n📊 Summary:")
    print(f"  Urgent Alerts: {brief['summary']['urgent_alerts']}")
    print(f"  Hot Projects: {brief['summary']['hot_projects']}")
    print(f"  Research Papers: {brief['summary']['research_papers']}")
    print(f"  Community Posts: {brief['summary']['community_discussions']}")
    print(f"  FDE Opportunities: {brief['summary']['fde_opportunities']}")
    print(f"\n⏱️  Duration: {duration:.1f}s")
    print(f"📅 Next Update: {brief['metadata']['next_update'][:10]}")

if __name__ == "__main__":
    main()
