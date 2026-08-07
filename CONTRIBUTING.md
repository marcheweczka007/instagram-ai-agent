# Contributing

Thanks for your interest in improving the Instagram Brand Research Assistant.

## Setup

```bash
uv sync --extra dev
cp .env.example .env   # then add OPENAI_API_KEY
```

## Development guidelines

- Keep public pipeline APIs stable.
- Prefer small, focused modules (agents / browser / services / pipelines).
- Add or update tests for behaviour changes.
- Use `ruff check` and `ruff format` before opening a PR.
- Do not commit `.env`, credentials, or files under `outputs/`.

## Pull requests

1. Describe the problem and the solution.
2. Note any API changes.
3. Include test coverage for new logic.
4. Keep PRs focused — one concern per PR when possible.
