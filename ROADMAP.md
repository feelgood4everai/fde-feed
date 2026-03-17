# FDE-Feed Roadmap

## Overview
Forward Deployed Intelligence System - Curated AI/LLM developments for FDEs

## Milestone 1: Complete Automation Pipeline

### Slice 1: Fix Orchestrator & Data Pipeline
Status: In Progress

**Tasks:**
1. Fix runner.py argument parsing (done)
2. Add proper error handling and notifications
3. Create working data fetchers for all 8 sources
4. Generate structured brief in JSON + Markdown
5. Auto-push to GitHub on success

**Success Criteria:**
- Orchestrator runs without errors
- All data sources fetch successfully
- Brief generated in both formats
- GitHub push works automatically

### Slice 2: Interactive Dashboard
Status: Not Started

**Tasks:**
1. Design dashboard layout
2. Build Streamlit/Gradio interface
3. Add historical archive browser
4. Implement source filtering
5. Deploy to HF Space

**Success Criteria:**
- Dashboard loads latest brief
- Users can browse history
- Mobile-friendly UI
- Auto-deployed to HF

### Slice 3: Content Generation
Status: Not Started

**Tasks:**
1. Extract key insights from brief
2. Generate LinkedIn posts
3. Generate Twitter threads
4. Save to reviewable files
5. Add hashtag optimization

**Success Criteria:**
- 3-5 post variations generated
- Twitter thread ready
- Content saved locally for review
- No auto-posting (safety)
