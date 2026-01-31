# Data Reproducibility & Processing Pipeline

This document details the data sources, cleaning decisions, and processing steps taken to generate the datasets used in this project. All raw data processing is automated via the Python scripts located in the `scripts/` directory.

## 1. NSF Awards Data
**Output File**: `clean_data/nsf_awards_full.csv`
**Processing Script**: `scripts/process_awards.py`

### Data Source
The primary data source consists of JSON files obtained from the [NSF Award Website](https://www.nsf.gov/awardsearch/download-awards), containing detailed information about National Science Foundation grants from fiscal years 2021 to 2025.

Each fiscal year is organized in a separate folder (`raw_data/full_nsf_awards_data/{year}/`) containing individual JSON files per award.

### Processing & Cleaning Steps
The `process_awards.py` script consolidates all JSON files from 2021-2025 into a single manageable CSV file.

#### Records with Missing State Information
I identified **83 grants** with missing state information (`StateName` or `StateCode`).
- **International Grants (60 records)**: Awards to institutions outside the United States.
- **U.S. Territory/Non-Standard Codes (23 records)**: Grants to institutions in Bermuda and Geneva.
**Decision**: All 83 records (0.15% of the dataset) were removed because geographic visualizations require U.S. state-level data and international/territorial grants cannot be mapped to U.S. states.

#### Directorate & Division Name Cleaning
All Directorate and Division fields were cleaned to remove redundant prefixes and abbreviations (e.g., "Directorate for Geosciences" → "Geosciences", "Division of Materials Research" → "Materials Research").
**Decision**: This improves tooltip readability, space efficiency, and ensures consistency across datasets.

#### U.S. Territories Exclusion
**154 grants** (0.27% of the dataset) from U.S. territories (Puerto Rico, Virgin Islands, Guam, American Samoa, Northern Mariana Islands) were excluded.
**Decision**:
- **No map topology**: Vega's U.S. states TopoJSON does not include these territories.
- **No electoral data**: Territories do not participate in presidential elections, making political party analysis inapplicable.

#### Year Assignment
I used the **fiscal year** (derived from the NSF data organization) rather than the effective date.
**Decision**: Fiscal year reflects when the NSF committed the budget, which is most meaningful for analyzing funding patterns and policy impacts.

#### Administrative/Governance Units Exclusion
Grants from administrative units like IRM (Information Resource Management), BFA (Business & Financial Affairs), and NSB (National Science Board) were excluded.
**Decision**: These units do not fund research projects. The Office of the Director (O/D) was retained as it funds external research.

#### Budget Field Consolidation
**Decision**: I used `MAX(tot_intn_awd_amt, awd_amount)` as the `EstimatedBudget` value. This reflects the actual budget for grants that received supplemental funding and ensures consistency with the cancellations dataset.

---

## 2. Cancellation Data
**Output File**: `clean_data/nsf_cancellations.csv`
**Processing Script**: `scripts/process_cancellations.py`

### Data Source
sourced from the [TidyTuesday Data Project (2025-05-06)](https://github.com/rfordatascience/tidytuesday/blob/main/data/2025/2025-05-06/readme.md), which compiled data from a community-maintained Airtable tracking NSF grant terminations in 2025.

### Processing & Cleaning Steps
The `process_cancellations.py` script processes the raw terminations data and enriches it with information from the full awards dataset.

#### Column Standardization
Columns were renamed to match the format used in `nsf_awards_full.csv`.
- `grant_id` → `AwardID`
- `status` → `Status` (Removed emojis)
- `nsf_start_date` → `Year` (Converted to fiscal year)
- `estimated_budget` → `EstimatedBudget`

#### Fiscal Year Calculation & Filtering
The grant start date was converted to the **NSF fiscal year** (Oct 1 - Sep 30).
**Decision**: A filter was applied to keep only grants from FY2021-FY2025 to match the main dataset scope.

#### Data Enrichment via Join
Since the cancellations dataset lacked detailed division information and had some budget discrepancies, I enriched it by joining with `nsf_awards_full.csv` on `AwardID`.
**Decision**: 
- Filled missing `Division`, `DivisionAbbr`, and `DirectorateAbbr`.
- Replaced cancellation budget with the verified `nsf_awards_full.csv` value to ensure 100% partial budget alignment (fixing slight discrepancies in 0.8% of records).

#### Manual Fixes
- **ADVANCE Grants**: Grants with "ADVANCE" in the title were manually classified under "stem Education" (EDU) and "Equity for Excellence in STEM" (EES).
- **Specific Unmatched IDs**: 4 specific grants were manually classified using data from the NSF Award Search website.

---

## 3. Geographic & Political Data
**Output File**: `clean_data/us_states.csv`

### Data Source
This dataset provides geographic and political context for US states.

- **Political Parties**:
  - `Party2020`: Winner of the 2020 Presidential Election (Biden). Source: FEC.
  - `Party2025`: Winner of the 2024 Presidential Election (Trump). Source: AP News.
- **Geographic Data**:
  - `Id`: FIPS state codes from Vega Datasets.
  - `Latitude`/`Longitude`: State centroids from Google Public Data.

**Note**: The year 2024 uses `Party2020` affiliation, while fiscal year 2025 uses `Party2025`.
