# Contributing

1. Use Python 3.11 and create an isolated virtual environment.
2. Install runtime and development dependencies: `python -m pip install -r requirements.txt -r requirements-dev.txt`, then `python -m pip install -e .`.
3. Keep model, dataset, scaler, and credential files out of Git. Follow `docs/model-data.md` for local inference prerequisites.
4. Before opening a pull request, run `python -m pytest` and `ruff check src tests scripts`.
5. To record real inference regression outputs, provision genuine local scalers, `forward_model_v2_curve.keras`, and `antenna_data_cleaned.csv`, then run `python scripts/capture_golden.py`. Review the generated `tests/fixtures/golden.json`; never hand-author expected model outputs. The integration test skips when the fixture or real assets are absent.
6. Keep API routes and JSON contracts stable unless the change explicitly updates the frontend and tests. Do not change Fly app/domain/health settings without deployment-owner approval.
7. Use focused commits and describe behavior changes and verification in the pull request.
