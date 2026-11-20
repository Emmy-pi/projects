"""Step 3: estimate each donor's likelihood of giving in the next campaign.

The model learns from who gave in the most recent campaign, using only
information that was known before that campaign began. It is checked
against a simple rule of thumb (most recent donors first) so an office can
see whether the model actually adds value on its own data.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split

NUMERIC_FEATURES = [
    "recency_days", "has_given", "gift_count", "total_giving", "avg_gift", "largest_gift",
    "tenure_years", "events_attended_3yr", "email_open_rate", "email_click_rate",
    "gave_to_youth_causes", "foster_content_clicks", "attended_cause_event",
]


def _design_matrix(df, columns=None):
    X = df[NUMERIC_FEATURES].astype(float).copy()
    dummies = pd.get_dummies(df["constituent_type"], prefix="type", dtype=float)
    X = pd.concat([X, dummies], axis=1)
    if columns is not None:
        X = X.reindex(columns=columns, fill_value=0.0)
    return X


def _top_decile(y_true, scores):
    order = np.argsort(-scores)
    k = max(1, len(order) // 10)
    top_rate = float(np.asarray(y_true)[order[:k]].mean())
    base = float(np.mean(y_true))
    return top_rate, (top_rate / base if base > 0 else float("nan"))


def train_and_score(df, target="gave_last_campaign", seed=42):
    """Train on past campaign outcomes, evaluate on held-out donors, and score everyone.

    Returns (scored_df, metrics, feature_importance).
    """
    if target not in df.columns:
        raise ValueError(
            f"Column '{target}' is needed to train the model: 1 if the donor gave in the most "
            "recent campaign, 0 if not."
        )
    y = pd.to_numeric(df[target], errors="coerce").fillna(0).astype(int)
    if y.nunique() < 2:
        raise ValueError(f"'{target}' must contain both donors who gave (1) and who did not (0).")
    X = _design_matrix(df)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, stratify=y, random_state=seed)

    model = GradientBoostingClassifier(n_estimators=250, max_depth=3, learning_rate=0.05,
                                       subsample=0.8, random_state=seed)
    model.fit(X_tr, y_tr)
    p_te = model.predict_proba(X_te)[:, 1]

    baseline_te = -df.loc[X_te.index, "recency_days"].to_numpy(dtype=float)  # most recent donors first
    top_rate, lift = _top_decile(y_te.to_numpy(), p_te)
    b_top_rate, b_lift = _top_decile(y_te.to_numpy(), baseline_te)
    metrics = {
        "target": target,
        "training_donors": int(len(X_tr)),
        "test_donors": int(len(X_te)),
        "response_rate": round(float(y.mean()), 4),
        "model_auc": round(float(roc_auc_score(y_te, p_te)), 3),
        "model_average_precision": round(float(average_precision_score(y_te, p_te)), 3),
        "model_top_decile_response_rate": round(top_rate, 3),
        "model_top_decile_lift": round(lift, 2),
        "baseline_auc": round(float(roc_auc_score(y_te, baseline_te)), 3),
        "baseline_top_decile_response_rate": round(b_top_rate, 3),
        "baseline_top_decile_lift": round(b_lift, 2),
    }

    importance = (pd.Series(model.feature_importances_, index=X.columns)
                  .sort_values(ascending=False).round(3).rename("importance"))

    # Refit on all donors so the final scores use every outcome available.
    model.fit(X, y)
    scored = df.copy()
    scored["propensity"] = model.predict_proba(X)[:, 1].round(4)
    return scored, metrics, importance
