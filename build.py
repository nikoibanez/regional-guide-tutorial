"""Convert two differently structured CSV exports to a small JSON directory."""
import csv
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent
SOURCES = [ROOT / "data/new_mexico.csv", ROOT / "data/regional_feed.csv"]
ALIASES = {
    "name": ("name", "business"),
    "city": ("city", "town"),
    "state": ("state", "region"),
    "category": ("category", "type"),
    "website": ("website", "url"),
}
STATES = {"nm": "NM", "new mexico": "NM", "co": "CO", "colorado": "CO"}
TRACKING_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def first(row, keys):
    """Get the first populated value among equivalent column names."""
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalized_text(value):
    return re.sub(r"\s+", " ", value.casefold().strip())


def normalized_url(value):
    if not value:
        return ""
    parts = urlsplit(value.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        return ""
    # Keep functional query arguments (e.g. ?page=2); discard common tracking keys.
    pairs = [
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_KEYS
    ]
    return urlunsplit((
        parts.scheme.lower(),
        parts.netloc.lower(),
        parts.path.rstrip("/"),
        urlencode(pairs),
        parts.fragment,
    ))


def normalize(row, source):
    record = {key: first(row, aliases) for key, aliases in ALIASES.items()}
    record["state"] = STATES.get(normalized_text(record["state"]), "")
    record["website"] = normalized_url(record["website"])
    record["source"] = source
    if not all(record[key] for key in ("name", "city", "state")):
        return None
    return record


def identity(record):
    # Exact location/name matches are less destructive than automatic fuzzy merges.
    return (normalized_text(record["name"]), normalized_text(record["city"]), record["state"])


def merge_records(paths):
    records = {}
    for path in paths:
        with path.open(newline="", encoding="utf-8-sig") as file:
            for line_number, raw in enumerate(csv.DictReader(file), start=2):
                record = normalize(raw, path.name)
                if record is None:
                    print(f"Skipping incomplete row: {path.name}:{line_number}")
                    continue
                key = identity(record)
                if key not in records:
                    record["sources"] = [record.pop("source")]
                    records[key] = record
                else:
                    existing = records[key]
                    if record["source"] not in existing["sources"]:
                        existing["sources"].append(record["source"])
                    for field in ("category", "website"):
                        if not existing[field] and record[field]:
                            existing[field] = record[field]
    return sorted(records.values(), key=lambda r: (r["state"], r["city"], r["name"]))


def main():
    result = merge_records(SOURCES)
    destination = ROOT / "directory.json"
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(result)} records to {destination.name}")


if __name__ == "__main__":
    main()
