# Deployment and production checks

## Fly.io deployment

`fly.toml` targets app `antenna-ai-project`, region `fra`, internal port 8080, and `/health`. The Dockerfile builds the image and starts `antdesigner.api.main:app`. The committed configuration also specifies the current VM size and service settings; preserve these unless an explicit deployment change is approved.

Before deploying, make sure authentic `scaler_geo.pkl` and `scaler_perf.pkl` files are present in the build context, Hugging Face can provide `forward_model_v2_curve.keras` and `antenna_data_cleaned.csv`, and any private repository access is injected securely. The tracked scaler pointers are not usable pickle files. See [model-data.md](model-data.md).

Typical owner-operated commands:

```bash
docker build -t antdesigner:local .
fly deploy
```

Do not commit credentials or place secrets in Docker `ARG`/`ENV`. Configure `GROQ_API_KEY` through Fly secrets if the optional assistant is enabled. The existing Fly app/domain/certificate setup is outside this repository's deployment scope.

## Post-deploy verification

Set these URLs to the actual endpoints, replacing the custom-domain placeholder:

```bash
FLY_URL=https://antenna-ai-project.fly.dev
CUSTOM_URL='[MY CUSTOM DOMAIN URL - FILL IN]'
for url in "$FLY_URL" "$CUSTOM_URL"; do
  curl -fsS "$url/health"
  curl -fsS "$url/api/meta"
done
```

A forward prediction and inverse search can be checked against each origin (the API may reject/skip inference if external assets are unavailable):

```bash
for base in "$FLY_URL" "$CUSTOM_URL"; do
  curl -fsS -X POST "$base/api/forward" -H 'content-type: application/json' \
    -d '{"shape_id":1,"lp":20,"wp":20,"use_ml_refine":true}'
  curl -fsS -X POST "$base/api/inverse" -H 'content-type: application/json' \
    -d '{"target_fr":3.5,"family":"Rectangular","priority":"Balanced Profile"}'
done
```

For browser assets, open DevTools Network on both hostnames and verify `/static/css/app.css`, `/static/js/app.js`, `/static/vendor/plotly.min.js`, `/static/fonts/*.woff2`, `/assets/antdesigner_favicon.png`, `/assets/antdesigner_logo_nav.png`, and `/assets/spu_logo_nav.png` return successfully. Verify the browser console has no asset or same-origin errors and that charts render. Confirm the custom domain certificate and Fly URL independently.
