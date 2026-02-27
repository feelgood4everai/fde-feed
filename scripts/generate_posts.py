#!/usr/bin/env python3
"""
Generate LinkedIn posts from FDE-Feed briefs
"""

import json
import random
from datetime import datetime
from pathlib import Path

def load_brief():
    """Load latest brief."""
    with open("data/latest.json") as f:
        return json.load(f)

def generate_hook():
    """Generate attention-grabbing hook."""
    hooks = [
        "I spent 5 hours this week staying current on AI. Now I do it in 5 minutes.",
        "My clients ask 'Have you heard about X?' I always have an answer.",
        "The best FDEs don't just build — they see around corners.",
        "I built this because I was tired of being surprised by client questions.",
        "26 years in IT taught me: Information asymmetry is a competitive advantage.",
    ]
    return random.choice(hooks)

def generate_body(brief):
    """Generate post body from brief content."""
    lines = []
    
    # Top insight
    opportunities = brief.get("fde_opportunities", [])
    if opportunities:
        top_opp = opportunities[0]
        lines.append(f"💡 This week's top FDE opportunity:")
        lines.append(f"{top_opp['title']}")
        lines.append(f"{top_opp['description'][:100]}...")
        lines.append("")
    
    # Hot project
    repos = brief.get("hot_this_week", {}).get("github_trending", [])
    if repos:
        top_repo = repos[0]
        lines.append(f"🔥 Trending: {top_repo['name']} ({top_repo['stars']:,} stars)")
        lines.append(f"Why FDEs care: {top_repo.get('fde_relevance', 'AI tooling')}")
        lines.append("")
    
    # Alert if any
    alerts = brief.get("urgent_alerts", [])
    if alerts:
        lines.append(f"🚨 Urgent: {alerts[0]['title']}")
        lines.append(f"Action: {alerts[0]['action']}")
        lines.append("")
    
    return "\n".join(lines)

def generate_cta():
    """Generate call-to-action."""
    ctas = [
        "I built FDE-Feed to automate my research. Get the full brief →",
        "Want the complete FDE intelligence brief? Link below 👇",
        "Full brief (including all opportunities) →",
        "This is just the highlights. Full analysis →",
    ]
    return random.choice(ctas)

def generate_hashtags():
    """Generate hashtags."""
    tags = [
        "#ForwardDeployedEngineer",
        "#FDE",
        "#AIEngineering",
        "#LLM",
        "#Consulting",
        "#ProductionAI",
        "#MLOps",
        "#TechLeadership",
        "#OpenSource",
    ]
    return " ".join(random.sample(tags, 5))

def generate_post(brief):
    """Generate complete LinkedIn post."""
    post = f"""{generate_hook()}

{generate_body(brief)}

{generate_cta()}

🔗 GitHub: https://github.com/feelgood4everai/fde-feed
📊 Dashboard: https://huggingface.co/spaces/AnandGeetha/fde-feed

{generate_hashtags()}

---

💼 I'm a Forward Deployed Engineer helping enterprises deploy production AI systems.

Available Q2 2026 for:
• AI strategy consulting
• LLM production deployment
• RAG system architecture
• Team training & best practices

📩 DM me or connect: https://linkedin.com/in/anandbg
"""
    return post

def generate_thread(brief):
    """Generate Twitter/X thread version."""
    tweets = []
    
    # Tweet 1: Hook
    tweets.append(f"🧵 FDE Brief — {datetime.now().strftime('%b %d')}\n\nAs a Forward Deployed Engineer, I built a system to stay current without the 5-hour research burden.\n\nHere's what caught my attention this week: 👇")
    
    # Tweet 2: Opportunity
    opportunities = brief.get("fde_opportunities", [])
    if opportunities:
        opp = opportunities[0]
        tweets.append(f"💡 Opportunity of the week:\n\n{opp['title']}\n\n{opp['description'][:100]}...\n\nClient type: {opp['client_type']}\nPotential: {opp['potential_value']}")
    
    # Tweet 3: Hot project
    repos = brief.get("hot_this_week", {}).get("github_trending", [])
    if repos:
        repo = repos[0]
        tweets.append(f"🔥 Trending on GitHub:\n\n{repo['name']}\n⭐ {repo['stars']:,} stars\n\n{repo['description'][:120]}...\n\nFDE relevance: {repo.get('fde_relevance', 'AI tooling')[:100]}")
    
    # Tweet 4: Framework update
    updates = brief.get("hot_this_week", {}).get("framework_updates", [])
    if updates:
        update = updates[0]
        tweets.append(f"🔧 Framework Alert:\n\n{update['framework']} {update['version']}\n\nIf your clients use {update['framework']}, check for breaking changes.\n\nProactive outreach = trust building.")
    
    # Tweet 5: CTA
    tweets.append(f"📊 Full brief with all opportunities, research papers, and community insights:\n\nhttps://huggingface.co/spaces/AnandGeetha/fde-feed\n\nBuilt for FDEs, by an FDE.\n\n#ForwardDeployedEngineer #AI")
    
    return "\n\n---\n\n".join(tweets)

def main():
    """Generate posts."""
    print("📝 Generating LinkedIn posts...")
    
    brief = load_brief()
    
    # Generate LinkedIn post
    linkedin_post = generate_post(brief)
    
    # Generate Twitter thread
    twitter_thread = generate_thread(brief)
    
    # Save posts
    posts_dir = Path("/home/openclaw/linkedin-posts")
    posts_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d")
    
    # LinkedIn
    linkedin_file = posts_dir / f"fde-brief-linkedin-{timestamp}.txt"
    with open(linkedin_file, 'w') as f:
        f.write(linkedin_post)
    print(f"  ✅ LinkedIn post: {linkedin_file}")
    
    # Twitter
    twitter_file = posts_dir / f"fde-brief-twitter-{timestamp}.txt"
    with open(twitter_file, 'w') as f:
        f.write(twitter_thread)
    print(f"  ✅ Twitter thread: {twitter_file}")
    
    # Preview
    print("\n" + "="*60)
    print("📱 LinkedIn Post Preview:")
    print("="*60)
    print(linkedin_post[:500] + "..." if len(linkedin_post) > 500 else linkedin_post)
    
    print("\n" + "="*60)
    print("🐦 Twitter Thread Preview (first tweet):")
    print("="*60)
    first_tweet = twitter_thread.split("\n\n---\n\n")[0]
    print(first_tweet[:280])

if __name__ == "__main__":
    main()
