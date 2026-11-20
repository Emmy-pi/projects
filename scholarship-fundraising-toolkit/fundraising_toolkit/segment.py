"""Step 2: group donors into segments with similar giving and engagement.

Segments let a small office write a different message for each group
(for example, thanking loyal donors versus re-engaging lapsed ones)
instead of sending one appeal to everyone.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

SEGMENT_FEATURES = ["recency_days", "gift_count", "total_giving", "events_attended_3yr", "email_click_rate"]


def segment(df, n_segments=5, seed=42):
    """Add ``segment_id`` and ``segment_name`` columns and return a profile table."""
    X = df[SEGMENT_FEATURES].copy()
    for col in ("recency_days", "gift_count", "total_giving"):
        X[col] = np.log1p(X[col])
    X_scaled = StandardScaler().fit_transform(X)
    km = KMeans(n_clusters=n_segments, n_init=10, random_state=seed)
    out = df.copy()
    out["segment_id"] = km.fit_predict(X_scaled)

    engagement = (out["events_attended_3yr"].rank(pct=True) + out["email_click_rate"].rank(pct=True)) / 2
    out["_engagement"] = engagement
    givers = out[out["has_given"] == 1]
    major_threshold = givers["total_giving"].quantile(0.75) if len(givers) else 0
    overall_engagement = engagement.median()

    profile = out.groupby("segment_id").agg(
        donors=("donor_id", "count"),
        share_ever_gave=("has_given", "mean"),
        median_days_since_last_gift=("recency_days", "median"),
        median_total_giving=("total_giving", "median"),
        median_gift_count=("gift_count", "median"),
        avg_events_3yr=("events_attended_3yr", "mean"),
        avg_email_click_rate=("email_click_rate", "mean"),
        _engagement=("_engagement", "mean"),
    )

    names, used = {}, {}
    for sid, row in profile.iterrows():
        if row["share_ever_gave"] < 0.3:
            name = "Engaged non-donors" if row["_engagement"] > overall_engagement else "Low-engagement prospects"
        elif row["median_days_since_last_gift"] > 730:
            name = "Lapsed donors"
        elif row["median_total_giving"] >= major_threshold:
            name = "Loyal major donors"
        elif row["median_days_since_last_gift"] <= 365:
            name = "Active donors"
        else:
            name = "Occasional donors"
        used[name] = used.get(name, 0) + 1
        names[sid] = name if used[name] == 1 else f"{name} ({used[name]})"

    out["segment_name"] = out["segment_id"].map(names)
    profile.insert(0, "segment_name", profile.index.map(names))
    profile = profile.drop(columns="_engagement").round(3).sort_values("donors", ascending=False)
    return out.drop(columns="_engagement"), profile.reset_index()
