"""Generate a synthetic donor file for trying the toolkit.

Every record is fake. No real donor, student, or institution is represented.
The file deliberately includes the kinds of problems real CRM exports have
(duplicate records, mixed date formats, missing values, entry errors) so the
data preparation step has something to fix.

Usage:
    python data/generate_sample_data.py --rows 5000 --out data/sample_donors.csv
"""
import argparse

import numpy as np
import pandas as pd

CONSTITUENT_TYPES = ["alumni", "parent", "friend", "faculty_staff", "organization"]
TYPE_PROBS = [0.45, 0.15, 0.25, 0.08, 0.07]


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def generate(rows=5000, seed=42, campaign_start="2026-02-01"):
    rng = np.random.default_rng(seed)
    start = pd.Timestamp(campaign_start)
    n = rows

    ctype = rng.choice(CONSTITUENT_TYPES, size=n, p=TYPE_PROBS)
    engagement = rng.beta(2, 5, n)          # hidden: how connected the donor feels
    affinity = rng.beta(1.5, 5, n)          # hidden: how much the donor cares about foster youth

    # Giving history as of the start of the campaign being modeled.
    gift_count = rng.poisson(0.4 + 9 * engagement)
    has_given = gift_count > 0
    tenure_days = rng.integers(90, 365 * 15, n)
    recency = np.where(has_given, (rng.beta(1.3, 2 + 6 * engagement, n) * tenure_days).astype(int) + 1, 0)

    typical_gift = rng.lognormal(mean=4.3, sigma=0.9, size=n)
    typical_gift[ctype == "organization"] *= 6
    avg_gift = np.where(has_given, typical_gift * rng.uniform(0.6, 1.4, n), 0.0)
    total_giving = np.round(gift_count * avg_gift, 2)
    largest_gift = np.round(np.where(has_given, avg_gift * rng.uniform(1.0, 3.0, n), 0.0), 2)

    events = rng.poisson(3.5 * engagement)
    open_rate = np.clip(rng.beta(2, 4, n) * 0.6 + engagement * 0.5, 0, 1)
    click_rate = np.clip(open_rate * rng.beta(2, 8, n) * (0.5 + engagement), 0, 1)

    youth_causes = (rng.random(n) < 0.06 + 0.55 * affinity).astype(int)
    foster_clicks = rng.poisson(0.2 + 4.5 * affinity * (0.4 + engagement))
    cause_event = (rng.random(n) < 0.03 + 0.6 * affinity * engagement).astype(int)

    # Outcomes of the most recent campaign (used to train and check the models).
    z = (-2.6 + 2.6 * engagement + 1.1 * (has_given & (recency < 400)) + 0.06 * np.minimum(gift_count, 15)
         + 0.25 * events + 2.0 * click_rate + 0.6 * cause_event + rng.normal(0, 0.6, n))
    gave_last = (rng.random(n) < _sigmoid(z)).astype(int)
    gave_foster = (gave_last & (rng.random(n) < _sigmoid(-2.2 + 5.0 * affinity))).astype(int)

    first_gift = pd.Series(start - pd.to_timedelta(tenure_days, unit="D"))
    last_gift = pd.Series(start - pd.to_timedelta(recency, unit="D"))
    first_gift[~has_given] = pd.NaT
    last_gift[~has_given] = pd.NaT

    df = pd.DataFrame({
        "donor_id": [f"D{i:05d}" for i in range(1, n + 1)],
        "email": [f"donor{i:05d}@example.org" for i in range(1, n + 1)],
        "constituent_type": ctype,
        "first_gift_date": first_gift.dt.strftime("%Y-%m-%d"),
        "last_gift_date": last_gift.dt.strftime("%Y-%m-%d"),
        "gift_count": gift_count,
        "total_giving": total_giving,
        "largest_gift": largest_gift,
        "events_attended_3yr": events,
        "email_open_rate": np.round(open_rate, 3),
        "email_click_rate": np.round(click_rate, 3),
        "gave_to_youth_causes": youth_causes,
        "foster_content_clicks": foster_clicks,
        "attended_cause_event": cause_event,
        "gave_last_campaign": gave_last,
        "gave_to_foster_fund": gave_foster,
    })

    # Inject realistic data problems.
    idx = rng.permutation(n)
    k = lambda share: int(n * share)  # noqa: E731
    mdy = idx[: k(0.10)]
    dmy = idx[k(0.10): k(0.13)]
    for col in ("first_gift_date", "last_gift_date"):
        d = pd.to_datetime(df[col], errors="coerce")
        df.loc[mdy, col] = d[mdy].dt.strftime("%m/%d/%Y")   # US style
        df.loc[dmy, col] = d[dmy].dt.strftime("%d/%m/%Y")   # imported from a vendor using day/month
    df.loc[idx[k(0.13): k(0.15)], "email_open_rate"] = np.nan
    neg = idx[k(0.15): k(0.153)]
    df.loc[neg, "total_giving"] = -df.loc[neg, "total_giving"]

    exact_dupes = df.iloc[idx[k(0.20): k(0.22)]]
    second_ids = df.iloc[idx[k(0.22): k(0.23)]].copy()
    second_ids["donor_id"] = [f"D{n + i + 1:05d}" for i in range(len(second_ids))]
    df = pd.concat([df, exact_dupes, second_ids], ignore_index=True)
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rows", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="data/sample_donors.csv")
    args = parser.parse_args()
    df = generate(args.rows, args.seed)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df):,} synthetic records to {args.out}")


if __name__ == "__main__":
    main()
