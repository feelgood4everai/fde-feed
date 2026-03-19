# M001: Complete FDE-Feed System

**Vision:** Autonomous intelligence system that curates AI/LLM developments for Forward Deployed Engineers.

## Success Criteria

- Pipeline runs automatically every 2 days without manual intervention
- Dashboard deployed and accessible on Hugging Face
- Brief generates in both JSON and Markdown formats
- All changes auto-committed to GitHub

## Key Risks / Unknowns

- API rate limits may block data fetching
- Hugging Face deployment may fail

## Slices

- [x] **S01: Core Pipeline** `risk:low` `depends:[]`
  > After this: Data fetcher works, orchestrator runs, brief generates
- [ ] **S02: Dashboard** `risk:medium` `depends:[S01]`
  > After this: Streamlit dashboard deployed to Hugging Face
- [ ] **S03: GitHub Integration** `risk:low` `depends:[S01]`
  > After this: Auto-push to GitHub on every run

## Milestone Definition of Done

- All slices complete
- Pipeline runs end-to-end automatically
- Dashboard live on Hugging Face
- GitHub repo has latest code
