# Data dictionary

The toolkit reads one CSV file with one row per donor. Column names are not case sensitive, and spaces are treated as underscores.

All history columns should describe the donor **as of the start of the campaign** you are learning from. If a gift made during that campaign is counted in `gift_count` or `last_gift_date`, the model will look better than it really is.

## Required columns

| Column | Type | Description |
|---|---|---|
| `donor_id` | text | Your CRM's unique ID for the donor. |
| `constituent_type` | text | For example: alumni, parent, friend, faculty_staff, organization. |
| `first_gift_date` | date | Date of the donor's first gift. Blank if they have never given. |
| `last_gift_date` | date | Date of the most recent gift before the campaign. Blank if never. |
| `gift_count` | number | Number of gifts before the campaign. |
| `total_giving` | number | Total amount given before the campaign, in dollars. |
| `largest_gift` | number | Largest single gift, in dollars. |
| `events_attended_3yr` | number | Events attended in the last three years. |
| `email_open_rate` | 0 to 1 | Share of your emails the donor opened. |
| `email_click_rate` | 0 to 1 | Share of your emails the donor clicked. |

Dates may be written as `YYYY-MM-DD` or with slashes. Dates that can only be one order (such as 25/03/2025) are corrected automatically. Dates that could be either order (such as 03/04/2025) are read using `--date-order` and listed for review.

## Needed to train the model

| Column | Type | Description |
|---|---|---|
| `gave_last_campaign` | 1 or 0 | Whether the donor gave in the most recent campaign. |

## Recommended for a foster youth scholarship fund

| Column | Type | Description |
|---|---|---|
| `gave_to_youth_causes` | 1 or 0 | Has given to any youth, student support, or child welfare fund. |
| `foster_content_clicks` | number | Clicks or opens on stories or appeals about students from foster care. |
| `attended_cause_event` | 1 or 0 | Attended an event about foster youth or student support. |
| `gave_to_foster_fund` | 1 or 0 | Gave to the foster youth fund in the last campaign. Used only to check the affinity score. |

If these columns are missing, the toolkit still runs, but every donor's cause affinity will be 0.

## Optional

| Column | Type | Description |
|---|---|---|
| `email` | text | Used only to find likely duplicate donors. It is never written to the outreach list. |
