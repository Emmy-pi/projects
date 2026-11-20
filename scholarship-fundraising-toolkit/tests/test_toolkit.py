import os
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "data"))

from fundraising_toolkit.prepare import clean, parse_date  # noqa: E402
from generate_sample_data import generate  # noqa: E402
from run_pipeline import run  # noqa: E402


@pytest.mark.parametrize("value,expected,status", [
    ("2025-03-04", "2025-03-04", "ok"),
    ("12/25/2025", "2025-12-25", "ok"),
    ("25/12/2025", "2025-12-25", "corrected_day_month"),
    ("03/04/2025", "2025-03-04", "ambiguous"),
    ("05/05/2025", "2025-05-05", "ok"),
])
def test_parse_date(value, expected, status):
    ts, st = parse_date(value)
    assert st == status
    assert ts == pd.Timestamp(expected)


def test_parse_date_handles_missing_and_bad_values():
    assert parse_date(None)[1] == "missing"
    assert parse_date("")[1] == "missing"
    assert parse_date("not a date")[1] == "unparseable"
    assert parse_date("13/13/2025")[1] == "unparseable"


def test_ambiguous_dates_follow_the_chosen_order():
    ts, st = parse_date("03/04/2025", ambiguous_default="DMY")
    assert st == "ambiguous" and ts == pd.Timestamp("2025-04-03")


def test_clean_removes_duplicates_and_fixes_negatives():
    raw = generate(rows=400, seed=1)
    df, report, issues = clean(raw)
    assert df["donor_id"].is_unique
    assert df["email"].str.lower().is_unique
    assert (df["total_giving"] >= 0).all()
    assert report["exact_duplicate_rows_removed"] > 0
    assert report["possible_duplicate_donors"] > 0
    assert not issues.empty


def test_clean_reports_missing_columns():
    with pytest.raises(ValueError, match="missing required columns"):
        clean(pd.DataFrame({"donor_id": ["D1"]}))


def test_full_pipeline(tmp_path):
    data = tmp_path / "donors.csv"
    generate(rows=1500, seed=7).to_csv(data, index=False)
    result = run(str(data), str(tmp_path / "out"))
    for name in ("report.md", "outreach_list.csv", "segment_profiles.csv", "data_quality_issues.csv"):
        assert (tmp_path / "out" / name).exists()
    assert result["metrics"]["model_auc"] > 0.6
    outreach = pd.read_csv(tmp_path / "out" / "outreach_list.csv")
    assert set(outreach["tier"]) == {"Tier 1", "Tier 2", "Tier 3", "Tier 4"}
    assert outreach["donor_id"].is_unique
    assert "email" not in outreach.columns
