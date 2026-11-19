# Scholarship Fundraising Toolkit

Open machine learning tools that help colleges raise scholarship funds for students who have experienced foster care.

**Version 0.1.0 · Released November 19, 2026 · MIT License**

## Why this exists

Only 8 to 12 percent of young people with foster care experience earn a two or four year college degree by their mid to late twenties, compared with roughly half of their peers. Money is a central reason. Without family support, a tuition shortfall or a gap in housing can end a student's enrollment.

Many colleges try to close that gap with scholarship funds dedicated to these students. Raising those funds means finding the relatively small group of donors who care about this cause, and most colleges that enroll students from foster care do not have a data scientist to help. This toolkit gives a small advancement office the same kind of donor analytics that large universities build in house, without needing technical staff.

## What it does

The toolkit takes a donor export from your CRM and produces a ranked outreach list in four steps:

1. **Prepare.** Checks and cleans the export: removes duplicate records, sets aside likely duplicate donors for staff to merge, fixes dates entered in day/month order, flags dates that could be read either way, and corrects impossible values. Every change is reported.
2. **Segment.** Groups donors with similar giving and engagement (for example, active donors, lapsed donors, engaged non-donors) so each group can get a message that fits.
3. **Score.** Estimates each donor's likelihood of giving in the next campaign, learned from who gave in the last one. It checks itself against a simple rule of thumb (most recent donors first) so you can see whether the model adds value on your data.
4. **Rank.** Combines likelihood of giving with cause affinity (how closely a donor's past behavior aligns with supporting students from foster care) and expected gift size, then assigns each donor an outreach tier and a recommended action.

## What you get

| File | What it is |
|---|---|
| `report.md` | A plain-language summary of the run. Start here. |
| `outreach_list.csv` | Every donor, ranked, with a tier and a recommended action. |
| `segment_profiles.csv` | A description of each donor segment. |
| `data_quality_issues.csv` | Record-level problems to fix in your CRM. |

Outreach tiers (sizes can be changed in `fundraising_toolkit/outreach.py`):

| Tier | Share of list | Recommended action |
|---|---|---|
| Tier 1 | Top 5% | Personal contact: call, visit, or handwritten note from leadership |
| Tier 2 | Next 15% | Personalized email from a named staff member, with a follow-up call |
| Tier 3 | Next 30% | Segment-specific email and text message sequence |
| Tier 4 | Remaining 50% | General appeal through the standard campaign mailing |

Donors who have lapsed but are likely to return are flagged for a renewal message.

## Quick start (try it on sample data)

You need Python 3.10 or newer.

```bash
pip install -r requirements.txt
python data/generate_sample_data.py --rows 5000 --out data/sample_donors.csv
python run_pipeline.py --input data/sample_donors.csv --output-dir output
```

Then open `output/report.md`. A finished example is in `example_output/`.

The sample data is entirely synthetic. It includes the kinds of problems real exports have, so you can see the preparation step at work.

## Using your own data

1. Export your donor records to a CSV with the columns listed in [docs/data_dictionary.md](docs/data_dictionary.md). Most CRMs can produce these with a saved report.
2. Include `gave_last_campaign` (1 or 0) so the model can learn from your most recent campaign. Include `gave_to_foster_fund` if you have it, so the toolkit can check the cause affinity score.
3. Run:

```bash
python run_pipeline.py --input my_export.csv --output-dir results --as-of 2027-02-01
```

Use `--as-of` for the date your campaign starts. If your CRM writes dates as day/month/year, add `--date-order DMY`. To rank donors for a general scholarship fund instead of a foster youth fund, add `--fund general`.

The output identifies donors only by `donor_id`. Join it back to your CRM to see names and contact details.

## Before you trust the results

- **Check section 3 of the report.** If the model does not beat the rule of thumb on your data, do not rely on it.
- **Check section 4.** The rate of giving to the fund should rise from the lowest affinity band to the highest. If it does not, adjust the weights in `fundraising_toolkit/affinity.py`.
- **Hold back a comparison group.** Leave a small random set of donors on your usual approach so you can measure the difference the new approach makes.
- **Results on the sample data are not evidence of real performance.** They show how the toolkit works, nothing more.

## Privacy and responsible use

The toolkit runs entirely on your own computer. No donor data is sent anywhere. It uses giving and engagement behavior only, never demographic traits, and it processes donor records, not student records. See [docs/privacy_and_responsible_use.md](docs/privacy_and_responsible_use.md).

## Roadmap

- **0.2:** Donor renewal and lapse modeling, because students need support for every year of a degree, not a single gift.
- **0.3:** Outcome tracking that links scholarship recipients to persistence and completion, run inside each institution's own systems.
- **0.4:** Import templates for common CRM systems and a guide for campus programs that support students from foster care.

## Background and citation

The methodology is described in:

Nkansah, E. (2025). Optimizing Fundraising Appeals: Using Data and Machine Learning. In V. Salminen (Ed.), *Human Factors, Business Management and Society*. AHFE (2025) International Conference, AHFE Open Access, Vol. 176. AHFE International, USA. https://doi.org/10.54941/ahfe1006308

If you use this toolkit, please cite it using [CITATION.cff](CITATION.cff).

This is an independent open source project. It contains no code, data, or proprietary information from any institution.

## License

MIT. You may use, change, and share this toolkit freely, including at your institution. See [LICENSE](LICENSE).
