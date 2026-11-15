# Searchable regional directory: tutorial source

Companion files for **“How I Turned Inconsistent CSV Records into a Searchable Regional Directory”** by Niko Ibáñez.

This is a reproducible teaching example based on a data-management problem associated with the New Mexico–Colorado Regional Marketing Guide. It is **not a verified extraction of the live site's implementation**. Names in the samples are illustrative and their example.org addresses are placeholders; do not publish them as current business listings.

## Requirements

- Python 3.10 or later
- A modern browser
- No external dependencies

## Run

```bash
python build.py
python -m unittest discover -s tests -v
python -m http.server 8000
```

Open http://localhost:8000. Stop the server with Ctrl+C.

Expected results: five output records from six sample CSV rows; six passing unit tests.

## Files

- `TUTORIAL.md` — full step-by-step article
- `build.py` — field normalization, URL handling, exact deduplication, JSON export
- `data/new_mexico.csv` and `data/regional_feed.csv` — sample inputs with incompatible headings
- `directory.json` — generated output
- `index.html`, `app.js` — searchable browser demo with accessible controls
- `tests/test_build.py` — unit tests
- `EDIT_NOTES.md` — editorial and factual corrections made to the first draft

The file named `regional_feed.csv` intentionally contains both New Mexico and Colorado entries. The filename describes its source, not the geography of every row.
