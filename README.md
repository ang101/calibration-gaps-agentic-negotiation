# Persona Calibration in Agentic Negotiation

This repository runs a two-phase pilot study of persona-conditioned buyer-seller negotiations using Claude via the Anthropic API.

## Files

- `run_experiment.py` — main experiment runner
- `analyze_results.py` — post-run analysis
- `.env.example` — example environment variable file

## Requirements

- Python 3.10+
- Anthropic API key
- Dependencies from `requirements.txt`

## Local setup

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your_key_here"
python run_experiment.py --dry-run
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY="your_key_here"
python run_experiment.py --dry-run
```

## Optional `.env` workflow

The script reads `ANTHROPIC_API_KEY` from the environment. It does **not** automatically load a `.env` file unless you add `python-dotenv` and call `load_dotenv()` in the script.

If you want to use a `.env` file locally:

1. Install dotenv:

```bash
pip install python-dotenv
```

2. Add near the top of `run_experiment.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

3. Copy the example file:

```bash
cp .env.example .env
```

4. Put your real key in `.env`.

Do **not** commit `.env` to version control.

## Run modes

### Dry run

Runs 1 pairing × 1 round × 2 phases to verify pipeline and model access.

```bash
python run_experiment.py --dry-run
```

### Full pilot

Runs the default 8-pairing, 20-round-per-phase pilot.

```bash
python run_experiment.py
```

### Resume after interruption

Resumes from `outputs/negotiation_log_partial.csv` if present.

```bash
python run_experiment.py --resume
```

### Skip auto-analysis

```bash
python run_experiment.py --skip-analysis
```

## Outputs

The script writes outputs under `outputs/`, including:

- `negotiation_log.csv`
- `negotiation_log_partial.csv`
- `round_summary.csv`
- `results_summary.txt`
- analysis outputs from `analyze_results.py`

## Submission guidance

For agentic or competition submission:

- pass `ANTHROPIC_API_KEY` as a platform secret or environment variable
- do **not** hardcode the key
- do **not** rely on a checked-in `.env`
- include `run_experiment.py`, `analyze_results.py`, `requirements.txt`, and this README

## Minimal submission command

```bash
python run_experiment.py
```

If the platform supports reruns after interruption:

```bash
python run_experiment.py --resume
```
