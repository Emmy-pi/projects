"""Run the full pipeline: prepare, segment, score, and rank.

Examples:
    python run_pipeline.py --input data/sample_donors.csv --output-dir output
    python run_pipeline.py --input my_export.csv --fund general --as-of 2027-02-01
"""
import argparse
import os

import pandas as pd

from fundraising_toolkit import __version__
from fundraising_toolkit.affinity import cause_affinity, validate_affinity
from fundraising_toolkit.outreach import build_outreach_list, summarize_tiers
from fundraising_toolkit.prepare import clean
from fundraising_toolkit.propensity import train_and_score
from fundraising_toolkit.report import write_report
from fundraising_toolkit.segment import segment


def run(input_file, output_dir, fund="foster_youth", as_of=None, date_order="MDY", n_segments=5, seed=42):
    os.makedirs(output_dir, exist_ok=True)
    raw = pd.read_csv(input_file)

    df, quality, issues = clean(raw, as_of=as_of, ambiguous_default=date_order)
    df, profile = segment(df, n_segments=n_segments, seed=seed)
    df, metrics, importance = train_and_score(df, seed=seed)
    df["cause_affinity"] = cause_affinity(df)
    affinity_check = validate_affinity(df) if fund == "foster_youth" else None

    outreach = build_outreach_list(df, fund=fund)
    tier_summary = summarize_tiers(outreach)

    outreach.to_csv(os.path.join(output_dir, "outreach_list.csv"), index=False)
    profile.to_csv(os.path.join(output_dir, "segment_profiles.csv"), index=False)
    issues.to_csv(os.path.join(output_dir, "data_quality_issues.csv"), index=False)
    write_report(os.path.join(output_dir, "report.md"), input_file=input_file, fund=fund, quality=quality,
                 profile=profile, metrics=metrics, importance=importance,
                 affinity_check=affinity_check, tier_summary=tier_summary)
    return {"quality": quality, "metrics": metrics, "tiers": tier_summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, help="CSV export of donor records")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--fund", choices=["foster_youth", "general"], default="foster_youth")
    parser.add_argument("--as-of", default=None, help="Date to measure recency from (YYYY-MM-DD)")
    parser.add_argument("--date-order", choices=["MDY", "DMY"], default="MDY",
                        help="How to read dates like 03/04/2025 when the order is unclear")
    parser.add_argument("--segments", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print(f"Scholarship Fundraising Toolkit {__version__}")
    result = run(args.input, args.output_dir, args.fund, args.as_of, args.date_order, args.segments, args.seed)
    m = result["metrics"]
    print(f"Model AUC {m['model_auc']} vs. rule of thumb {m['baseline_auc']}; "
          f"top 10% lift {m['model_top_decile_lift']}x vs. {m['baseline_top_decile_lift']}x")
    print(f"Results written to {args.output_dir}/ (start with report.md)")


if __name__ == "__main__":
    main()
