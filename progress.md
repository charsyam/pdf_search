# Progress Log

## Current Baseline

Last stable commit before this log update:

- `95949bb` - `Initialize project scaffolding and search foundation`

Current working state after that commit:

- search service implemented
- order-aware ranking implemented
- snippet extraction implemented
- document registration and per-PDF indexing connected to the UI
- empty-state-first startup flow implemented
- `File -> Add PDF` menu and add button implemented

## Implemented So Far

### Foundation

- Python project scaffold created
- `.venv`-based workflow established
- PySide6 app shell added
- Git repository initialized

### Storage

- `catalog.db` bootstrap implemented
- per-PDF index DB bootstrap implemented
- `index_key` generation implemented
- page and gram posting persistence implemented

### Search Core

- PDF page text extraction implemented with `PyMuPDF`
- whitespace-insensitive normalization implemented
- normalized-to-original offset mapping implemented
- 2-gram tokenization and page posting generation implemented
- selected-PDF-only search implemented
- exact compact-match verification implemented
- order-aware ranking implemented
- snippet/context extraction implemented

### UI

- startup empty state implemented
- PDF add flow implemented
- indexed PDF selection implemented
- Enter-based search connected
- result list connected
- result click shows page text in the right pane as a temporary placeholder

## Verified State

Verification command:

```bash
source .venv/bin/activate
PYTHONPATH=src pytest -q
```

Latest verified result at the time of writing:

- `13 passed`

App launch command:

```bash
cd /Users/daemyung/develop/charsyam/suki-helper
source .venv/bin/activate
PYTHONPATH=src python -m suki_helper.app.main
```

## Known Gaps

- right pane does not yet render high-resolution page images
- left result list does not yet show low-resolution thumbnails
- indexing is currently synchronous
- rendering and indexing workers are not yet in place
- performance tuning and Windows validation are still pending

## Next Recommended Start Point

Resume from:

1. implement a PDF page renderer using `PyMuPDF`
2. replace the right-pane text placeholder with rendered page images
3. add thumbnail generation for result rows
4. move indexing and rendering to background workers

## Rule For Future Updates

When a feature phase is completed:

- update `work_plan.md` status for the relevant phase
- append or revise `progress.md` so the next session can resume from the new baseline
