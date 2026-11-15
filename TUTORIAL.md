# How I Turned Inconsistent CSV Records into a Searchable Regional Directory

**Niko Ibáñez**  
*Python 3.10+, CSV, JSON, vanilla JavaScript, Netlify*

One spreadsheet says `business`. Another says `name`. Somewhere a third party has decided that `town` is better than `city`, and the same coffee shop appears twice because its website has acquired an extra slash. The records look fine until you try to search them together.

I've worked on that problem through the [New Mexico–Colorado Regional Marketing Guide](https://newmexicocoloradoguide.netlify.app/), a regional information project spanning Colfax County, New Mexico, and Las Animas and Huerfano counties in Colorado. It brings together listings maintained by separate organizations. Those organizations have their own naming conventions, publication schedules, and ideas about what belongs in a column called *type*.

The example below reproduces one **data-processing problem** from that work: accepting two differently formatted CSV exports, keeping track of their sources, combining exact duplicates, and putting the cleaned records into a browser-searchable directory. It's a small, runnable reconstruction. I haven't verified that the deployed guide uses this particular code, and the sample files aren't exports from the live site.

You can complete the example with Python and a browser. No third-party packages, database server, or JavaScript framework.

## Step 1: Make a place for the mess

Create a directory with these files. The [companion source files](./README.md) contain the completed versions; `directory.json` will be generated in Step 5.

```text
regional-guide-tutorial/
├── data/
│   ├── new_mexico.csv
│   └── regional_feed.csv
├── tests/
│   └── test_build.py
├── build.py
├── app.js
├── index.html
└── directory.json       # generated file
```

Here is the first sample, `data/new_mexico.csv`:

```csv
name,city,state,category,website
Sage Coffee,Raton,NM,Cafe,https://example.org/sage
Old Pass Gallery,Raton,NM,Arts,https://example.org/old-pass
High Plains Library,Raton,NM,Community,https://example.org/library
```

The second file, `data/regional_feed.csv`, has different headings and one overlapping entry:

```csv
business,town,region,type,url
Sage Coffee,Raton,New Mexico,Coffee,https://example.org/sage/
Trinidad Community Studio,Trinidad,Colorado,Arts,https://example.org/studio
Walsenburg Makerspace,Walsenburg,CO,Community,https://example.org/makerspace
```

These are **illustrative records**, some using familiar local names, with placeholder URLs. They haven't been checked as current listings. That's fine for a programming example; it's a terrible basis for publishing a business directory.

Notice that `regional_feed.csv` includes a New Mexico record. Source filenames describe where the data *came from*, not necessarily where every listing is located. If we named the file `colorado.csv`, the first test would already be lying to us.

## Step 2: Give the columns one set of names

In `build.py`, start with a mapping between incoming headings and the fields we'll use internally:

```python
ALIASES = {
    "name": ("name", "business"),
    "city": ("city", "town"),
    "state": ("state", "region"),
    "category": ("category", "type"),
    "website": ("website", "url"),
}


def first(row, keys):
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""
```

`first()` checks each accepted column heading in order and returns the first nonempty value. It also handles missing values without raising an error. There are plenty of legitimate reasons for a field to be blank; Python doesn't need to make it dramatic.

The column mapping belongs at the import boundary. That way the browser receives `name` whether the original source called it `name`, `business`, or, after we add another mapping, something else.

## Step 3: Clean the values without damaging the links

Column headings aren't the only problem. We also have `NM` and `New Mexico`, and URLs that differ by a trailing slash or a tracking parameter.

For the states in this project, a small lookup table is enough:

```python
STATES = {
    "nm": "NM",
    "new mexico": "NM",
    "co": "CO",
    "colorado": "CO",
}
```

For web addresses, the cleanup needs more care. A first attempt might remove *every* query parameter after `?`. That breaks pages using `?page=2`, `?id=123`, or other arguments to determine what gets displayed. This version removes familiar marketing parameters and preserves the rest:

```python
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def normalized_url(value):
    if not value:
        return ""
    parts = urlsplit(value.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        return ""

    pairs = [
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
        and key.lower() not in TRACKING_KEYS
    ]

    return urlunsplit((
        parts.scheme.lower(),
        parts.netloc.lower(),
        parts.path.rstrip("/"),
        urlencode(pairs),
        parts.fragment,
    ))
```

For instance, `https://Example.org/a/?page=2&utm_source=feed` becomes `https://example.org/a?page=2`. The page selector survives. The marketing tag doesn't.

The function also refuses non-HTTP addresses. That matters later, when a browser turns imported website fields into links. For more complicated source systems, especially those using signed URLs or unusual routing, URL normalization needs source-specific rules and tests.

## Step 4: Decide what actually counts as a duplicate

I'm deliberately conservative here. If two entries have the same normalized name, city, and state, we treat them as one listing. Similar spelling alone isn't enough. A mistaken merge would erase a distinct organization, and a directory with a thousand entries can hide that error for a long while.

```python
import re


def normalized_text(value):
    return re.sub(r"\s+", " ", value.casefold().strip())


def identity(record):
    return (
        normalized_text(record["name"]),
        normalized_text(record["city"]),
        record["state"],
    )
```

Both Sage Coffee rows produce the key `("sage coffee", "raton", "NM")`.

In `merge_records()`, each row passes through `normalize()`, which applies the aliases, standardizes the state, cleans the URL, and rejects rows missing a name, city, or recognized state. The merge then keeps the first record with each key. Later matches contribute their source filenames and can fill fields that were originally empty.

```python
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
```

The sample has a small disagreement: one source calls Sage Coffee a `Cafe`, the other calls it `Coffee`. This code keeps the first populated category. It does **not** pretend to have resolved the disagreement. For a larger directory, I'd collect those conflicts in a review report rather than allow the source order to decide quietly.

The trade-off goes the other direction, too. `Sage Coffee` and `Sage Coffees` won't merge automatically. They can be flagged for human review after the exact matches are handled.

## Step 5: Write JSON and check the count

The full `build.py` uses `csv.DictReader` to read the two files, then writes an indented JSON array. Run it from the directory containing `build.py`:

```bash
python build.py
```

Expected output:

```text
Wrote 5 records to directory.json
```

Six input rows became five records. The duplicated listing retains both contributing filenames in its `sources` array. Output is sorted by state, city, and organization name, making the generated file easier to inspect in a diff.

If a row has no name, city, or recognized state, the script prints its source filename and CSV line number before skipping it. That is a basic safeguard, not a complete validation system. A production pipeline should collect rejected rows and fail the build when required fields disappear across a source.

## Step 6: Let the browser search the cleaned file

The HTML page has a search input, a state dropdown, a count, and a list for results. `app.js` fetches the generated JSON:

```javascript
async function start() {
  try {
    const response = await fetch('./directory.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    records = await response.json();
    render();
  } catch (error) {
    count.textContent =
      'Could not load directory.json. Run build.py and serve over HTTP.';
    console.error(error);
  }
}
```

Once the records are loaded, search checks three fields and the selected state. The controls work independently, so a search for `Arts` within Colorado will not return art listings from New Mexico.

```javascript
const matches = records.filter((item) => {
  const searchable =
    `${item.name} ${item.city} ${item.category}`.toLocaleLowerCase();

  return (!state.value || item.state === state.value)
    && searchable.includes(search);
});
```

For rendering, I use `document.createElement()` and `textContent` instead of inserting source fields into `innerHTML`. A business name should stay a business name even when it contains characters that resemble markup. `index.html` also includes visible labels for the controls, a focus outline for keyboard users, and an `aria-live` count so changes to the results are announced to assistive technology.

The frontend is intentionally plain. With five records, the ability to find the right one matters more than elaborate animation. With fifteen hundred, it matters considerably more.

## Step 7: Run the tests before publishing

The companion project includes six unit tests. Run them with:

```bash
python -m unittest discover -s tests -v
```

They check column aliases, state normalization, exact-duplicate merging, required fields, query-string preservation, whitespace/case matching, and handling null-valued input fields. The source data should produce five records, with the duplicated entry retaining both source filenames.

For an actual import pipeline, I'd add fixture files for corrupted rows, changed headers, Unicode names, and contradictory records from separate sources. Import failures have a habit of looking like ordinary empty results unless you make them visible.

## Step 8: Preview it over HTTP

Run a local server from the project folder:

```bash
python -m http.server 8000
```

Open `http://localhost:8000`. Try `Raton`, switch to `Colorado`, then search `Arts`. The results and count should change with each input.

Avoid opening `index.html` directly with a `file://` URL; browsers may restrict its request for `directory.json`. That can look like a JavaScript bug when it's actually a local-file access restriction.

## Step 9: Deploy the static site

The browser only needs three files after the Python step has run:

```text
index.html
app.js
directory.json
```

Upload them together to a Netlify site, or connect a Git repository and configure the build to run `python build.py` before publishing the output directory. If you work from a repository subfolder, point Netlify at that folder explicitly. No backend is needed to serve this demonstration.

I wouldn't automate publication of unreviewed imports yet. The next job is a validation report: which rows were rejected, which categories disagree, which websites are malformed, and which near-duplicates need an actual person to look at them. That person will eventually want a filename and line number. We may as well keep both from the start.
