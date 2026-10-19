import numpy as np
import pandas as pd
import pytest

from src.pulls.trends import combine_geos, from_pytrends_frame, import_manual_csv


def frame(dates, target, anchor):
    return pd.DataFrame({"wispr flow": target, "anchor": anchor},
                        index=pd.DatetimeIndex(dates, name="date"))


D = pd.date_range("2025-09-07", periods=4, freq="W")


def test_zero_and_missing_stay_distinct():
    f = frame(D, [0, np.nan, 5, 10], [50, 60, 0, 40])
    out = from_pytrends_frame(f, "IN-KA", "wispr flow", "anchor")
    assert out.loc[out.date == D[0], "target"].iloc[0] == 0
    assert np.isnan(out.loc[out.date == D[1], "target"].iloc[0])
    assert out.loc[out.date == D[2], "anchor"].iloc[0] == 0


def test_combine_rejects_mismatched_date_ranges():
    a = from_pytrends_frame(frame(D, [1, 2, 3, 4], [1, 1, 1, 1]), "IN-KA", "wispr flow", "anchor")
    b = from_pytrends_frame(frame(D[:3], [1, 2, 3], [1, 1, 1]), "IN-MH", "wispr flow", "anchor")
    with pytest.raises(ValueError, match="date range"):
        combine_geos([a, b])


def test_combine_ok_when_aligned():
    a = from_pytrends_frame(frame(D, [1, 2, 3, 4], [1, 1, 1, 1]), "IN-KA", "wispr flow", "anchor")
    b = from_pytrends_frame(frame(D, [1, 2, 3, 4], [1, 1, 1, 1]), "IN-MH", "wispr flow", "anchor")
    assert set(combine_geos([a, b]).geo) == {"IN-KA", "IN-MH"}


def test_manual_csv_importer_logs_pull(tmp_path):
    csv = tmp_path / "multiTimeline.csv"
    csv.write_text("Category: All categories\n\nWeek,wispr flow: (Karnataka),voice typing: (Karnataka)\n"
                   "2025-09-07,0,50\n2025-09-14,<1,60\n2025-09-21,5,0\n")
    out = import_manual_csv(csv, "IN-KA", "wispr flow", "voice typing", log_dir=tmp_path)
    assert list(out.target) == [0, 0, 5]  # "<1" is Google's rounded-to-zero marker
    assert (tmp_path / "pull_log.csv").exists()


def test_partial_period_dropped():
    f = frame(D, [1, 2, 3, 0], [1, 1, 1, 0])
    f["isPartial"] = [False, False, False, True]
    assert len(from_pytrends_frame(f, "IN-KA", "wispr flow", "anchor")) == 3
