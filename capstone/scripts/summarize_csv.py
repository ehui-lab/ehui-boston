"""Summarise a CSV file: shape, column types, missing data, duplicates and distributions.

Usage:
    python scripts/summarize_csv.py data/DisneylandReviews.csv
    python scripts/summarize_csv.py data/DisneylandReviews.csv --out data/DisneylandReviews_summary.md

Output is Markdown, so it can be pasted straight into notes or the milestone draft.
Missing data is counted two ways: real nulls, and "sentinel" strings such as
"missing" or "unknown" that pandas does not treat as null.
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

SENTINELS = {"", "missing", "unknown", "n/a", "na", "nan", "null", "none", "?", "-"}
TEXT_MIN_MEAN_LEN = 50  # string columns with a longer mean length are treated as free text
MAX_CATEGORY_VALUES = 15  # numeric columns with at most this many values get a value table
ID_COLUMN = re.compile(r"(^|_)id($|_)", re.IGNORECASE)
NUMERIC_JUNK = re.compile(r"[$,%\s]")
SPACED_WORD = re.compile(r"[A-Za-z] {2,}[A-Za-z]")  # e.g. "wasn   t": an apostrophe lost to bad encoding


def load(path, encoding):
    """Read the CSV, trying UTF-8 then Latin-1 unless an encoding is given."""
    if encoding:
        return pd.read_csv(path, encoding=encoding), encoding
    try:
        return pd.read_csv(path, encoding="utf-8"), "utf-8"
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1"), "latin-1 (utf-8 failed)"


def table(header, rows):
    """Render a Markdown table."""
    def cell(v):
        return str(v).replace("|", "\\|").replace("\n", " ")[:60]
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows]
    return "\n".join(lines)


def is_string(s):
    return pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s)


def is_text(s):
    return is_string(s) and s.dropna().astype(str).str.len().mean() >= TEXT_MIN_MEAN_LEN


def sentinel_count(s):
    if not is_string(s):
        return 0
    return int(s.dropna().astype(str).str.strip().str.lower().isin(SENTINELS).sum())


def numeric_stored_as_text(s):
    if not is_string(s) or is_text(s):
        return False
    values = s.dropna().astype(str).str.replace(NUMERIC_JUNK, "", regex=True)
    return len(values) > 0 and pd.to_numeric(values, errors="coerce").notna().mean() > 0.9


def overview(df, path, encoding):
    size_mb = Path(path).stat().st_size / 1e6
    return "## Overview\n\n" + table(
        ["Item", "Value"],
        [
            ["File", Path(path).name],
            ["Size", f"{size_mb:.1f} MB"],
            ["Encoding used", encoding],
            ["Rows", f"{len(df):,}"],
            ["Columns", len(df.columns)],
        ],
    )


def columns(df):
    rows = []
    for c in df.columns:
        s = df[c]
        flags = []
        if ID_COLUMN.search(c):
            flags.append("id-like")
        if is_text(s):
            flags.append("free text")
        if numeric_stored_as_text(s):
            flags.append("numeric stored as text")
        nulls = int(s.isna().sum())
        rows.append([
            c, s.dtype, f"{len(s) - nulls:,}", f"{nulls:,} ({nulls / len(s):.1%})",
            f"{sentinel_count(s):,}", f"{s.nunique():,}", ", ".join(flags),
        ])
    return "## Columns\n\n" + table(
        ["Column", "Type", "Non-null", "Null", "Sentinel missing", "Unique", "Flags"], rows
    ) + (
        "\n\n*Sentinel missing* counts strings like \"missing\" or \"unknown\" that are not real nulls."
    )


def duplicates(df):
    id_cols = [c for c in df.columns if ID_COLUMN.search(c)]
    rows = [["Fully duplicated rows", int(df.duplicated().sum())]]
    for c in id_cols:
        rows.append([f"Duplicate values in {c}", int(df[c].duplicated().sum())])
    if id_cols:
        rows.append([f"Duplicated rows ignoring {', '.join(id_cols)}",
                     int(df.drop(columns=id_cols).duplicated().sum())])
    for c in df.columns:
        if is_text(df[c]):
            rows.append([f"Duplicate values in {c}", int(df[c].dropna().duplicated().sum())])
    return "## Duplicates\n\n" + table(["Check", "Count"], rows)


def numeric_summary(df):
    num = df.select_dtypes("number")
    if num.empty:
        return ""
    d = num.describe().T
    rows = [[c, f"{r['mean']:,.2f}", f"{r['std']:,.2f}", f"{r['min']:,.2f}", f"{r['25%']:,.2f}",
             f"{r['50%']:,.2f}", f"{r['75%']:,.2f}", f"{r['max']:,.2f}"] for c, r in d.iterrows()]
    return "## Numeric columns\n\n" + table(
        ["Column", "Mean", "Std", "Min", "25%", "Median", "75%", "Max"], rows
    )


def value_tables(df, top):
    parts = []
    for c in df.columns:
        s = df[c]
        if is_text(s) or ID_COLUMN.search(c):
            continue
        n = s.nunique()
        numeric = pd.api.types.is_numeric_dtype(s)
        if numeric and not 1 < n <= MAX_CATEGORY_VALUES:
            continue
        if not numeric and not 1 < n < len(s) / 2:
            continue
        counts = s.value_counts(dropna=False)
        shown = counts.head(top) if not numeric else counts.sort_index()
        rows = [[v, f"{k:,}", f"{k / len(s):.1%}"] for v, k in shown.items()]
        note = f" (top {top} of {n:,})" if len(shown) < n else ""
        parts.append(f"### {c}{note}\n\n" + table(["Value", "Count", "Share"], rows))
    return "## Value counts\n\n" + "\n\n".join(parts) if parts else ""


def text_summary(df):
    parts = []
    for c in df.columns:
        s = df[c]
        if not is_text(s):
            continue
        text = s.dropna().astype(str)
        chars, words = text.str.len(), text.str.split().str.len()
        rows = [
            ["Characters (median / mean / max)", f"{chars.median():,.0f} / {chars.mean():,.0f} / {chars.max():,}"],
            ["Words (median / mean / max)", f"{words.median():,.0f} / {words.mean():,.0f} / {words.max():,}"],
            ["Rows with non-ASCII characters", f"{int(text.str.contains(r'[^\x00-\x7f]').sum()):,}"],
            ["Rows with replacement character (U+FFFD)", f"{int(text.str.contains(chr(0xFFFD)).sum()):,}"],
            ["Rows with spaces inside a word (likely lost apostrophes)", f"{int(text.str.contains(SPACED_WORD).sum()):,}"],
        ]
        parts.append(f"### {c}\n\n" + table(["Check", "Result"], rows))
    return "## Free-text columns\n\n" + "\n\n".join(parts) if parts else ""


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", help="CSV file to summarise")
    parser.add_argument("--encoding", help="file encoding (default: try utf-8, then latin-1)")
    parser.add_argument("--top", type=int, default=10, help="values to show per categorical column")
    parser.add_argument("--out", help="also write the report to this Markdown file")
    args = parser.parse_args()

    df, encoding = load(args.path, args.encoding)
    sections = [
        f"# Summary of {Path(args.path).name}",
        overview(df, args.path, encoding),
        columns(df),
        duplicates(df),
        numeric_summary(df),
        value_tables(df, args.top),
        text_summary(df),
    ]
    report = "\n\n".join(s for s in sections if s) + "\n"

    sys.stdout.reconfigure(encoding="utf-8")
    print(report)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
