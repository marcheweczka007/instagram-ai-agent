# Project Review — v1.0

## Architecture review

The project follows a clean layered layout:

```
CLI / pipelines
    ↓
agents (Discovery, Scorer, Research)
browser (InstagramScraper)
    ↓
domain models
    ↓
services (CSV, JSON, Markdown report)
```

Pipelines orchestrate; agents and services own business logic. That separation is the main architectural strength.

## Strengths

- Clear domain models (`BrandProfile`, `AnalysisResult`, `ResearchAnalysis`, `BrandResearchResult`)
- Brand-fit research is separated from generic profile scoring
- Browser Use concerns isolated from OpenAI scoring/research
- Deterministic report generation (no LLM in the formatter)
- Configurable timeouts, models, and output folders
- Shared OpenAI client reduces connection churn

## Weaknesses

- Instagram discovery via Google is brittle (CAPTCHA / geo / login walls)
- Browser Use still depends on LLM latency for extraction
- `discover_and_research` is sequential and can be slow on large result sets
- Smoke demos (`*_test.py`) coexist with real pytest tests — naming can confuse newcomers
- No authentication/session strategy for Instagram login-gated content

## Technical debt

- Empty-ish placeholder agents (`CommenterAgent`, `MemoryAgent`)
- `langchain-openai` dependency is unused and should be removed unless needed later
- Limited integration tests against live Browser Use (intentionally mocked in CI)
- Ranking thresholds and report copy are still heuristic

## Future improvements

1. Persist brand + research results in a database
2. Multi-tenant SaaS API (FastAPI) around existing pipelines
3. Platform adapters (TikTok / YouTube) feeding the same `ResearchAgent`
4. Concurrent analysis with rate limits
5. Human-in-the-loop review UI for outreach drafts
6. Richer evaluation harness for prompt quality
