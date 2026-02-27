# Data Schema

## latest.json Structure

```json
{
  "schema_version": "1.0",
  "generated_at": "ISO8601 timestamp",
  "edition": "brief identifier",
  
  "summary": {
    "urgent_alerts": int,
    "hot_projects": int,
    "research_papers": int,
    "community_discussions": int,
    "fde_opportunities": int
  },
  
  "urgent_alerts": [
    {
      "severity": "critical|high|medium",
      "title": "string",
      "source": "source name",
      "impact": "fde impact description",
      "action": "recommended action",
      "url": "source url",
      "detected_at": "ISO8601"
    }
  ],
  
  "hot_this_week": {
    "github_trending": [
      {
        "name": "repo name",
        "url": "github url",
        "stars": int,
        "stars_gained": int,
        "description": "string",
        "fde_relevance": "why fdes care",
        "fde_use_case": "how to use with clients"
      }
    ],
    "hf_papers": [...],
    "framework_updates": [...]
  },
  
  "research_roundup": [
    {
      "title": "paper title",
      "authors": ["string"],
      "url": "paper url",
      "tldr": "one sentence summary",
      "fde_takeaway": "practical insight for fdes",
      "publication_date": "ISO8601"
    }
  ],
  
  "community_pulse": {
    "reddit": [
      {
        "subreddit": "string",
        "title": "post title",
        "url": "post url",
        "score": int,
        "fde_insight": "what this means for fdes"
      }
    ],
    "linkedin": [...]
  },
  
  "fde_opportunities": [
    {
      "type": "client_conversation|project_idea|optimization",
      "title": "string",
      "description": "string",
      "client_type": "who this applies to",
      "your_move": "recommended action",
      "potential_value": "£X-£Y"
    }
  ],
  
  "deep_dive": {
    "topic": "string",
    "summary": "2-paragraph summary",
    "fde_takeaway": "practical advice",
    "sources": ["url"]
  },
  
  "metadata": {
    "sources_checked": ["list of sources"],
    "fetch_duration_seconds": int,
    "next_update": "ISO8601"
  }
}
```