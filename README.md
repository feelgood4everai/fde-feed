# FDE-Feed: Forward Deployed Intelligence System

[![GitHub](https://img.shields.io/badge/GitHub-Repo-blue?logo=github)](https://github.com/feelgood4everai/fde-feed)
[![Hugging Face](https://img.shields.io/badge/🤗-Demo-yellow)](https://huggingface.co/spaces/AnandGeetha/fde-feed)

> Autonomous intelligence system that curates AI/LLM developments for Forward Deployed Engineers

## What It Does

**FDE-Feed** monitors 8+ sources every 2 days and generates a curated brief:

- 🔥 **Hot Projects** — Trending AI/ML repos with FDE relevance analysis
- 📚 **Research Papers** — Latest papers from Hugging Face & arXiv  
- 💬 **Community Pulse** — Reddit r/MachineLearning discussions
- 🔧 **Framework Updates** — LangChain, LlamaIndex releases
- 🖥️ **Microsoft Updates** — Copilot roadmap changes
- 🔔 **API Changelogs** — OpenAI, Anthropic alerts
- 💼 **FDE Opportunities** — Actionable business opportunities

## Dashboard

**Live Demo:** [Hugging Face Space](https://huggingface.co/spaces/AnandGeetha/fde-feed)

Features:
- 📊 Real-time metrics
- 🔥 Hot projects browser
- 📚 Research roundup
- 💼 FDE opportunities
- 🚨 Urgent alerts
- 📜 Historical archive

## Architecture

```
fde-feed/
├── scripts/
│   └── fetch_feed.py      # Data fetchers for 8 sources
│   └── generate_readme.py # Markdown brief generator
├── orchestrator/
│   └── runner.py          # Job orchestration
├── frontend/
│   └── app.py             # Streamlit dashboard
├── data/
│   ├── latest.json        # Structured brief data
│   ├── latest.md          # Human-readable brief
│   └── archive/           # Historical briefs
└── hf-space/              # Hugging Face deployment
```

## Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Fetch latest data
python scripts/fetch_feed.py

# Generate markdown brief
python scripts/generate_readme.py

# Run dashboard
streamlit run frontend/app.py
```

## Automation

Runs automatically every 2 days via cron:
```
0 9 */2 * * /home/openclaw/.openclaw/workspace/fde-feed/run-orchestrated.sh
```

## Environment Variables

```bash
GITHUB_TOKEN=ghp_xxx          # For GitHub API
HF_TOKEN=hf_xxx               # For Hugging Face
TELEGRAM_BOT_TOKEN=xxx        # For notifications (optional)
```

## Latest Brief

See [data/latest.md](data/latest.md) for the most recent FDE brief.

---

*Built for Forward Deployed Engineers*
