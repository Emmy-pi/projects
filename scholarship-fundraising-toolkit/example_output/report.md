# Scholarship Fundraising Toolkit: Run Report

- Toolkit version: 0.1.0
- Run date: 2026-11-19
- Input file: `data/sample_donors.csv`
- Fund: scholarship fund for students who have experienced foster care
- Recency measured as of: 2026-02-01

## 1. Data quality

Read 5,150 records and kept 5,000. Changes made:

- Exact duplicate rows removed: 100
- Repeated donor IDs removed: 0
- Possible duplicate donors (same email, different ID) set aside until staff merge them: 50
- Negative amounts corrected to 0: 14
- Dates corrected from day/month order: 160
- Ambiguous dates parsed with the default order and flagged: 397
- Unreadable dates: 0
- Gift dates swapped because the last gift preceded the first: 0
- Missing email open rates filled with the median: 100

Every record-level issue is listed in `data_quality_issues.csv` so it can be fixed in the CRM.

## 2. Donor segments

| segment_id | segment_name | donors | share_ever_gave | median_days_since_last_gift | median_total_giving | median_gift_count | avg_events_3yr | avg_email_click_rate |
|---|---|---|---|---|---|---|---|---|
| 0 | Lapsed donors | 1579 | 1.0 | 815.0 | 97.86 | 1.0 | 0.444 | 0.036 |
| 3 | Active donors | 1376 | 1.0 | 290.5 | 370.825 | 4.0 | 0.471 | 0.048 |
| 4 | Occasional donors (2) | 962 | 1.0 | 390.0 | 258.615 | 4.0 | 2.647 | 0.051 |
| 2 | Low-engagement prospects | 548 | 0.009 | 7300.0 | 0.0 | 0.0 | 0.524 | 0.035 |
| 1 | Occasional donors | 535 | 1.0 | 376.0 | 328.1 | 4.0 | 1.372 | 0.161 |

## 3. Likelihood-of-giving model

Trained on 3,750 donors and tested on 1,250 donors the model did not see. Overall response rate in the last campaign: 34.3%.

| Measure | Model | Rule of thumb (most recent donors first) |
|---|---|---|
| AUC (0.5 = random, 1.0 = perfect) | 0.73 | 0.691 |
| Response rate in the top 10% | 73.6% | 56.0% |
| Lift in the top 10% | 2.14x | 1.63x |

The model ranks donors better than the rule of thumb on this data.

Most influential inputs:

| input | importance |
|---|---|
| recency_days | 0.354 |
| events_attended_3yr | 0.109 |
| email_open_rate | 0.105 |
| gift_count | 0.091 |
| email_click_rate | 0.075 |
| total_giving | 0.06 |
| tenure_years | 0.059 |
| largest_gift | 0.054 |

## 4. Cause affinity check

How often donors in each affinity band gave to the foster youth fund in the last campaign. If the rate does not rise from the lowest band to the highest, adjust the weights in `affinity.py`.

| affinity_band | donors | gave_to_fund | rate |
|---|---|---|---|
| None (0) | 1795 | 131 | 0.073 |
| Low (up to 0.25) | 2010 | 216 | 0.107 |
| Medium (0.25 to 0.5) | 856 | 113 | 0.132 |
| High (above 0.5) | 339 | 49 | 0.145 |

## 5. Outreach plan

| tier | donors | avg_propensity | expected_value | renewal_flags |
|---|---|---|---|---|
| Tier 1 | 250 | 0.554 | 56466.0 | 12 |
| Tier 2 | 750 | 0.479 | 41877.0 | 28 |
| Tier 3 | 1500 | 0.402 | 30110.0 | 37 |
| Tier 4 | 2500 | 0.246 | 13134.0 | 9 |

Expected value is likelihood of giving multiplied by expected gift size. It is a planning estimate, not a forecast.

## Before acting on these results

- Results on the synthetic sample data say nothing about real-world performance. Run the toolkit on your own data and check section 3.
- Hold back a small random group from the new approach so you can measure the difference it makes.
- Review the data quality issues before importing results into your CRM.
