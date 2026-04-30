# Benchmarking Agent Prometheus

Agent Prometheus should improve through measured behavior, not claims.

The benchmark runner in `tools/benchmark_consultant.py` checks deterministic parts of the consultant runtime without spending model tokens.

## What the benchmark measures

The current benchmark verifies:

- evidence collection completes for representative tasks
- expected project files are selected for relevant tasks
- Python compile diagnostics run during evidence collection
- repository summaries are produced
- weak-model JSON repair handles common malformed output
- runtime duration is recorded for comparison over time

## Run locally

From the repository root:

```bash
python tools/benchmark_consultant.py --workspace . --output benchmark-results/consultant_benchmark.json
```

Read the output:

```bash
cat benchmark-results/consultant_benchmark.json
```

## How to interpret results

Important fields:

```text
json_repair_passed          Should be true.
expected_path_hit_rate      Should be 1.0 for each current built-in case.
compile_error_count         Should be 0 unless the repo contains invalid Python.
mean_duration_seconds       Useful for tracking runtime speed over time.
selected_paths              Shows what evidence the consultant would receive.
```

## Why this exists

Prometheus is designed to work with weaker or cheaper models by doing deterministic work before asking the AI. This benchmark checks that deterministic layer.

It does not prove that a model will always produce a correct patch. It proves that the runtime is giving the model a better, safer, smaller evidence packet.

## Release rule

Before a release, run:

```bash
python -m compileall .
pytest -q
python tools/benchmark_consultant.py --workspace .
docker compose config
```

Commit benchmark result files only when intentionally publishing a release snapshot. For normal development, benchmark outputs can stay local.
