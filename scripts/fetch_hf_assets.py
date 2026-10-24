import os
from huggingface_hub import hf_hub_download

repo = os.environ['HF_REPO']
rev = os.environ['HF_REVISION']

def need(p: str) -> bool:
    if not os.path.exists(p):
        return True
    try:
        with open(p, 'rb') as fh:
            return fh.read(32).startswith(b'version https://git-lfs')
    except Exception:
        return True

for fname in ('scaler_geo.pkl', 'scaler_perf.pkl', 'forward_model_v2_curve.keras', 'antenna_data_cleaned.csv'):
    if need(fname):
        try:
            print(f'[build] fetching {fname} from {repo}@{rev}')
            hf_hub_download(repo_id=repo, filename=fname, revision=rev, local_dir='.')
            print(f'[build] fetched {fname}')
        except Exception as e:
            print(f'[build] could not fetch {fname} from HF: {e}')
