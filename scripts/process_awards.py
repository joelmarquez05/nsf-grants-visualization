import pandas as pd
import json
import os
import glob
import concurrent.futures

NSF_DATA_DIR = os.path.join("raw_data", "full_nsf_awards_data")
OUTPUT_DIR = "clean_data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "nsf_awards_full.csv")

EXCLUDED_LOCATIONS = {'AS', 'GU', 'MP', 'PR', 'VI', 'BM-07', 'GENEVA'}

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        d = json.load(f)
    
    inst = d.get('inst', {})
    inst_country = inst.get('inst_country_name')
    
    # only US institutions
    if inst_country != 'United States':
        return None
    
    state_code = inst.get('inst_state_code')
    if state_code in EXCLUDED_LOCATIONS:
        return None
    
    # get year from directory path (fiscal year by NSF source)
    year_str = os.path.basename(os.path.dirname(file_path))
    fiscal_year = int(year_str)
    
    item = {
        'AwardID': str(d.get('awd_id', '')),
        'Directorate': d.get('org_dir_long_name'),
        'DirectorateAbbr': d.get('dir_abbr'),
        'Division': d.get('org_div_long_name'),
        'DivisionAbbr': d.get('div_abbr'),
        'StateCode': state_code,
        'StateName': inst.get('inst_state_name'),
        'Year': fiscal_year,
        'EstimatedBudget': max(
            float(d.get('tot_intn_awd_amt', 0) or 0),
            float(d.get('awd_amount', 0) or 0)
        )
    }
    return item


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    years = ['2021', '2022', '2023', '2024', '2025']
    first_year = True
    
    for year in years:
        search_path = os.path.join(NSF_DATA_DIR, year, "*.json")
        files = glob.glob(search_path)
        
        year_grants = []
        
        # parallel processing
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(process_file, files)
            
            for res in results:
                if res is not None:
                    year_grants.append(res)
        
        df_year = pd.DataFrame(year_grants)
        
        if not df_year.empty:
            if first_year:
                df_year.to_csv(OUTPUT_FILE, index=False, mode='w')
                first_year = False
            else:
                df_year.to_csv(OUTPUT_FILE, index=False, mode='a', header=False)
        
        print(f"{year} completed")
    
    df_final = pd.read_csv(OUTPUT_FILE)
    
    # exclude administrative/governance units (< 100 grants, not research directorates)
    EXCLUDED_DIRECTORATES = {'IRM', 'BFA', 'NSB', 'OCIO'}
    df_final = df_final[~df_final['DirectorateAbbr'].isin(EXCLUDED_DIRECTORATES)]
    
    # clean Directorate and Division names (remove prefixes for cleaner tooltips)
    df_final['Directorate'] = df_final['Directorate'].str.replace(r'^Directorate for ', '', regex=True)
    df_final['Division'] = df_final['Division'].str.replace(r'^Division [Oo]f ', '', regex=True)
    df_final['Division'] = df_final['Division'].str.replace(r'^OIA-', '', regex=True)
    df_final['Division'] = df_final['Division'].str.replace(r'^Div\. of ', '', regex=True)
    df_final['Division'] = df_final['Division'].str.replace(r' \([A-Z/&]+\)$', '', regex=True) # Repeated DivisionAbbr at the end
    
    df_final.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
