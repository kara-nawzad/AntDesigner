# Golden output fixture

`golden.json` is intentionally absent: no real prediction outputs were generated in this environment. On a trusted checkout with authentic local scaler files, `forward_model_v2_curve.keras`, and `antenna_data_cleaned.csv`, run:

```bash
python scripts/capture_golden.py
```

Review the generated outputs before committing `golden.json`. Never substitute hand-written or synthetic predictions for captured engine results.
