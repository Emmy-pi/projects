"""Step 4: turn scores into a ranked outreach list a small office can act on.

Staff time is the scarcest resource in a small advancement office, so the
list puts personal contact where it is most likely to matter and automates
the rest. Tier sizes and actions can be changed to match staff capacity.
"""
import numpy as np
import pandas as pd

TIERS = [  # (share of the list, tier name, recommended action)
    (0.05, "Tier 1", "Personal contact: call, visit, or handwritten note from leadership"),
    (0.15, "Tier 2", "Personalized email from a named staff member, with a follow-up call"),
    (0.30, "Tier 3", "Segment-specific email and text message sequence"),
    (0.50, "Tier 4", "General appeal through the standard campaign mailing"),
]
LAPSED_DAYS = 540


def build_outreach_list(df, fund="foster_youth", tiers=None):
    """Rank donors by expected value and assign each a tier and action.

    For the foster youth fund, likelihood of giving is weighted by cause
    affinity so that donors who care about this cause rise in the list.
    """
    tiers = tiers or TIERS
    out = df.copy()
    if fund == "foster_youth":
        out["priority_score"] = out["propensity"] * (0.5 + 0.5 * out["cause_affinity"])
    else:
        out["priority_score"] = out["propensity"]

    donor_median = out.loc[out["has_given"] == 1, "avg_gift"].median()
    out["expected_gift"] = np.where(out["has_given"] == 1, out["avg_gift"], donor_median * 0.5)
    out["expected_value"] = (out["priority_score"] * out["expected_gift"]).round(2)
    out = out.sort_values("expected_value", ascending=False).reset_index(drop=True)
    out["rank"] = np.arange(1, len(out) + 1)

    cut_points = np.cumsum([t[0] for t in tiers])
    position = out["rank"] / len(out)
    tier_idx = np.searchsorted(cut_points, position, side="left").clip(max=len(tiers) - 1)
    out["tier"] = [tiers[i][1] for i in tier_idx]
    out["recommended_action"] = [tiers[i][2] for i in tier_idx]

    likely = out["propensity"] >= out["propensity"].quantile(0.8)
    out["renewal_flag"] = np.where((out["has_given"] == 1) & (out["recency_days"] > LAPSED_DAYS) & likely,
                                   "Lapsed but likely to return: use a renewal message", "")

    columns = ["rank", "donor_id", "segment_name", "tier", "recommended_action", "renewal_flag",
               "propensity", "cause_affinity", "priority_score", "expected_gift", "expected_value"]
    columns = [c for c in columns if c in out.columns]
    return out[columns].round({"priority_score": 4, "expected_gift": 2})


def summarize_tiers(outreach):
    return (outreach.groupby("tier")
            .agg(donors=("donor_id", "count"),
                 avg_propensity=("propensity", "mean"),
                 expected_value=("expected_value", "sum"),
                 renewal_flags=("renewal_flag", lambda s: int((s != "").sum())))
            .round({"avg_propensity": 3, "expected_value": 0})
            .reset_index())
