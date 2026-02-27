#!/usr/bin/env python3
"""
FDE-Feed Fetcher v2
Monitors AI/LLM sources and generates structured brief for Forward Deployed Engineers
"""

import os
import sys
import json
import requests
import xml.etree.ElementTree as ET
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

# Microsoft 365 Roadmap RSS
MS_ROADMAP_URL = "https://www.microsoft.com/en-us/microsoft-365/roadmap?rtc=1&filters=Microsoft%20Copilot"

def ensure_dirs():
    """Ensure all directories exist."""
    for d in [DATA_DIR, SOURCES_DIR, ARCHIVE_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def fetch_github_trending():
    """Fetch trending AI/ML repos from GitHub."""
    print("📊 Fetching GitHub trending...")
    
    repos = []
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    
    # Search for trending AI/LLM repos (last 14 days for broader catch)
    two_weeks_ago = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    
    queries = [
        "LLM created:>" + two_weeks_ago,
        "RAG created:>" + two_weeks_ago,
        "AI agent created:>" + two_weeks_ago,
        "MLOps created:>" + two_weeks_ago,
        "LangChain created:>" + two_weeks_ago,
    ]
    
    for query in queries[:3]:
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
                        "stars_gained": item["stargazers_count"],
                        "description": item["description"] or "No description",
                        "language": item["language"],
                        "created_at": item["created_at"],
                        "fde_relevance": analyze_fde_relevance(item["description"]),
                        "fde_use_case": generate_use_case(item["description"])
                    })
        except Exception as e:
            print(f"  ⚠️  Error fetching GitHub: {e}")
    
    # Deduplicate and sort
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
            # HF API returns a list of papers directly
            if isinstance(data, list):
                paper_list = data[:5]
            else:
                paper_list = data.get("papers", [])[:5]
            
            for p in paper_list:
                if isinstance(p, dict):
                    paper_id = ""
                    if isinstance(p.get("paper"), dict):
                        paper_id = p["paper"].get("id", "")
                    
                    papers.append({
                        "title": p.get("title", "Untitled"),
                        "authors": p.get("authors", []),
                        "url": f"https://arxiv.org/abs/{paper_id}" if paper_id else "",
                        "tldr": (p.get("summary", "")[:200] + "...") if len(p.get("summary", "")) > 200 else p.get("summary", ""),
                        "fde_takeaway": extract_fde_takeaway(p.get("summary", "")),
                        "published_at": p.get("publishedAt", "")
                    })
    except Exception as e:
        print(f"  ⚠️  Error fetching HF papers: {e}")
    
    return papers

def fetch_arxiv_papers():
    """Fetch recent AI/ML papers from arXiv."""
    print("📖 Fetching arXiv papers...")
    
    papers = []
    queries = ["RAG", "LLM deployment"]
    
    for query in queries[:1]:  # Limit to avoid rate limits
        url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=3&sortBy=submittedDate&sortOrder=descending"
        
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                # Parse Atom feed
                root = ET.fromstring(resp.content)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                for entry in root.findall('atom:entry', ns)[:3]:
                    title = entry.find('atom:title', ns)
                    summary = entry.find('atom:summary', ns)
                    link = entry.find('atom:id', ns)
                    published = entry.find('atom:published', ns)
                    
                    # Get authors
                    authors = []
                    for author in entry.findall('atom:author', ns)[:3]:
                        name = author.find('atom:name', ns)
                        if name is not None:
                            authors.append(name.text)
                    
                    if title is not None:
                        papers.append({
                            "title": title.text.replace("\n", " ").strip() if title.text else "Untitled",
                            "authors": authors,
                            "url": link.text if link is not None else "",
                            "tldr": (summary.text[:200] + "...") if summary is not None and len(summary.text) > 200 else (summary.text if summary is not None else ""),
                            "fde_takeaway": extract_fde_takeaway(summary.text if summary is not None else ""),
                            "published_at": published.text if published is not None else ""
                        })
        except Exception as e:
            print(f"  ⚠️  Error fetching arXiv: {e}")
    
    return papers[:5]

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
            for post in data.get("data", {}).get("children", [])[:15]:
                p = post.get("data", {})
                # Filter for discussion posts
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

def fetch_framework_updates():
    """Check for LangChain, LlamaIndex updates."""
    print("🔧 Fetching framework updates...")
    
    updates = []
    
    # LangChain releases
    try:
        url = "https://api.github.com/repos/langchain-ai/langchain/releases/latest"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            published = data.get("published_at", "")[:10]
            # Only include if published in last 7 days
            if published >= (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"):
                updates.append({
                    "framework": "LangChain",
                    "version": data.get("tag_name", ""),
                    "url": data.get("html_url", ""),
                    "published": published,
                    "fde_relevance": "Check for breaking changes affecting client implementations"
                })
    except Exception as e:
        print(f"  ⚠️  Error fetching LangChain: {e}")
    
    # LlamaIndex releases
    try:
        url = "https://api.github.com/repos/run-llama/llama_index/releases/latest"
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            published = data.get("published_at", "")[:10]
            if published >= (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"):
                updates.append({
                    "framework": "LlamaIndex",
                    "version": data.get("tag_name", ""),
                    "url": data.get("html_url", ""),
                    "published": published,
                    "fde_relevance": "Review for RAG pipeline improvements"
                })
    except Exception as e:
        print(f"  ⚠️  Error fetching LlamaIndex: {e}")
    
    return updates

def fetch_microsoft_copilot_updates():
    """Fetch Microsoft Copilot updates."""
    print("🖥️  Fetching Microsoft Copilot updates...")
    
    updates = []
    
    # Microsoft 365 Roadmap RSS for Copilot features
    try:
        # Note: Microsoft doesn't have a simple RSS, so we check their blog
        url = "https://techcommunity.microsoft.com/t5/copilot-for-microsoft-365/bg-p/CopilotforMicrosoft365"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            # Look for recent Copilot announcements
            if "new feature" in resp.text.lower() or "announcing" in resp.text.lower():
                updates.append({
                    "product": "Microsoft Copilot",
                    "update": "Check Tech Community for latest announcements",
                    "url": "https://techcommunity.microsoft.com/t5/copilot-for-microsoft-365/bg-p/CopilotforMicrosoft365",
                    "fde_relevance": "Critical for enterprise Copilot implementations"
                })
    except Exception as e:
        print(f"  ⚠️  Error fetching Microsoft updates: {e}")
    
    return updates

def fetch_linkedin_insights():
    """Fetch trending LinkedIn topics for FDEs."""
    print("💼 Fetching LinkedIn insights...")
    
    # Since we can't easily scrape LinkedIn without auth, we'll use proxy indicators
    insights = []
    
    # Check GitHub discussions for hiring trends
    try:
        url = "https://api.github.com/search/issues"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        params = {
            "q": "forward deployed engineer hiring is:open",
            "sort": "updated",
            "per_page": 5
        }
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("total_count", 0) > 0:
                insights.append({
                    "topic": "FDE Hiring Trends",
                    "trend": f"{data['total_count']} open discussions about FDE hiring",
                    "fde_relevance": "Market validation for FDE positioning",
                    "source": "GitHub Discussions"
                })
    except Exception as e:
        print(f"  ⚠️  Error fetching LinkedIn insights: {e}")
    
    return insights

def check_api_changelogs():
    """Check for API changelogs (OpenAI, Anthropic, etc.)."""
    print("🔔 Checking API changelogs...")
    
    alerts = []
    
    # OpenAI changelog check
    try:
        url = "https://openai.com/blog/rss.xml"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            ns = {'content': 'http://purl.org/rss/1.0/modules/content/'}
            
            for item in root.findall('.//item')[:3]:
                title_elem = item.find('title')
                link_elem = item.find('link')
                
                title = title_elem.text.lower() if title_elem is not None and title_elem.text else ""
                link = link_elem.text if link_elem is not None else "https://openai.com/blog"
                
                if any(k in title for k in ["deprecat", "breaking", "sunset", "end of life"]):
                    alerts.append({
                        "severity": "critical",
                        "title": f"OpenAI: {title_elem.text}",
                        "source": "OpenAI Blog",
                        "impact": "Client integrations may break",
                        "action": "Review and notify affected clients immediately",
                        "url": link,
                        "detected_at": datetime.now().isoformat()
                    })
                elif any(k in title for k in ["new", "launch", "introducing", "announcing"]):
                    alerts.append({
                        "severity": "medium",
                        "title": f"OpenAI: {title_elem.text}",
                        "source": "OpenAI Blog",
                        "impact": "New capabilities for client solutions",
                        "action": "Evaluate for client opportunities",
                        "url": link,
                        "detected_at": datetime.now().isoformat()
                    })
    except Exception as e:
        print(f"  ⚠️  Error checking OpenAI: {e}")
    
    # Anthropic changelog
    try:
        url = "https://www.anthropic.com/news/rss.xml"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            
            for item in root.findall('.//item')[:2]:
                title_elem = item.find('title')
                link_elem = item.find('link')
                
                title = title_elem.text.lower() if title_elem is not None and title_elem.text else ""
                link = link_elem.text if link_elem is not None else "https://anthropic.com/news"
                
                if any(k in title for k in ["claude", "api", "model"]):
                    alerts.append({
                        "severity": "medium",
                        "title": f"Anthropic: {title_elem.text}",
                        "source": "Anthropic News",
                        "impact": "Claude API changes may affect clients",
                        "action": "Review for client impact",
                        "url": link,
                        "detected_at": datetime.now().isoformat()
                    })
    except Exception as e:
        print(f"  ⚠️  Error checking Anthropic: {e}")
    
    return alerts[:5]  # Limit alerts

def analyze_fde_relevance(description):
    """Analyze why this repo matters to FDEs."""
    if not description:
        return "General AI tooling"
    
    desc_lower = description.lower()
    
    if any(k in desc_lower for k in ["debug", "monitor", "observ", "trace", "log"]):
        return "Debugging/Observability — essential for production client systems"
    elif any(k in desc_lower for k in ["cost", "price", "budget", "optim", "efficien"]):
        return "Cost optimization — high-value client conversation starter"
    elif any(k in desc_lower for k in ["rag", "retriev", "vector", "embed", "search"]):
        return "RAG infrastructure — core to enterprise knowledge systems"
    elif any(k in desc_lower for k in ["agent", "autonomous", "workflow", "chain"]):
        return "AI agent tooling — fastest growing client need"
    elif any(k in desc_lower for k in ["eval", "benchmark", "metric", "test"]):
        return "Evaluation framework — prove ROI to client stakeholders"
    elif any(k in desc_lower for k in ["deploy", "production", "scale", "infra"]):
        return "Deployment tooling — bridge dev-to-prod gap for clients"
    else:
        return "Emerging tool — monitor for client relevance"

def generate_use_case(description):
    """Generate FDE use case from description."""
    if not description:
        return "Evaluate for client projects"
    
    desc_lower = description.lower()
    
    if "debug" in desc_lower or "monitor" in desc_lower:
        return "Demo to clients with production issues → support contract"
    elif "cost" in desc_lower or "optim" in desc_lower:
        return "Propose cost audit → £5K-£15K optimization project"
    elif "rag" in desc_lower or "retriev" in desc_lower:
        return "Architecture review for RAG-heavy clients"
    elif "agent" in desc_lower:
        return "Pilot program for clients exploring multi-agent systems"
    elif "eval" in desc_lower:
        return "ROI measurement setup for stakeholder reporting"
    elif "deploy" in desc_lower:
        return "Dev-to-prod acceleration for client launches"
    else:
        return "Thought leadership share → gauge client interest"

def extract_fde_takeaway(summary):
    """Extract practical takeaway for FDEs from paper summary."""
    if not summary:
        return "Review for client applicability"
    
    summary_lower = summary.lower()
    
    if "production" in summary_lower or "deploy" in summary_lower:
        return "Production deployment insights — share with DevOps-minded clients"
    elif "efficient" in summary_lower or "speed" in summary_lower or "latency" in summary_lower:
        return "Performance optimization angle — relevant for scaling clients"
    elif "cost" in summary_lower or "cheap" in summary_lower or "reduc" in summary_lower:
        return "Cost reduction opportunity — propose optimization project"
    elif "eval" in summary_lower or "benchmark" in summary_lower or "metric" in summary_lower:
        return "New evaluation method — improve client success metrics"
    elif "rag" in summary_lower:
        return "RAG advancement — audit client retrieval strategies"
    elif "agent" in summary_lower:
        return "Agent system insight — position as agent specialist"
    else:
        return "Technical advance — monitor for production readiness"

def analyze_reddit_post(title, text):
    """Analyze Reddit post for FDE insights."""
    combined = (title + " " + text).lower()
    
    if any(k in combined for k in ["failed", "broke", "issue", "problem", "bug", "error", "crash"]):
        return "⚠️ Production failure pattern — alert clients using similar stacks"
    elif any(k in combined for k in ["migrated", "switched", "moved from", "replaced"]):
        return "🔄 Technology shift detected — evaluate impact on client roadmap"
    elif any(k in combined for k in ["cost", "expensive", "bill", "pricing", "budget"]):
        return "💰 Cost concern trending — propose optimization to similar clients"
    elif any(k in combined for k in ["production", "deploy", "scale", "enterprise"]):
        return "🏭 Real-world deployment insight — incorporate into client advice"
    elif any(k in combined for k in ["hiring", "job", "career", "interview"]):
        return "💼 Market trend — FDE skills in demand, strengthen positioning"
    elif any(k in combined for k in ["gpt-4", "claude", "llama", "model comparison"]):
        return "🤖 Model selection insight — inform client model decisions"
    else:
        return "💭 Community sentiment check — note for client conversations"

def generate_fde_opportunities(github_repos, papers, reddit_posts, framework_updates):
    """Generate actionable opportunities for FDEs."""
    opportunities = []
    
    # From trending repos
    for repo in github_repos[:3]:
        rel_lower = repo.get("fde_relevance", "").lower()
        if "cost" in rel_lower:
            opportunities.append({
                "type": "project_idea",
                "title": f"Cost Optimization: {repo['name'].split('/')[-1]}",
                "description": f"New tool '{repo['name']}' trending for cost optimization. Clients likely overspending on LLM infrastructure.",
                "client_type": "Clients with £2K+/month LLM spend",
                "your_move": f"Demo {repo['name']} and propose cost audit",
                "potential_value": "£5K-£15K project"
            })
        elif "debug" in rel_lower or "monitor" in rel_lower:
            opportunities.append({
                "type": "client_conversation",
                "title": f"Observability Opportunity: {repo['name'].split('/')[-1]}",
                "description": f"Trending debugging tool for AI systems. Many clients lack production visibility.",
                "client_type": "Clients with production AI systems",
                "your_move": "Offer health check → ongoing support retainer",
                "potential_value": "£3K-£8K initial + £2K/month retainer"
            })
    
    # From papers
    for paper in papers[:2]:
        takeaway = paper.get("fde_takeaway", "").lower()
        if "production" in takeaway or "deploy" in takeaway:
            opportunities.append({
                "type": "thought_leadership",
                "title": f"Research Spotlight: {paper['title'][:40]}...",
                "description": "New production-focused research published. Early insight = credibility.",
                "client_type": "CTOs and technical decision makers",
                "your_move": "Share on LinkedIn + DM to 3 target prospects",
                "potential_value": "Inbound inquiry or advisory call"
            })
    
    # From Reddit
    for post in reddit_posts[:2]:
        if "cost" in post.get("fde_insight", "").lower():
            opportunities.append({
                "type": "optimization",
                "title": "Cost Optimization Wave",
                "description": f"Reddit discussion: {post['title'][:50]}...",
                "client_type": "All clients with significant AI spend",
                "your_move": "Proactive outreach with cost-saving framework",
                "potential_value": "£5K-£10K per client"
            })
    
    # From framework updates
    for update in framework_updates[:1]:
        opportunities.append({
            "type": "technical_review",
            "title": f"{update['framework']} Update: {update['version']}",
            "description": f"New version may have breaking changes or improvements",
            "client_type": f"Clients using {update['framework']}",
            "your_move": "Proactive compatibility check → upgrade assistance",
            "potential_value": "£2K-£5K per client"
        })
    
    return opportunities

def generate_deep_dive(github_repos, papers, framework_updates):
    """Generate deep dive section."""
    # Prioritize: trending repo > framework update > paper
    if github_repos and github_repos[0].get("stars", 0) > 1000:
        top_repo = github_repos[0]
        return {
            "topic": f"Deep Dive: {top_repo['name']}",
            "summary": f"{top_repo['name']} is gaining traction with {top_repo['stars']:,} stars. {top_repo['description']}. This represents a significant trend in {top_repo.get('language', 'AI')} tooling for production systems. FDEs should understand whether this is a flash-in-the-pan or a genuine shift in how teams build AI systems.",
            "fde_takeaway": f"Evaluate {top_repo['name']} for client relevance. If it solves a real problem, early expertise = premium positioning. If not, you save clients from chasing hype.",
            "sources": [top_repo['url']]
        }
    elif framework_updates:
        update = framework_updates[0]
        return {
            "topic": f"Framework Alert: {update['framework']} {update['version']}",
            "summary": f"{update['framework']} released {update['version']}. Framework updates can break client implementations or unlock new capabilities. FDEs need to quickly assess impact.",
            "fde_takeaway": f"Review {update['framework']} changelog for breaking changes. Proactive outreach to affected clients positions you as their technical guardian.",
            "sources": [update['url']]
        }
    elif papers:
        paper = papers[0]
        return {
            "topic": paper['title'][:60],
            "summary": paper.get('tldr', 'Research summary'),
            "fde_takeaway": paper.get('fde_takeaway', 'Review for client applicability'),
            "sources": [paper['url']]
        }
    else:
        return {
            "topic": "FDE Best Practice: Documentation",
            "summary": "The best FDEs document everything. Every client solution becomes a reusable framework. Every war story becomes a case study. Build your playbook.",
            "fde_takeaway": "Start a 'patterns' file. Log what works, what fails, what surprises clients. This is your IP.",
            "sources": []
        }

def build_brief():
    """Build the complete FDE brief."""
    print("\n🔨 Building FDE Brief...")
    
    # Fetch all sources
    github_repos = fetch_github_trending()
    hf_papers = fetch_hf_papers()
    arxiv_papers = fetch_arxiv_papers()
    reddit_posts = fetch_reddit_ml()
    framework_updates = fetch_framework_updates()
    ms_updates = fetch_microsoft_copilot_updates()
    linkedin_insights = fetch_linkedin_insights()
    urgent_alerts = check_api_changelogs()
    
    # Merge papers from HF and arXiv
    all_papers = hf_papers + arxiv_papers
    seen_titles = set()
    unique_papers = []
    for p in all_papers:
        title = p.get("title", "")
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_papers.append(p)
    
    # Generate insights
    opportunities = generate_fde_opportunities(github_repos, unique_papers, reddit_posts, framework_updates)
    deep_dive = generate_deep_dive(github_repos, unique_papers, framework_updates)
    
    # Build brief
    brief = {
        "schema_version": "2.0",
        "generated_at": datetime.now().isoformat(),
        "edition": f"fde-brief-{datetime.now().strftime('%Y%m%d')}",
        "summary": {
            "urgent_alerts": len(urgent_alerts),
            "hot_projects": len(github_repos),
            "research_papers": len(unique_papers),
            "community_discussions": len(reddit_posts),
            "fde_opportunities": len(opportunities),
            "framework_updates": len(framework_updates)
        },
        "urgent_alerts": urgent_alerts,
        "hot_this_week": {
            "github_trending": github_repos,
            "hf_papers": unique_papers[:5],
            "framework_updates": framework_updates,
            "microsoft_updates": ms_updates
        },
        "research_roundup": unique_papers[:5],
        "community_pulse": {
            "reddit": reddit_posts,
            "linkedin_insights": linkedin_insights
        },
        "fde_opportunities": opportunities,
        "deep_dive": deep_dive,
        "metadata": {
            "sources_checked": [
                "GitHub Trending",
                "Hugging Face Papers", 
                "arXiv",
                "Reddit r/MachineLearning",
                "LangChain/LlamaIndex Releases",
                "Microsoft Copilot Updates",
                "LinkedIn Insights (proxy)",
                "OpenAI/Anthropic Changelogs"
            ],
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
    sources_data = {
        "github": brief["hot_this_week"]["github_trending"],
        "papers": brief["hot_this_week"]["hf_papers"],
        "reddit": brief["community_pulse"]["reddit"],
        "framework_updates": brief["hot_this_week"]["framework_updates"]
    }
    for source_name, data in sources_data.items():
        source_file = SOURCES_DIR / f"{source_name}-{datetime.now().strftime('%Y%m%d')}.json"
        with open(source_file, 'w') as f:
            json.dump(data, f, indent=2)

def main():
    """Main entry point."""
    print("="*60)
    print("🚀 FDE-Feed Fetcher v2")
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
    print(f"  🚨 Urgent Alerts: {brief['summary']['urgent_alerts']}")
    print(f"  🔥 Hot Projects: {brief['summary']['hot_projects']}")
    print(f"  📚 Research Papers: {brief['summary']['research_papers']}")
    print(f"  💬 Community Posts: {brief['summary']['community_discussions']}")
    print(f"  💼 FDE Opportunities: {brief['summary']['fde_opportunities']}")
    print(f"  🔧 Framework Updates: {brief['summary']['framework_updates']}")
    print(f"\n⏱️  Duration: {duration:.1f}s")
    print(f"📅 Next Update: {brief['metadata']['next_update'][:10]}")

if __name__ == "__main__":
    main()
