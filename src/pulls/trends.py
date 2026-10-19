"""Google Trends pulls (rules 3, 4). Values are relative search interest, never installs.

Each request pulls [target, anchor] together so both share one normalisation. Zeros (Google
reports 0 or "<1") and missing values (NaN) are kept distinct.
"""
import io
import json
import time
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

from src.common.logs import append_pull
from src.pulls.reviews import with_retries

RAW = Path("data/raw")
COLS = ["date", "geo", "target", "anchor"]


def from_pytrends_frame(df, geo, target_q, anchor_q):
    if "isPartial" in df.columns:  # the current, incomplete period is not comparable
        df = df[~df["isPartial"].astype(bool)]
    out = pd.DataFrame({"date": pd.to_datetime(df.index), "geo": geo,
                        "target": df[target_q].astype(float).to_numpy(),
                        "anchor": df[anchor_q].astype(float).to_numpy()})
    return out[COLS].reset_index(drop=True)


def combine_geos(frames):
    ranges = {(f.date.min(), f.date.max(), len(f)) for f in frames}
    if len(ranges) != 1:
        raise ValueError(f"mismatched date range across geos: {sorted(ranges)}")
    return pd.concat(frames, ignore_index=True)


def import_manual_csv(path, geo, target_q, anchor_q, log_dir=Path("data/logs")):
    """Importer for a Google Trends 'multiTimeline.csv' export (target in column 2)."""
    text = Path(path).read_text()
    lines = text.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.split(",")[0] in ("Week", "Day", "Month"))
    df = pd.read_csv(io.StringIO("\n".join(lines[start:])), na_values=[""], keep_default_na=False)
    df = df.replace("<1", 0).replace("", np.nan)
    df = df.set_index(pd.to_datetime(df.iloc[:, 0]))
    df.index.name = "date"
    f = pd.DataFrame({target_q: pd.to_numeric(df.iloc[:, 1], errors="coerce"),
                      anchor_q: pd.to_numeric(df.iloc[:, 2], errors="coerce")}, index=df.index)
    out = from_pytrends_frame(f, geo, target_q, anchor_q)
    append_pull(f"trendscsv-{uuid.uuid4().hex[:6]}", "google-trends manual csv export", str(path),
                {"geo": geo, "target": target_q, "anchor": anchor_q}, path, rows=len(out),
                log_dir=log_dir)
    return out


def pull_trends(target_q, anchor_q, geos, timeframe, label):
    from pytrends.request import TrendReq

    frames = []
    for geo in geos:
        pid = f"trends-{label}-{geo}-{uuid.uuid4().hex[:6]}"

        def get(geo=geo):
            py = TrendReq(hl="en-US", tz=0, timeout=(10, 30))
            py.build_payload([target_q, anchor_q], timeframe=timeframe, geo=geo)
            df = py.interest_over_time()
            if df.empty:
                raise ValueError("empty trends frame")
            return df

        df = with_retries(pid, get, sleep=lambda s: time.sleep(10 * (s + 1)))
        RAW.mkdir(parents=True, exist_ok=True)
        path = RAW / f"{pid}.json"
        path.write_text(df.reset_index().to_json(orient="records", date_format="iso"))
        append_pull(pid, "pytrends (unofficial)", "interest_over_time",
                    {"q": [target_q, anchor_q], "geo": geo, "timeframe": timeframe},
                    path, rows=len(df))
        frames.append(from_pytrends_frame(df, geo, target_q, anchor_q))
        time.sleep(5)
    return combine_geos(frames)


def main():
    import sys

    target, anchor = sys.argv[1], sys.argv[2]
    geos = ["IN-KA", "IN-MH", "IN-DL", "IN-TN", "IN-TG"]
    out = pull_trends(target, anchor, geos, "2025-09-01 " + pd.Timestamp.now().strftime("%Y-%m-%d"),
                      target.replace(" ", "_"))
    name = f"data/interim/trends_{target.replace(' ', '_')}.csv"
    out.to_csv(name, index=False)
    print(json.dumps({"rows": len(out), "file": name}))


if __name__ == "__main__":
    main()
