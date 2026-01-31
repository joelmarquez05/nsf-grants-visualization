import pandas as pd
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

INPUT_FILE = os.path.join(PROJECT_DIR, "raw_data", "original_data", "nsf_terminations_airtable.csv")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "clean_data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "nsf_cancellations.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_FILE)

# needed columns
columns_mapping = {
    'grant_id': 'AwardID',
    'status': 'Status',
    'nsf_start_date': 'Year',
    'project_title': 'ProjectTitle',
    'org_state': 'StateCode',
    'estimated_budget': 'EstimatedBudget',
    'directorate': 'Directorate',
    'dir': 'DirectorateAbbr'
}

df_clean = df[list(columns_mapping.keys())].copy()
df_clean = df_clean.rename(columns=columns_mapping)

df_clean['AwardID'] = df_clean['AwardID'].astype(str)
df_clean['Status'] = df_clean['Status'].str.replace('❌ ', '', regex=False)
df_clean['Status'] = df_clean['Status'].str.replace('🔄 Possibly ', '', regex=False)

# normalize Directorate names (match nsf_awards_full.csv)
df_clean['Directorate'] = df_clean['Directorate'].replace({
    'Office of the Director': 'Office Of The Director',
    'Technology, Innovation and Partnerships': 'Directorate for Technology, Innovation, and Partnerships'
})

# fiscal year (Oct 1 - Sep 30): if month >= 10, FY = year + 1
start_date = pd.to_datetime(df_clean['Year'], errors='coerce')
df_clean['Year'] = start_date.dt.year + (start_date.dt.month >= 10).astype(int)

df_clean = df_clean[df_clean['Year'].between(2021, 2025)]

EXCLUDED_LOCATIONS = {'AS', 'GU', 'MP', 'PR', 'VI'}
df_clean = df_clean[~df_clean['StateCode'].isin(EXCLUDED_LOCATIONS)]

# normalize abbreviations (match nsf_awards_full.csv)
df_clean['DirectorateAbbr'] = df_clean['DirectorateAbbr'].replace({
    'CISE': 'CSE',
    'OD': 'O/D'
})

# add Division (nsf_awards_full.csv as source)
FULL_AWARDS_FILE = os.path.join(OUTPUT_DIR, "nsf_awards_full.csv")
df_full = pd.read_csv(FULL_AWARDS_FILE, usecols=['AwardID', 'Directorate', 'DirectorateAbbr', 'Division', 'DivisionAbbr', 'EstimatedBudget'])
df_full['AwardID'] = df_full['AwardID'].astype(str)

df_clean = df_clean.merge(
    df_full[['AwardID', 'Division', 'DivisionAbbr', 'DirectorateAbbr', 'EstimatedBudget']],
    on='AwardID',
    how='left',
    suffixes=('', '_full')
)

df_clean['DirectorateAbbr'] = df_clean['DirectorateAbbr'].fillna(df_clean['DirectorateAbbr_full'])
df_clean = df_clean.drop(columns=['DirectorateAbbr_full'])

# align EstimatedBudget (match nsf_awards_full.csv)
budget_mismatch_before = (df_clean['EstimatedBudget'] != df_clean['EstimatedBudget_full']).sum()
df_clean.loc[df_clean['EstimatedBudget_full'].notna(), 'EstimatedBudget'] = df_clean['EstimatedBudget_full']
df_clean = df_clean.drop(columns=['EstimatedBudget_full'])

# fill Directorate with mapping (nsf_awards_full.csv as source)
directorate_mapping = df_full.groupby('DirectorateAbbr')['Directorate'].first().to_dict()
for abbr, full_name in directorate_mapping.items():
    mask = (df_clean['DirectorateAbbr'] == abbr) & (df_clean['Directorate'].isna())
    df_clean.loc[mask, 'Directorate'] = full_name

# fix for ADVANCE
advance_mask = (
    df_clean['ProjectTitle'].str.contains('ADVANCE', case=False, na=False) & 
    (df_clean['DirectorateAbbr'].isna() | df_clean['Division'].isna())
)
df_clean.loc[advance_mask, 'DirectorateAbbr'] = df_clean.loc[advance_mask, 'DirectorateAbbr'].fillna('EDU')
df_clean.loc[advance_mask, 'Directorate'] = df_clean.loc[advance_mask, 'Directorate'].fillna('Directorate for STEM Education')
df_clean.loc[advance_mask, 'Division'] = df_clean.loc[advance_mask, 'Division'].fillna('Div. of Equity for Excellence in STEM')
df_clean.loc[advance_mask, 'DivisionAbbr'] = df_clean.loc[advance_mask, 'DivisionAbbr'].fillna('EES')

# manual fixes for specific AwardIDs (from NSF website)
manual_fixes = {
    '1943467': {'Division': 'Division of Information & Intelligent Systems', 'DivisionAbbr': 'IIS'},
    '2007891': {'Directorate': 'Directorate for Computer and Information Science and Engineering', 'DirectorateAbbr': 'CSE', 'Division': 'Division of Computing and Communication Foundations', 'DivisionAbbr': 'CCF'},
    '2008428': {'Directorate': 'Directorate for STEM Education', 'DirectorateAbbr': 'EDU', 'Division': 'Div. of Equity for Excellence in STEM', 'DivisionAbbr': 'EES'},
    '2020709': {'Division': 'Div. of Equity for Excellence in STEM', 'DivisionAbbr': 'EES'}
}
for award_id, fixes in manual_fixes.items():
    mask = df_clean['AwardID'] == award_id
    for col, val in fixes.items():
        df_clean.loc[mask, col] = val

df_clean = df_clean.drop(columns=['ProjectTitle'])

# clean Directorate and Division names (remove prefixes for cleaner tooltips)
df_clean['Directorate'] = df_clean['Directorate'].str.replace(r'^Directorate for ', '', regex=True)
df_clean['Division'] = df_clean['Division'].str.replace(r'^Division [Oo]f ', '', regex=True)
df_clean['Division'] = df_clean['Division'].str.replace(r'^Div\. of ', '', regex=True)
df_clean['Division'] = df_clean['Division'].str.replace(r'^OIA-', '', regex=True)
df_clean['Division'] = df_clean['Division'].str.replace(r' \([A-Z/&]+\)$', '', regex=True) # Repeated DivisionAbbr at the end remove

df_clean.to_csv(OUTPUT_FILE, index=False)
print(f"Saved to: {OUTPUT_FILE}")
