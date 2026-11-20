"""Write a plain-language summary of a pipeline run."""
from datetime import date

from . import __version__


def _table(df):
    cols = list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def write_report(path, *, input_file, fund, quality, profile, metrics, importance, affinity_check, tier_summary):
    q = quality
    m = metrics
    beats = m["model_top_decile_lift"] > m["baseline_top_decile_lift"]
    lines = [
        "# Scholarship Fundraising Toolkit: Run Report",
        "",
        f"- Toolkit version: {__version__}",
        f"- Run date: {date.today().isoformat()}",
        f"- Input file: `{input_file}`",
        f"- Fund: {'scholarship fund for students who have experienced foster care' if fund == 'foster_youth' else 'general scholarship fund'}",
        f"- Recency measured as of: {q['as_of_date']}",
        "",
        "## 1. Data quality",
        "",
        f"Read {q['rows_in']:,} records and kept {q['rows_out']:,}. Changes made:",
        "",
        f"- Exact duplicate rows removed: {q['exact_duplicate_rows_removed']}",
        f"- Repeated donor IDs removed: {q['repeated_donor_ids_removed']}",
        f"- Possible duplicate donors (same email, different ID) set aside until staff merge them: {q['possible_duplicate_donors']}",
        f"- Negative amounts corrected to 0: {q['negative_values_corrected']}",
        f"- Dates corrected from day/month order: {q['dates_corrected_from_day_month']}",
        f"- Ambiguous dates parsed with the default order and flagged: {q['dates_ambiguous_parsed_with_default']}",
        f"- Unreadable dates: {q['dates_unparseable']}",
        f"- Gift dates swapped because the last gift preceded the first: {q['swapped_gift_dates']}",
        f"- Missing email open rates filled with the median: {q['email_open_rate_filled_with_median']}",
        "",
        "Every record-level issue is listed in `data_quality_issues.csv` so it can be fixed in the CRM.",
        "",
        "## 2. Donor segments",
        "",
        _table(profile),
        "",
        "## 3. Likelihood-of-giving model",
        "",
        f"Trained on {m['training_donors']:,} donors and tested on {m['test_donors']:,} donors the model did not see. "
        f"Overall response rate in the last campaign: {m['response_rate']:.1%}.",
        "",
        "| Measure | Model | Rule of thumb (most recent donors first) |",
        "|---|---|---|",
        f"| AUC (0.5 = random, 1.0 = perfect) | {m['model_auc']} | {m['baseline_auc']} |",
        f"| Response rate in the top 10% | {m['model_top_decile_response_rate']:.1%} | {m['baseline_top_decile_response_rate']:.1%} |",
        f"| Lift in the top 10% | {m['model_top_decile_lift']}x | {m['baseline_top_decile_lift']}x |",
        "",
        ("The model ranks donors better than the rule of thumb on this data."
         if beats else
         "On this data the model does not beat the rule of thumb. Do not rely on it until it does."),
        "",
        "Most influential inputs:",
        "",
        _table(importance.head(8).reset_index().rename(columns={"index": "input"})),
        "",
    ]
    if fund == "foster_youth":
        lines += ["## 4. Cause affinity check", ""]
        if affinity_check is not None:
            lines += [
                "How often donors in each affinity band gave to the foster youth fund in the last campaign. "
                "If the rate does not rise from the lowest band to the highest, adjust the weights in `affinity.py`.",
                "",
                _table(affinity_check),
                "",
            ]
        else:
            lines += ["No past fund gifts (`gave_to_foster_fund`) were provided, so the affinity score could not be checked.", ""]
    lines += [
        "## 5. Outreach plan",
        "",
        _table(tier_summary),
        "",
        "Expected value is likelihood of giving multiplied by expected gift size. It is a planning estimate, not a forecast.",
        "",
        "## Before acting on these results",
        "",
        "- Results on the synthetic sample data say nothing about real-world performance. Run the toolkit on your own data and check section 3.",
        "- Hold back a small random group from the new approach so you can measure the difference it makes.",
        "- Review the data quality issues before importing results into your CRM.",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
