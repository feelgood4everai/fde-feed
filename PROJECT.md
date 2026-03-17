# FDE-Feed: Forward Deployed Intelligence System

## Vision
An autonomous intelligence system that curates AI/LLM developments for Forward Deployed Engineers. Monitors 8+ sources, generates actionable briefs, and creates content for personal brand building.

## Target Users
AI engineers and FDEs who need to stay ahead of the curve without drowning in information overload.

## Key Differentiators
- Curated by someone actually deploying AI in production
- Focused on practical opportunities, not just news
- Automated content generation for thought leadership

## Milestone 1: Complete Automation Pipeline
Make the entire pipeline autonomous and reliable.

### Slices

#### Slice 1: Fix Orchestrator & Data Pipeline
The current orchestrator has issues. Fix them and make it reliable.

**Success Criteria:**
- [ ] Fix runner.py argument parsing (already done)
- [ ] Add proper error handling and notifications
- [ ] Create working data fetchers for all 8 sources
- [ ] Generate structured brief in JSON + Markdown
- [ ] Auto-push to GitHub on success

#### Slice 2: Interactive Dashboard
Build a proper Hugging Face Space dashboard for the brief.

**Success Criteria:**
- [ ] Streamlit or Gradio dashboard showing latest brief
- [ ] Historical archive browser
- [ ] Source filtering and search
- [ ] Mobile-friendly UI
- [ ] Deploy to HF Space automatically

#### Slice 3: Content Generation
Auto-generate LinkedIn/Twitter content from briefs.

**Success Criteria:**
- [ ] Extract key insights from brief
- [ ] Generate 3-5 LinkedIn post variations
- [ ] Generate Twitter thread
- [ ] Save to local files (not auto-post)
- [ ] Include relevant hashtags and mentions

## Technical Stack
- Python 3.11+
- SQLite for data storage
- GitHub API for repo creation
- Hugging Face API for Space deployment
- Streamlit/Gradio for dashboard
- Scheduled via cron

## Success Criteria
- Runs every 2 days without manual intervention
- Generates complete brief with 8+ sources
- Dashboard shows latest brief with good UX
- Content ready for manual review/posting
- All errors logged and notified
