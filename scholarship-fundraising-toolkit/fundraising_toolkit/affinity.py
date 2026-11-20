"""Cause affinity: how closely a donor's past behavior aligns with a specific fund.

For a scholarship fund for students who have experienced foster care, the
donors most likely to respond are often not the largest donors overall but
the ones who have already shown they care about young people in difficult
circumstances. This score is deliberately simple and transparent: every
weight is listed below and can be changed to fit an institution's own data.
It uses giving and engagement behavior only, never demographic traits.
"""
import pandas as pd

FOSTER_YOUTH_WEIGHTS = {
    "gave_to_youth_causes": 0.40,     # has given to youth or child welfare funds before
    "foster_content_clicks": 0.35,    # opened or clicked foster youth stories, scaled 0 to 1
    "attended_cause_event": 0.25,     # attended an event about foster youth or student support
}
CLICK_CAP = 5


def cause_affinity(df, weights=None):
    """Return a 0 to 1 affinity score for each donor."""
    w = weights or FOSTER_YOUTH_WEIGHTS
    parts = {
        "gave_to_youth_causes": df["gave_to_youth_causes"].clip(0, 1),
        "foster_content_clicks": df["foster_content_clicks"].clip(0, CLICK_CAP) / CLICK_CAP,
        "attended_cause_event": df["attended_cause_event"].clip(0, 1),
    }
    score = sum(w[k] * parts[k] for k in w) / sum(w.values())
    return score.round(4)


def validate_affinity(df, score_col="cause_affinity", outcome_col="gave_to_foster_fund"):
    """If past gifts to the fund are known, show how often each affinity band gave to it."""
    if outcome_col not in df.columns:
        return None
    bands = pd.cut(df[score_col], bins=[-0.001, 0, 0.25, 0.5, 1.0],
                   labels=["None (0)", "Low (up to 0.25)", "Medium (0.25 to 0.5)", "High (above 0.5)"])
    table = (df.assign(affinity_band=bands)
             .groupby("affinity_band", observed=True)[outcome_col]
             .agg(donors="count", gave_to_fund="sum", rate="mean")
             .round(3))
    return table.reset_index()
