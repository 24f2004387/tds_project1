# llm-deploy-api — FastAPI /task endpoint (Docker)

This Space runs the LLM Code Deployment API (FastAPI) which accepts instructor task JSON, synthesizes static apps with an LLM, pushes to GitHub and enables Pages.

## How it runs (Docker)
- Entrypoint: `start.sh` -> runs `uvicorn api.server:app` on port `7860`
- Requirements: `api/requirements.txt` (installed by Dockerfile)
- Port: 7860 (exposed)

## Required secrets (Settings → Variables and secrets)
- `EXPECTED_SECRET` — secret students include in the request
- `GITHUB_USERNAME` — GitHub username used for repo creation
- `GH_TOKEN` — GitHub PAT (scopes: `public_repo`; `workflow` helps)
- `OPENAI_API_KEY` — AI Pipe token / OpenAI API key
- `OPENAI_BASE_URL` — `https://aipipe.org/openai/v1` (or `/openrouter/v1`)

## Endpoints
- `POST /task` — receive task requests
- `GET /docs` — OpenAPI docs

## Notes
- Keep secrets in HF's Variables & secrets — do NOT commit `.env`.
- Check **Build logs** for pip install issues and **Runtime logs** for startup traces.
