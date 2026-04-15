# suki-helper

Desktop PDF search application with:

- Python desktop UI
- per-PDF SQLite index databases
- whitespace-insensitive 2-gram search
- order-aware ranking

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Run

```bash
source .venv/bin/activate
python -m suki_helper.app.main
```

## Status

This repository is in early MVP scaffolding.
