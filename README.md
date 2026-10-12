# AntDesigner — AI-Based CPW Antenna Synthesis

[![Live Demo](https://img.shields.io/badge/Live-Demo-2ea44f)](https://antenna-ai-project.fly.dev/)
[![Dockerfile](https://img.shields.io/badge/Dockerfile-available-2496ED)](Dockerfile)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> A FastAPI workbench for forward and inverse CPW antenna synthesis, bringing CST-backed simulation data and an existing trained surrogate into one deployable design workflow.

---

### 📌 Overview & Engineering Background

AntDesigner is a graduation research project from the Technical College of Engineering, Communication Department, Sulaymaniyah Polytechnic University. It focuses on coplanar-waveguide-fed microstrip patch antenna synthesis across the project’s 1–7 GHz frequency range and 12 patch shapes grouped into four families.

The deployed interface is a static HTML/CSS/JavaScript application served by FastAPI. Its scientific engine retains the existing CST-data and ML inference paths; this repository does not train or retrain the model.

The workbench provides:

- **Forward prediction:** evaluate a shape and patch dimensions and return antenna metrics and response curves.
- **Inverse design:** search for a geometry for a target resonant frequency, shape family, and optimization priority.
- **Visual analysis:** antenna geometry views, Plotly visuals, and S11/VSWR response charts.
- **Engine validation:** run the application’s validation workflows against the data and model available to the running instance.
- **AETHER:** optional server-side Groq chat, enabled with `GROQ_API_KEY`.

The public FastAPI workbench constrains Lp and Wp to 10–35 mm, as configured in the API. The legacy Streamlit entry point, `10_web_app.py`, remains at the repository root as a rollback and parity reference; it is not the production entry point.

### 📊 System Architecture

The architecture diagram is maintained in [`docs/architecture.md`](docs/architecture.md). The FastAPI backend is under `src/backend/`; the browser application is under `web/`. Root-level antenna modules and `engine_v2.py` remain in place for compatibility with the unchanged Streamlit reference.

### 🛠️ Tech Stack

- **Language:** Python 3.11; browser-side JavaScript, HTML, and CSS.
- **Web/API:** FastAPI, Uvicorn, Pydantic.
- **Scientific and ML libraries:** NumPy, pandas, TensorFlow CPU, scikit-learn, SciPy, Joblib, and Matplotlib.
- **Browser visualization:** Plotly.js, served locally from `web/vendor/`.
- **Model and data delivery:** Hugging Face Hub; the full model and CST CSV are external to Git.
- **Optional assistant:** Groq API, configured server-side.
- **Interfaces and standards:** same-origin HTTP/JSON API; Git LFS pointer files are retained for the tracked scaler paths.
- **Deployment and verification:** Docker, Fly.io, and Python verification scripts under `tests/`.

### 🚀 Quick Start & Installation

Use Python 3.11. Clone the repository and install the pinned dependencies:

```bash
git clone https://github.com/kara-nawzad/Antenna-AI-Project.git
cd Antenna-AI-Project
python -m venv .venv
```

Activate the environment, then install dependencies. PowerShell activation:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS/Linux activation:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

For full inference, the authentic `scaler_geo.pkl` and `scaler_perf.pkl` bytes must be provisioned locally at the repository root. Git tracks pointer files at those paths; do not commit replacement scaler bytes. The Keras model and CST CSV are not in Git and are fetched from the configured Hugging Face repository. Without the real local scalers, the server can report health but the inference engine cannot initialize successfully.

Run the application from the repository root:

```bash
python -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8080
```

Open <http://localhost:8080>. Check the health endpoint with:

```bash
curl -fsS http://localhost:8080/health
```

Set `GROQ_API_KEY` in the server environment to enable AETHER. Keep the key out of frontend files and Git.

#### Docker

With the genuine scaler files available locally, build and run the image:

```bash
docker build -t antdesigner .
docker run --rm -p 8080:8080 antdesigner
```

The Dockerfile checks for unresolved scaler pointers, downloads the Keras model and CST CSV at build time, starts Uvicorn on port 8080, and checks `/health`. The Fly configuration uses the same port and health path.

#### Verification scripts

After installing the dependencies, run:

```bash
python tests/test_engine_core_source.py
python tests/test_api_shell.py
python tests/test_parity.py
```

The parity script requires genuine scaler bytes, the model, and CST data. It reports **NOT VERIFIED** rather than claiming a pass when those assets are unavailable.

### 📈 Results & Performance Metrics

No verified real-CST performance report or research paper is included in this repository, so no numerical performance table is presented here. Use the application’s **Engine Validation** workflow with the authentic CST dataset and model for project-specific measurements. Earlier repository documentation described synthetic-data comparison figures; they are not presented as verified CST results.

### 👤 Author

**Kara Nawzad** — Communication Engineer

[GitHub profile](https://github.com/kara-nawzad) · [Live application](https://antenna-ai-project.fly.dev/)
