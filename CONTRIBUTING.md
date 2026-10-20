# Contributing

1. Use Python 3.11 and create an isolated virtual environment.
2. Install runtime and development dependencies: `python -m pip install -r requirements.txt -r requirements-dev.txt`, then `python -m pip install -e .`.
3. Keep model, dataset, scaler, and credential files out of Git. Follow `docs/model-data.md` for local inference prerequisites.
4. Before opening a pull request, run `python -m pytest` and `ruff check src tests`.
5. Keep API routes and JSON contracts stable unless the change explicitly updates the frontend and tests. Do not change Fly app/domain/health settings without deployment-owner approval.
6. Use focused commits and describe behavior changes and verification in the pull request.
