# Repository Guidelines

## Project Structure & Module Organization
The FastAPI application lives in `app/`: `api/v1` exposes versioned routers, `core` manages settings/CORS, `db` encapsulates persistence helpers, `lib` houses shared utilities, `models` and `schemas` define domain logic and Pydantic DTOs. `main.py` boots the ASGI app. Supporting assets live in `scripts/` (automation), `bash/` (deployment + media tooling), `data/`, `examples/`, and `notebooks/`. Pytest suites belong in `tests/`, mirroring the feature modules they verify.

## Build, Test, and Development Commands
- `poetry install` — install runtime and dev dependencies from `pyproject.toml`.
- `poetry run python main.py` — launch the API in development; reload toggles via `RUN_ENV`.
- `poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8080` — expose the service for networked testing.
- `poetry run pytest` — execute the full test suite; add `-k` and paths to scope runs.
- `bash bash/deploy_source_to_cloud_run.sh` — deploy the current source to Google Cloud Run.
- `ngrok start --all` — start the predefined tunnels for external webhook integrations.

## Coding Style & Naming Conventions
Write Python 3.10 code that adheres to PEP 8 with four-space indentation. Keep modules and functions `snake_case`, classes `PascalCase`, and constants `UPPER_SNAKE_CASE`. Group FastAPI routers by feature within `app/api/v1`. Prefer explicit type hints and docstrings on public interfaces. Update associated schema definitions in `app/schemas` when endpoints change.

## Testing Guidelines
Use Pytest, placing files as `tests/test_<feature>.py` and naming classes `TestFeature`. Scope fixtures to the modules under test and isolate secrets with temporary environment variables. Aim to cover new branches, including failure paths, before submitting a PR. Run targeted checks with `poetry run pytest tests/test_encription.py -k decrypt` when iterating quickly, and ensure a clean suite before merging.

## Commit & Pull Request Guidelines
Follow the existing Git history by writing concise, imperative commit subjects (e.g., `Add get_relative_date helper`). Commit logical units and avoid bundling unrelated changes. Pull requests should summarize the feature or fix, reference related issues, note configuration updates (such as new `.env` keys), and include proof of testing (`poetry run pytest` output or equivalent). Attach screenshots or sample payloads when altering user-facing responses.

## Environment & Configuration
Configuration is driven by `.env` files loaded through `app/core/config.py`; never commit secrets. Duplicate `.env.test` when crafting deterministic test data. Document any new environment keys in the PR and consider providing safe defaults. Set `RUN_ENV=production` only when deploying, otherwise keep it at `development` for auto-reload and verbose logging.
