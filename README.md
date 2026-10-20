# AntDesigner

FastAPI workbench for forward and inverse synthesis of coplanar-waveguide-fed patch antennas, based on CST simulation data and an existing trained surrogate. The browser UI and API are served from the same origin.

- **Live on Fly.io:** https://antenna-ai-project.fly.dev/
- **Custom domain:** [MY CUSTOM DOMAIN URL - FILL IN] (replace with the production domain)
- **Repository:** https://github.com/kara-nawzad/AntDesigner
- **License:** MIT; see [LICENSE](LICENSE).

## Features

- Forward performance prediction from antenna shape and patch dimensions.
- Inverse geometry search for target resonant frequency, shape family, and priority.
- Interactive response, comparison, 3D antenna, design-space, and validation views.
- Optional AETHER chat assistant through Groq (server-side key only).
- Health endpoint at `/health`.

The production API constrains Lp and Wp to 10–35 mm, the documented CST-backed domain. This repository does not train the model.

## Technology and architecture

Python 3.11, FastAPI, Uvicorn, Pydantic, NumPy, pandas, TensorFlow CPU, scikit-learn, Joblib, SciPy, Matplotlib, Plotly, and Groq. The frontend is static HTML/CSS/JavaScript; Plotly.js and fonts are served locally. Docker builds the Fly.io image. The architecture details are in [docs/architecture.md](docs/architecture.md).

```text
src/antdesigner/
├── api/main.py                 FastAPI app and HTTP routes
├── engine/core.py              scientific prediction and validation paths
├── engine/model_v2.py          trained-model inference helper
├── services/aether.py          optional Groq adapter
└── visualization/              Plotly and antenna geometry helpers
web/                            static UI, fonts, and Plotly.js
assets/                         images served at /assets/
tests/unit/                     asset-independent source checks
tests/integration/              API shell tests (external model/data not required)
docs/                           architecture, deployment, and model-data notes
```

## Required external inference assets

The project root must contain genuine `scaler_geo.pkl` and `scaler_perf.pkl` pickle files. The files currently tracked in Git are 129-byte Git LFS pointer text, not scaler data. The Dockerfile copies them and fails early if it detects pointer text; it does **not** fetch them. The production model and dataset are fetched from Hugging Face during image build: `forward_model_v2_curve.keras` and `antenna_data_cleaned.csv` in `HF_REPO` (default `kara-nawzad/antenna-models`). See [docs/model-data.md](docs/model-data.md) for contributor prerequisites and the proposed, unapplied scaler-hosting fix.

Obtain authentic scaler files from the maintainer through an approved secure channel and place them at the repository root. Do not commit them. The model/data repo must be reachable by the Docker build. For private repositories, credentials must be injected securely by the builder and never stored in source or image layers.

## Local setup

Use Python 3.11. Clone and install:

```bash
git clone https://github.com/kara-nawzad/AntDesigner.git
cd AntDesigner
python -m venv .venv
# Activate the environment, then:
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

Run the API (requires the external assets above for a ready inference engine):

```bash
python -m uvicorn antdesigner.api.main:app --host 0.0.0.0 --port 8080
```

Open http://localhost:8080. The health endpoint is http://localhost:8080/health. Set `PYTHONPATH=src` if you do not install the package editable.

## Tests and lint

```bash
python -m pytest
ruff check src tests
```

The API shell tests are designed to work without model/data assets; runtime dependencies such as FastAPI are still required. Model-dependent prediction and parity verification require the authentic scalers, Hugging Face model, and CST CSV.

## Deployment to Fly.io

Production deploy configuration is in `fly.toml`; the Dockerfile binds Uvicorn to port 8080 and exposes `/health`. The checked-in Fly app is `antenna-ai-project` in region `fra`. Do not change the Fly app, region, port, health path, VM size, or domain/certificate configuration without an explicit operations review.

To build and deploy from a machine with Docker, Fly CLI access, and authentic scaler files:

```bash
docker build -t antdesigner:local .
fly deploy
```

For live checks of both the Fly URL and custom domain, see [docs/deployment.md](docs/deployment.md). Never put Fly or Hugging Face credentials in `.env`, Docker build arguments, or committed files. `.env.example` contains placeholders only.

## Environment variables

| Variable | Purpose | Default / expected value |
|---|---|---|
| `GROQ_API_KEY` | Enables AETHER chat; server-side secret only | unset (feature disabled) |
| `HF_REPO` | Hugging Face repo containing model and data | `kara-nawzad/antenna-models` |
| `PORT` | Container/service port | `8080` |
| `TF_NUM_INTRAOP_THREADS` | TensorFlow intra-op threads | `1` in Docker |
| `TF_NUM_INTEROP_THREADS` | TensorFlow inter-op threads | `1` in Docker |
| `OMP_NUM_THREADS` | OpenMP threads | `1` in Docker |
| `TF_CPP_MIN_LOG_LEVEL` | TensorFlow log verbosity | `2` in Docker/Fly |
| `HF_HUB_DISABLE_TELEMETRY` | Disable Hub telemetry | `1` in Docker |

## Project documentation

- [Architecture](docs/architecture.md)
- [Deployment and domain checks](docs/deployment.md)
- [Model, dataset, and scaler assets](docs/model-data.md)
- [Contributing](CONTRIBUTING.md)
