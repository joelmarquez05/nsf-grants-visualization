# NSF Grants Visualization (2021-2025)

## Overview

This project presents an interactive data visualization of National Science Foundation (NSF) grants from fiscal years 2021 to 2025, with a specific focus on analyzing the impact of grant cancellations in 2025.

Using **Altair** and **Streamlit**, I developed a set of visualizations following the "Overview first, zoom and filter, then details on demand" methodology. The analysis examines:
- Grant distribution across U.S. states and NSF directorates (over 57,000 total grants).
- Temporal evolution of funding amounts.
- The geography and financial impact of nearly 2,000 grant cancellations.

## Included Files

- **`visualization.ipynb`**: Main Jupyter notebook containing the analysis, visualizations, and detailed documentation.
- **`streamlit/`**: Contains the code for the interactive web dashboard (`streamlit_app.py` and `charts.py`).
- **`clean_data/`**: Processed datasets used for the analysis.
- **`scripts/`**: Python scripts used to process raw data into the clean formats.

## Data Sources & Methodology

### 1. NSF Awards (`nsf_awards_full.csv`)
Original data sourced from the [NSF Award Website](https://www.nsf.gov/awardsearch/download-awards).
- **Processing**: Consolidated from individual JSON records. Filtered to exclude international grants (non-US) and internal administrative units (e.g., HR, IT oversight) to focus on research funding.
- **Budget**: Using the maximum of `tot_intn_awd_amt` and `awd_amount` to reflect actual committed funding.

### 2. Grant Cancellations (`nsf_cancellations.csv`)
Sourced from the [TidyTuesday Data Project](https://github.com/rfordatascience/tidytuesday/blob/main/data/2025/2025-05-06/readme.md), derived from a community-tracked Airtable of terminations.
- **Processing**: Enriched with Division/Directorate info from the main awards dataset to match naming conventions.

### 3. Political & Geographic Context (`us_states.csv`)
Includes U.S. presidential election results (2020 and 2024 winners per state) to allow for political analysis of funding patterns, along with latitude/longitude data for mapping.

---

## Setup Instructions

### Option A: Google Colab
If you are running the `visualization.ipynb` notebook in Google Colab:

1.  **Create a directory** named `clean_data` in the Colab file browser.
2.  **Upload** the following CSV files (found in the `clean_data/` folder of this repository) into that directory:
    -   `nsf_awards_full.csv`
    -   `nsf_cancellations.csv`
    -   `us_states.csv`
3.  Run the notebook cells to generate the visualizations.

### Option B: Local Setup
To run the analysis or the Streamlit dashboard on your local machine:

#### 1. Environment Setup
Create and activate a virtual environment:

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 2. Install Dependencies
Install all required packages from the requirements file:
```bash
pip install -r requirements.txt
```

#### 3. Run the Dashboard
To launch the interactive Streamlit application:
```bash
streamlit run streamlit/streamlit_app.py
```

#### 4. Run the Notebook
To use `visualization.ipynb`:
- Ensure your Jupyter environment is using the kernel from the virtual environment you just created.
