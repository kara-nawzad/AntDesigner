# Model, dataset, and scaler assets

## Required runtime files

The production engine reads `scaler_geo.pkl` and `scaler_perf.pkl` from the project root. It loads `forward_model_v2_curve.keras` and `antenna_data_cleaned.csv` from the Hugging Face repository configured by `HF_REPO` (default: `kara-nawzad/antenna-models`). The Docker build downloads the model and CSV into `/app` before startup.

The two tracked scaler paths are currently 129-byte Git LFS pointer files, not usable pickle files. `.gitattributes` applies Git LFS to `*.keras` only; it does not apply an LFS filter to `*.pkl`. The tracked pointers therefore likely reflect historical LFS storage/checkout state and must not be interpreted as scaler contents. The Dockerfile copies those paths and fails its build if either starts with the Git LFS pointer header. It does not currently download scalers, materialize them, or access a secret/volume containing them. The Fly deployment could be working because the deploy machine supplied actual local files in its build context, but that mechanism is not represented in this repository and cannot be confirmed here.

## New contributor build prerequisites

1. Obtain the authentic scaler files from the project maintainer through an approved secure channel. Do not commit them or put them in a public issue.
2. Place them in the repository root with the exact names `scaler_geo.pkl` and `scaler_perf.pkl`.
3. Confirm they are real pickle bytes, not pointer text (`head -c 32 scaler_geo.pkl` must not show `version https://git-lfs`).
4. Ensure the Hugging Face repository configured by `HF_REPO` contains the exact model and CSV filenames above and is accessible to the build. For a private repository, configure access securely using the existing deployment mechanism; no token should be committed.
5. Build the image and run the checks described in `README.md`.

## Recommended reviewed fix (proposal only; not applied)

The cleanest reproducible option is to store the scaler artifacts in the same Hugging Face model repository and download them alongside the model and CSV during Docker build. Confirm the exact filenames, access policy, artifact revisions/checksums, and whether the repo is public before adopting this. A proposed Dockerfile block, replacing the current `COPY scaler_geo.pkl scaler_perf.pkl ./` and pointer-check block, is:

```dockerfile
ARG HF_REPO=kara-nawzad/antenna-models
ARG HF_REVISION=main
ENV HF_REPO=${HF_REPO}
ENV HF_REVISION=${HF_REVISION}
RUN python -c "import os; from huggingface_hub import hf_hub_download; \
repo=os.environ['HF_REPO']; rev=os.environ['HF_REVISION']; \
[ hf_hub_download(repo_id=repo, filename=f, revision=rev, local_dir='.') \
  for f in ('scaler_geo.pkl', 'scaler_perf.pkl', 'forward_model_v2_curve.keras', 'antenna_data_cleaned.csv') ]"
```

For a production-grade immutable build, replace `main` with a reviewed immutable commit/revision and record artifact checksums. If private, pass a short-lived build secret using BuildKit secret mounts (not an `ARG`, `ENV`, or committed config), and verify Fly's remote builder supports that flow. This proposal changes no current deployment behavior because it is documentation only.
