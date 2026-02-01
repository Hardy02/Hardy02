# Mini PokerTracker

A local, production-minded "mini PokerTracker" that computes core HUD statistics from **hand histories you already possess and are permitted to analyze**. It does **not** scrape, intercept traffic, or infer opponent identities.

## Safe design

- **Hero-only tracking by default**.
- **Villain stats only if IDs are stable and permitted**, and you explicitly enable them.
- **Post-session analytics**: upload hand history text files stored on your machine.

See [`docs/feasibility.md`](docs/feasibility.md) for the feasibility note and rule-safe design decision.

## Folder structure

```
app/
  main.py
  db.py
  models.py
  stats.py
  parser/
    tokenizer.py
    hand_parser.py
  templates/
    index.html
    definitions.html
  static/
    style.css

data/
  sample_hands.txt

docs/
  feasibility.md

tests/
  test_stats.py
```

## Installation

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   uvicorn app.main:app --reload
   ```

4. Open `http://localhost:8000` and upload a hand history file.

## Validation harness

Sample hands live in `data/sample_hands.txt`.

Run tests:

```bash
pytest
```

## Supported formats

- PokerStars-style text hand histories (baseline).
- Generic hand text with "Hand #" headers, "*** FLOP ***" markers, and action lines like `Player: raises $X to $Y`.

## Ethics & compliance

This tool only parses hand histories you already have and are permitted to analyze.
It intentionally avoids any real-time HUD tracking on anonymous tables and does not persist or infer opponent identities across sessions.
