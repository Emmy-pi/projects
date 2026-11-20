"""Step 1: check and clean a donor export before any modeling.

Models built on messy data give confident but wrong answers, so this step
finds and fixes the common problems in CRM exports and reports every change.
"""
import re

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "donor_id", "constituent_type", "first_gift_date", "last_gift_date",
    "gift_count", "total_giving", "largest_gift", "events_attended_3yr",
    "email_open_rate", "email_click_rate",
]
OPTIONAL_COLUMNS = [
    "email", "gave_to_youth_causes", "foster_content_clicks", "attended_cause_event",
    "gave_last_campaign", "gave_to_foster_fund",
]
NEVER_GAVE_RECENCY_DAYS = 365 * 20

_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SLASH = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")


def parse_date(value, ambiguous_default="MDY"):
    """Parse one date string and say how confident the parse is.

    Returns (timestamp_or_NaT, status). Status is one of:
    ok, missing, corrected_day_month, ambiguous, unparseable.
    A date like 03/04/2025 could be March 4 or April 3; it is parsed using
    ``ambiguous_default`` ("MDY" or "DMY") and flagged for review.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)) or str(value).strip() == "":
        return pd.NaT, "missing"
    s = str(value).strip()
    if _ISO.match(s):
        ts = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
        return (ts, "ok") if not pd.isna(ts) else (pd.NaT, "unparseable")
    m = _SLASH.match(s)
    if not m:
        return pd.NaT, "unparseable"
    a, b, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if a > 12 and b <= 12:
        month, day, status = b, a, "corrected_day_month"
    elif b > 12 and a <= 12:
        month, day, status = a, b, "ok"
    elif a == b:
        month, day, status = a, b, "ok"
    else:
        if ambiguous_default.upper() == "DMY":
            month, day = b, a
        else:
            month, day = a, b
        status = "ambiguous"
    try:
        return pd.Timestamp(year=year, month=month, day=day), status
    except ValueError:
        return pd.NaT, "unparseable"


def clean(raw, as_of=None, ambiguous_default="MDY"):
    """Validate and clean a donor table.

    Returns (clean_df, report, issues) where ``report`` summarizes every change
    and ``issues`` lists record-level problems for staff to review in the CRM.
    """
    df = raw.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "The input file is missing required columns: " + ", ".join(missing)
            + ". See docs/data_dictionary.md for the expected layout."
        )
    report = {"rows_in": int(len(df))}
    issues = []

    before = len(df)
    df = df.drop_duplicates()
    report["exact_duplicate_rows_removed"] = int(before - len(df))

    before = len(df)
    df = df.drop_duplicates(subset="donor_id", keep="first")
    report["repeated_donor_ids_removed"] = int(before - len(df))

    report["possible_duplicate_donors"] = 0
    if "email" in df.columns:
        email = df["email"].astype(str).str.strip().str.lower()
        dup_mask = email.duplicated(keep=False) & df["email"].notna()
        groups = df[dup_mask].groupby(email[dup_mask])["donor_id"].apply(list)
        for ids in groups:
            for d in ids[1:]:
                issues.append({"donor_id": d, "issue": "possible_duplicate_donor",
                               "detail": f"same email as {ids[0]}; set aside until merged in the CRM"})
        set_aside = [d for ids in groups for d in ids[1:]]
        df = df[~df["donor_id"].isin(set_aside)]
        report["possible_duplicate_donors"] = len(set_aside)

    for col in ("gift_count", "total_giving", "largest_gift", "events_attended_3yr"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
        neg = df[col] < 0
        for d in df.loc[neg, "donor_id"]:
            issues.append({"donor_id": d, "issue": f"negative_{col}", "detail": "set to 0; check the source record"})
        df.loc[neg, col] = 0
        df[col] = df[col].fillna(0)
    report["negative_values_corrected"] = int(sum(1 for i in issues if i["issue"].startswith("negative_")))

    for col in ("email_open_rate", "email_click_rate"):
        df[col] = pd.to_numeric(df[col], errors="coerce").clip(0, 1)
        n_missing = int(df[col].isna().sum())
        df[col] = df[col].fillna(df[col].median())
        report[f"{col}_filled_with_median"] = n_missing

    status_counts = {}
    for col in ("first_gift_date", "last_gift_date"):
        parsed = df[col].apply(lambda v: parse_date(v, ambiguous_default))
        df[col] = pd.to_datetime(parsed.str[0])
        statuses = parsed.str[1]
        for st in ("corrected_day_month", "ambiguous", "unparseable"):
            mask = statuses == st
            status_counts[st] = status_counts.get(st, 0) + int(mask.sum())
            for d in df.loc[mask, "donor_id"]:
                issues.append({"donor_id": d, "issue": f"date_{st}", "detail": col})
    report["dates_corrected_from_day_month"] = status_counts.get("corrected_day_month", 0)
    report["dates_ambiguous_parsed_with_default"] = status_counts.get("ambiguous", 0)
    report["dates_unparseable"] = status_counts.get("unparseable", 0)

    reversed_dates = df["last_gift_date"] < df["first_gift_date"]
    for d in df.loc[reversed_dates, "donor_id"]:
        issues.append({"donor_id": d, "issue": "last_gift_before_first_gift", "detail": "dates swapped"})
    df.loc[reversed_dates, ["first_gift_date", "last_gift_date"]] = (
        df.loc[reversed_dates, ["last_gift_date", "first_gift_date"]].values)
    report["swapped_gift_dates"] = int(reversed_dates.sum())

    for col in ("gave_to_youth_causes", "foster_content_clicks", "attended_cause_event"):
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    as_of = pd.Timestamp(as_of) if as_of else (df["last_gift_date"].max() + pd.Timedelta(days=1))
    report["as_of_date"] = str(as_of.date())
    df["has_given"] = (df["gift_count"] > 0).astype(int)
    df["recency_days"] = (as_of - df["last_gift_date"]).dt.days
    df["recency_days"] = df["recency_days"].fillna(NEVER_GAVE_RECENCY_DAYS).clip(lower=0)
    df["tenure_years"] = ((as_of - df["first_gift_date"]).dt.days / 365.25).fillna(0).clip(lower=0)
    df["avg_gift"] = np.where(df["gift_count"] > 0, df["total_giving"] / df["gift_count"].replace(0, np.nan), 0.0)
    df["avg_gift"] = df["avg_gift"].fillna(0)
    df["constituent_type"] = df["constituent_type"].fillna("unknown").astype(str).str.strip().str.lower()

    report["rows_out"] = int(len(df))
    issues_df = pd.DataFrame(issues, columns=["donor_id", "issue", "detail"])
    return df.reset_index(drop=True), report, issues_df
