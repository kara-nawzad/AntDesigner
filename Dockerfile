FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    # TensorFlow on a single shared vCPU: cap the thread pools. The defaults spawn
    # one worker per host core and then thrash, which costs both startup time and
    # steady-state latency.
    TF_NUM_INTRAOP_THREADS=1 \
    TF_NUM_INTEROP_THREADS=1 \
    OMP_NUM_THREADS=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    HF_HUB_DISABLE_TELEMETRY=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY web/ ./web/
COPY assets/ ./assets/
COPY engine_v2.py antenna_charts.py antenna_viz.py ./
COPY scaler_geo.pkl scaler_perf.pkl ./

# Fail before a long model download if the two required small scalers were copied
# as Git-LFS pointer text rather than their real pickle bytes.
RUN python -c "import sys; \
bad=[p for p in ('scaler_geo.pkl','scaler_perf.pkl') \
     if open(p,'rb').read(32).startswith(b'version https://git-lfs')]; \
sys.exit(f'ERROR: unresolved Git LFS pointer(s): {bad} -- materialize the real scaler bytes before fly deploy') if bad else None"

# ---------------------------------------------------------------------------
# Pre-fetch the main model + CST dataset at IMAGE BUILD time. A deployed machine
# therefore does not put a 115 MB model transfer on its health-check/startup path.
# These files are inference assets only; no model/data contents are changed.
# ---------------------------------------------------------------------------
ARG HF_REPO=kara-nawzad/antenna-models
ENV HF_REPO=${HF_REPO}
RUN python -c "import os; from huggingface_hub import hf_hub_download; \
repo=os.environ['HF_REPO']; \
[print(f'[build] fetching {f} from {repo}') or hf_hub_download(repo_id=repo, filename=f, local_dir='.') \
 for f in ('forward_model_v2_curve.keras', 'antenna_data_cleaned.csv') \
 if not os.path.exists(f)]"

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=5 \
    CMD curl -fsS http://localhost:8080/health || exit 1

CMD ["python", "-m", "uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
