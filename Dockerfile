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
    HF_HUB_DISABLE_TELEMETRY=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY web/ ./web/
COPY assets/ ./assets/

# Small scalers are now fetched from HF like the model/CSV so a fresh
# clone does NOT need local scaler_geo.pkl/scaler_perf.pkl. If those files
# already exist in the build context they are kept, otherwise they are
# downloaded. This removes the 129-byte LFS pointer failure.
ARG HF_REPO=kara-nawzad/antenna-models
ARG HF_REVISION=main
ENV HF_REPO=${HF_REPO}
ENV HF_REVISION=${HF_REVISION}
RUN python -c "import os; from huggingface_hub import hf_hub_download; \
repo=os.environ['HF_REPO']; rev=os.environ['HF_REVISION']; \
[print(f'[build] fetching {f} from {repo}@{rev}') or hf_hub_download(repo_id=repo, filename=f, revision=rev, local_dir='.') \
 for f in ('scaler_geo.pkl','scaler_perf.pkl','forward_model_v2_curve.keras','antenna_data_cleaned.csv') \
 if not os.path.exists(f)]"
RUN python -c "import sys; \
bad=[p for p in ('scaler_geo.pkl','scaler_perf.pkl','forward_model_v2_curve.keras','antenna_data_cleaned.csv') \
     if not __import__('os').path.exists(p) or open(p,'rb').read(32).startswith(b'version https://git-lfs')]; \
sys.exit(f'ERROR: missing or pointer asset(s): {bad} -- ensure HF_REPO={__import__(\"os\").environ.get(\"HF_REPO\")} contains them at revision {__import__(\"os\").environ.get(\"HF_REVISION\")}') if bad else print('[build] all 4 assets present')"

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=5 \
    CMD curl -fsS http://localhost:8080/health || exit 1

CMD ["python", "-m", "uvicorn", "antdesigner.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
