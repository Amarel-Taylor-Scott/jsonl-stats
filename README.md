# jsonl-stats

A tiny, dependency-free CLI that reports basic statistics over a [JSON Lines](https://jsonlines.org/) file.

## What it reports

- **record_count** — number of JSON objects in the file.
- **key_frequency** — how many records contain each key.
- **type_histograms** — per-key histogram of JSON value types (`str`, `int`, `float`, `bool`, `null`, `list`, `dict`).

## Requirements

- Python 3.7+
- No third-party packages.

## Usage

```bash
python3 jsonl_stats.py sample.jsonl
```

Example output:

```text
record_count: 4

key_frequency:
  name   4
  age    3
  active 2
  tags   2
  score  1

type_histograms:
  name: str: 4
  age: int: 2, null: 1
  active: bool: 2
  tags: list: 2
  score: float: 1
```

### JSON output

```bash
python3 jsonl_stats.py sample.jsonl --json
```

### Read from stdin / write to file

```bash
cat sample.jsonl | python3 jsonl_stats.py > report.txt
python3 jsonl_stats.py sample.jsonl -o report.txt
```

## Running tests

```bash
python3 -m unittest test_jsonl_stats.py
```

## License

MIT
