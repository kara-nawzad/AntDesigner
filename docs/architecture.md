# System architecture

The production service is a single FastAPI process on port 8080. It serves the browser application and API from the same origin; the legacy Streamlit source is retained separately for rollback/parity purposes.

```mermaid
flowchart LR
    Browser[Browser]
    Web["web/ static UI<br/>HTML · CSS · JavaScript · Plotly.js"]
    API["FastAPI<br/>src/backend/main.py<br/>port 8080"]
    Assets["Shared images<br/>assets/ → /assets/*"]
    Core["Numerical API engine<br/>src/backend/engine_core.py"]
    V2["Existing inference module<br/>engine_v2.py (root)"]
    External["Hugging Face Hub<br/>Keras model + CST CSV"]
    Scalers["scaler_geo.pkl + scaler_perf.pkl<br/>tracked Git LFS pointer files;<br/>real bytes are provisioned locally"]
    Viz["Visualization helpers<br/>antenna_viz.py + antenna_charts.py (root)"]
    Aether["AETHER adapter<br/>src/backend/aether.py"]
    Groq["Groq API<br/>only when GROQ_API_KEY is set"]
    Fly["Fly.io container<br/>HTTP port 8080 · /health"]
    Legacy["Legacy Streamlit reference<br/>10_web_app.py (root)"]

    Browser <-->|"same-origin HTTP"| API
    API -->|"/static/*"| Web
    API -->|"/assets/*"| Assets
    API --> Core
    Core --> V2
    Core --> Scalers
    V2 -. "fetches missing model assets" .-> External
    Core --> Viz
    API --> Aether
    Aether -. "optional chat" .-> Groq
    Fly --> API
    Legacy -. "rollback/parity source" .-> V2
    Legacy -.-> Viz
    Legacy -.-> Assets
```

## Runtime paths

- `src/backend/main.py` owns FastAPI routes, synchronous engine startup, static serving, health reporting, and validation/API orchestration.
- `src/backend/engine_core.py` contains the API-side numerical functions and loads the unchanged root-level `engine_v2.py` module.
- `src/backend/aether.py` calls Groq only when a server-side `GROQ_API_KEY` is configured.
- `web/` is mounted at `/static`; root `assets/` is mounted at `/assets`. These URLs are same-origin with the API.
- The Docker image downloads the model and CST CSV during build. The scaler paths are checked at build time and must contain genuine local scaler bytes for a usable engine; committed Git LFS pointer text is not pickle data.
- Fly.io uses internal port 8080 and the `/health` HTTP check defined in `fly.toml`.
