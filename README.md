# eval-score-bounds

An offline Python CLI that checks decimal score fixtures against inclusive declared bounds. It validates fixture shape and reports only a status, record count, and physical line numbers. It does not run an evaluator or judge quality, accuracy, or statistical significance.

Requires Python 3.10 or newer. Runtime uses only the standard library.

```console
python -m pip install .
eval-score-bounds examples/rows.jsonl examples/policy.json
```

Rows are UTF-8 JSON Lines objects with exactly `id` (a non-empty string) and `score` (a decimal string). IDs must be unique. The policy is one UTF-8 JSON object with exactly `min` and `max`, each a decimal string, with `min <= max`. Decimal spelling is ASCII `-?(0|[1-9][0-9]*)(\.[0-9]{1,6})?`; the absolute value may not exceed 1,000,000,000. Bounds are inclusive. Duplicate JSON keys and invalid UTF-8 are rejected.

Input errors return exit 2 and `{"status":"invalid_input"}`. Valid in-range and out-of-range results return 0 and 1. No source values, IDs, paths, or exception details appear in output. Memory use grows with the input size.

For contributors, install the optional test extra and run `python -m pytest`.
