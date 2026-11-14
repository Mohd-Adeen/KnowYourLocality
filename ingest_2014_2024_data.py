"""
NCRB Official Dataset Ingestion & Consolidation Engine (2014-2024)
-----------------------------------------------------------------
Ingests, extracts, cleans, standardizes, and unifies district-level data
from all 9 official NCRB categories covering years 2014 through 2024:
  1. District-wise IPC Crimes (Core IPC / BNS offenses)
  2. District-wise crime against Women
  3. District-wise Crime against Children
  4. District-wise Crime against SC
  5. District-wise Crime against ST
  6. District-wise Cyber Crimes
  7. District-wise SLL Crimes
  8. District-wise IPC Crime by Juveniles
  9. District-wise SLL Crime by Juveniles
"""

import os
import sys
import re
import json
import shutil
import logging
import openpyxl
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

STATE_NORMALIZATION = {
    'A&N ISLANDS': 'A & N ISLANDS',
    'A & N ISLANDS': 'A & N ISLANDS',
    'ANDAMAN AND NICOBAR ISLANDS': 'A & N ISLANDS',
    'ANDAMAN & NICOBAR ISLANDS': 'A & N ISLANDS',
    'ANDHRA PRADESH': 'ANDHRA PRADESH',
    'ARUNACHAL PRADESH': 'ARUNACHAL PRADESH',
    'ASSAM': 'ASSAM',
    'BIHAR': 'BIHAR',
    'CHANDIGARH': 'CHANDIGARH',
    'CHHATTISGARH': 'CHHATTISGARH',
    'D&N HAVELI': 'D & N HAVELI AND DAMAN & DIU',
    'D & N HAVELI': 'D & N HAVELI AND DAMAN & DIU',
    'DADRA & NAGAR HAVELI': 'D & N HAVELI AND DAMAN & DIU',
    'DAMAN & DIU': 'D & N HAVELI AND DAMAN & DIU',
    'D&N HAVELI AND DAMAN & DIU': 'D & N HAVELI AND DAMAN & DIU',
    'DADRA AND NAGAR HAVELI AND DAMAN AND DIU': 'D & N HAVELI AND DAMAN & DIU',
    'DELHI': 'DELHI UT',
    'DELHI UT': 'DELHI UT',
    'GOA': 'GOA',
    'GUJARAT': 'GUJARAT',
    'HARAYANA': 'HARYANA',
    'HARYANA': 'HARYANA',
    'HIMACHAL PRADESH': 'HIMACHAL PRADESH',
    'JAMMU & KASHMIR': 'JAMMU & KASHMIR',
    'JHARKHAND': 'JHARKHAND',
    'KARNATAKA': 'KARNATAKA',
    'KERALA': 'KERALA',
    'LADAKH': 'JAMMU & KASHMIR',
    'LAKSHADWEEP': 'LAKSHADWEEP',
    'MADHYA PRADESH': 'MADHYA PRADESH',
    'MAHARASHTRA': 'MAHARASHTRA',
    'MANIPUR': 'MANIPUR',
    'MEGHALAYA': 'MEGHALAYA',
    'MIZORAM': 'MIZORAM',
    'NAGALAND': 'NAGALAND',
    'NAGALAND #': 'NAGALAND',
    'ODISHA': 'ODISHA',
    'ORISSA': 'ODISHA',
    'PUDUCHERRY': 'PUDUCHERRY',
    'PONDICHERRY': 'PUDUCHERRY',
    'PUNJAB': 'PUNJAB',
    'RAJASTHAN': 'RAJASTHAN',
    'SIKKIM': 'SIKKIM',
    'TAMIL NADU': 'TAMIL NADU',
    'TELANGANA': 'TELANGANA',
    'TRIPURA': 'TRIPURA',
    'UTTAR PRADESH': 'UTTAR PRADESH',
    'UTTARAKHAND': 'UTTARAKHAND',
    'WEST BENGAL': 'WEST BENGAL',
}

IPC_PATTERNS = {
    'TOTAL IPC CRIMES': [r'Total Cognizable (IPC|IPC/BNS) crimes'],
    'MURDER': [r'^Murder$', r'Murder \(Sec\.302', r'Murder \(Section 103 \(1\) BNS /Section 302 IPC\) \(Total'],
    'A. MURDER': [r'Attempt to commit Murder'],
    'CULPABLE HOMICIDE': [r'Culpable Homicide not amounting to Murder'],
    'RAPE': [r'^Rape$', r'Rape \(Sec\.376 IPC\)', r'Rape \(Section 64 to Section 71 BNS'],
    'CUSTODIAL RAPE': [r'Custodial Rape'],
    'OTHER RAPE': [r'Rape_Others', r'Rape other than Custodial'],
    'KIDNAPPING': [r'Kidnapping & Abduction_Total', r'Kidnapping and Abduction.*\(Total', r'Kidnapping & Abduction.*\(Total'],
    'KIDNAPPING OF WOMEN': [r'Kidnapping.*Women.*marriage'],
    'KIDNAPPING OTHERS': [r'Other Kidnapping & Abduction'],
    'DACOITY': [r'^Dacoity$', r'Dacoity.*\(Total'],
    'PREPARATION FOR DACOITY': [r'Preparation.*Dacoity'],
    'ROBBERY': [r'^Robbery$', r'Robbery\s*\(Sec\.392', r'Robbery\s*\(Section 309'],
    'BURGLARY': [r'Criminal Trespass/Burglary', r'Burglary.*\(Total'],
    'THEFT': [r'^Theft$', r'Theft.*\(Total'],
    'AUTO THEFT': [r'Auto.*Theft', r'Vehicle Theft'],
    'OTHER THEFT': [r'Other Theft', r'Other Thefts'],
    'RIOTS': [r'^Riots$', r'Rioting.*\(Total'],
    'CRIMINAL BREACH OF TRUST': [r'Criminal Breach of Trust'],
    'CHEATING': [r'^Cheating$', r'Cheating \(Sec\.420 IPC\)', r'Cheating \(Section 318'],
    'COUNTERFIETING': [r'Counterfeit', r'Counterfeiting'],
    'ARSON': [r'^Arson'],
    'HURT/GREVIOUS HURT': [r'Grievous Hurt', r'Hurt - Hurt \(Total\)', r'Hurt or Grievous Hurt.*\(Total'],
    'DOWRY DEATHS': [r'Dowry Death'],
    'ASSAULT ON WOMEN WITH INTENT TO OUTRAGE HER MODESTY': [r'Assault on Women with intent to outrage', r'Assault or use of Criminal Force to woman with intent to outrage'],
    'INSULT TO MODESTY OF WOMEN': [r'Insult.*Modesty'],
    'CRUELTY BY IN-LAWS': [r'Cruelty by Husband'],
    'IMPORTATION OF GIRLS': [r'Importation of Girls'],
    'DEATH BY NEGLIGENCE': [r'Causing Death by Negligence'],
    'OTHER IPC CRIMES': [r'Other IPC crimes', r'Other IPC Crimes', r'Other IPC/BNS crimes']
}

def clean_state_name(raw_name):
    if not raw_name:
        return ""
    s = re.sub(r'^(State|UT)\s*:\s*', '', str(raw_name), flags=re.I).strip().upper()
    return STATE_NORMALIZATION.get(s, s)

def clean_district_name(raw_name):
    if not raw_name:
        return ""
    d = str(raw_name).strip().upper()
    d = re.sub(r'\s+', ' ', d)
    return d

def find_file(folder_name, year):
    target_dir = os.path.join(DATASET_DIR, folder_name)
    if not os.path.exists(target_dir):
        return None
    for f in os.listdir(target_dir):
        if str(year) in f and f.endswith('.xlsx'):
            return os.path.join(target_dir, f)
    return None

def extract_domain_totals(folder_name, year):
    """
    Extracts total crime count per (State, District) and per state index for a domain folder.
    Returns: dict keyed by (state, district) and dict keyed by (state, row_idx_within_state).
    """
    fpath = find_file(folder_name, year)
    if not fpath:
        return {}, {}

    wb = openpyxl.load_workbook(fpath, read_only=True)
    sheet = wb.active
    rows = list(sheet.iter_rows(values_only=True))
    wb.close()

    if not rows:
        return {}, {}

    start_row = 0
    for idx, r in enumerate(rows[:12]):
        val0 = str(r[0]).strip() if r[0] is not None else ''
        if val0.startswith('State') or val0.startswith('UT') or 'State :' in val0 or 'UT :' in val0:
            start_row = idx
            break

    headers = []
    num_cols = len(rows[start_row-1]) if start_row > 0 else len(rows[1])
    for c in range(num_cols):
        parts = []
        for r_i in range(1, start_row):
            v = rows[r_i][c] if c < len(rows[r_i]) else None
            if v is not None:
                s = str(v).strip()
                if s and not s.startswith('[') and not s.isdigit() and s != 'None':
                    parts.append(s)
        headers.append(' | '.join(parts))

    # Find total column
    total_idx = None
    for c_idx in range(len(headers)-1, -1, -1):
        h = headers[c_idx].upper()
        if 'TOTAL' in h and any(k in h for k in ['CRIME', 'VICTIM', 'SLL', 'SC', 'ST', 'CHILDREN', 'WOMEN', 'CYBER']):
            total_idx = c_idx
            break

    named_mapping = {}
    pos_mapping = {}
    current_state = None
    state_row_count = 0

    for r in rows[start_row:]:
        r0 = str(r[0]).strip() if r[0] is not None else ''
        r1 = str(r[1]).strip() if len(r) > 1 and r[1] is not None else ''
        if (r0.startswith('State') or r0.startswith('UT') or 'State :' in r0 or 'UT :' in r0) and (not r1 or r1 == 'None'):
            current_state = clean_state_name(r0)
            state_row_count = 0
        elif current_state and r1 and r1 != 'None' and not r1.startswith('[') and not r1.isdigit():
            val = r[total_idx] if total_idx is not None and total_idx < len(r) else 0
            try:
                val = float(val) if val is not None else 0.0
            except:
                val = 0.0
            dist_clean = clean_district_name(r1)
            named_mapping[(current_state, dist_clean)] = val
            pos_mapping[(current_state, state_row_count)] = val
            state_row_count += 1

    return named_mapping, pos_mapping

def ingest_all_years():
    logging.info("Starting ingestion of 2014-2024 NCRB official datasets...")
    all_records = []

    for year in range(2014, 2025):
        logging.info(f"Processing Year {year}...")
        ipc_file = find_file("District-wise IPC Crimes", year)
        if not ipc_file:
            logging.warning(f"IPC file for {year} not found! Skipping.")
            continue

        # Load domain totals
        wom_named, wom_pos = extract_domain_totals("District-wise crime against Women", year)
        ch_named, ch_pos = extract_domain_totals("District-wise Crime against Children", year)
        sc_named, sc_pos = extract_domain_totals("District-wise Crime against SC", year)
        st_named, st_pos = extract_domain_totals("District-wise Crime against ST", year)
        cyb_named, cyb_pos = extract_domain_totals("District-wise Cyber Crimes", year)
        sll_named, sll_pos = extract_domain_totals("District-wise SLL Crimes", year)
        juv_ipc_named, juv_ipc_pos = extract_domain_totals("District-wise IPC Crime by Juveniles", year)
        juv_sll_named, juv_sll_pos = extract_domain_totals("District-wise SLL Crime by Juveniles", year)

        # Parse IPC file
        wb = openpyxl.load_workbook(ipc_file, read_only=True)
        sheet = wb.active
        rows = list(sheet.iter_rows(values_only=True))
        wb.close()

        start_row = 0
        for idx, r in enumerate(rows[:12]):
            val0 = str(r[0]).strip() if r[0] is not None else ''
            if val0.startswith('State') or val0.startswith('UT') or 'State :' in val0 or 'UT :' in val0:
                start_row = idx
                break

        headers = []
        num_cols = len(rows[start_row-1]) if start_row > 0 else len(rows[1])
        for c in range(num_cols):
            parts = []
            for r_i in range(1, start_row):
                v = rows[r_i][c] if c < len(rows[r_i]) else None
                if v is not None:
                    s = str(v).strip()
                    if s and not s.startswith('[') and not s.isdigit() and s != 'None':
                        parts.append(s)
            headers.append(' | '.join(parts))

        # Build column index mapping for IPC targets
        col_map = {}
        for col_name, pats in IPC_PATTERNS.items():
            matched_idx = None
            for p in pats:
                for c_i, h in enumerate(headers):
                    if re.search(p, h, flags=re.I):
                        matched_idx = c_i
                        break
                if matched_idx is not None:
                    break
            col_map[col_name] = matched_idx

        # Iterate data rows
        current_state = None
        state_row_count = 0

        for r in rows[start_row:]:
            r0 = str(r[0]).strip() if r[0] is not None else ''
            r1 = str(r[1]).strip() if len(r) > 1 and r[1] is not None else ''

            if (r0.startswith('State') or r0.startswith('UT') or 'State :' in r0 or 'UT :' in r0) and (not r1 or r1 == 'None'):
                current_state = clean_state_name(r0)
                state_row_count = 0
            elif current_state and r1 and r1 != 'None' and not r1.startswith('[') and not r1.isdigit():
                dist_clean = clean_district_name(r1)
                is_aggregate = ('TOTAL' in dist_clean)

                rec = {
                    'STATE': current_state,
                    'DISTRICT': dist_clean,
                    'YEAR': year,
                    'IS_AGGREGATE_ROW': is_aggregate
                }

                # Extract IPC values
                for col_name, c_idx in col_map.items():
                    val = 0.0
                    if c_idx is not None and c_idx < len(r):
                        try:
                            val = float(r[c_idx]) if r[c_idx] is not None else 0.0
                        except:
                            val = 0.0
                    rec[col_name] = val

                # Derive missing sub-breakdowns if needed
                if rec.get('OTHER RAPE', 0) == 0 and rec.get('RAPE', 0) > 0:
                    rec['OTHER RAPE'] = rec['RAPE']
                if rec.get('OTHER THEFT', 0) == 0 and rec.get('THEFT', 0) > 0:
                    rec['OTHER THEFT'] = rec['THEFT'] - rec.get('AUTO THEFT', 0)

                # Attach domain totals (named match first, then positional fallback)
                k_named = (current_state, dist_clean)
                k_pos = (current_state, state_row_count)

                rec['CRIMES AGAINST WOMEN'] = wom_named.get(k_named, wom_pos.get(k_pos, 0.0))
                rec['CRIMES AGAINST CHILDREN'] = ch_named.get(k_named, ch_pos.get(k_pos, 0.0))
                rec['CRIMES AGAINST SC'] = sc_named.get(k_named, sc_pos.get(k_pos, 0.0))
                rec['CRIMES AGAINST ST'] = st_named.get(k_named, st_pos.get(k_pos, 0.0))
                rec['CYBER CRIMES'] = cyb_named.get(k_named, cyb_pos.get(k_pos, 0.0))
                rec['SLL CRIMES'] = sll_named.get(k_named, sll_pos.get(k_pos, 0.0))
                rec['JUVENILE CRIMES'] = juv_ipc_named.get(k_named, juv_ipc_pos.get(k_pos, 0.0)) + \
                                         juv_sll_named.get(k_named, juv_sll_pos.get(k_pos, 0.0))

                all_records.append(rec)
                state_row_count += 1

    df = pd.DataFrame(all_records)
    logging.info(f"Successfully consolidated {len(df)} total records from 2014 to 2024!")
    return df

def save_and_backup(df):
    clean_csv = os.path.join(BASE_DIR, "crime_data_clean.csv")
    raw_csv = os.path.join(BASE_DIR, "crime_data.csv")

    backup_clean = os.path.join(BASE_DIR, "crime_data_clean_legacy_backup.csv")
    backup_raw = os.path.join(BASE_DIR, "crime_data_legacy_backup.csv")

    if os.path.exists(clean_csv) and not os.path.exists(backup_clean):
        logging.info(f"Backing up existing clean dataset to {backup_clean}")
        shutil.copyfile(clean_csv, backup_clean)

    if os.path.exists(raw_csv) and not os.path.exists(backup_raw):
        logging.info(f"Backing up existing raw dataset to {backup_raw}")
        shutil.copyfile(raw_csv, backup_raw)

    # Standardize column order
    core_cols = [
        'STATE', 'DISTRICT', 'YEAR',
        'MURDER', 'A. MURDER', 'CULPABLE HOMICIDE',
        'RAPE', 'CUSTODIAL RAPE', 'OTHER RAPE',
        'KIDNAPPING', 'KIDNAPPING OF WOMEN', 'KIDNAPPING OTHERS',
        'DACOITY', 'PREPARATION FOR DACOITY', 'ROBBERY',
        'BURGLARY', 'THEFT', 'AUTO THEFT', 'OTHER THEFT',
        'RIOTS', 'CRIMINAL BREACH OF TRUST', 'CHEATING', 'COUNTERFIETING',
        'ARSON', 'HURT/GREVIOUS HURT', 'DOWRY DEATHS',
        'ASSAULT ON WOMEN WITH INTENT TO OUTRAGE HER MODESTY',
        'INSULT TO MODESTY OF WOMEN', 'CRUELTY BY IN-LAWS', 'IMPORTATION OF GIRLS',
        'DEATH BY NEGLIGENCE', 'OTHER IPC CRIMES', 'TOTAL IPC CRIMES',
        'CRIMES AGAINST WOMEN', 'CRIMES AGAINST CHILDREN',
        'CRIMES AGAINST SC', 'CRIMES AGAINST ST',
        'CYBER CRIMES', 'SLL CRIMES', 'JUVENILE CRIMES',
        'IS_AGGREGATE_ROW'
    ]

    # Reorder columns
    present_cols = [c for c in core_cols if c in df.columns]
    extra_cols = [c for c in df.columns if c not in core_cols]
    ordered_df = df[present_cols + extra_cols]

    ordered_df.to_csv(clean_csv, index=False)
    ordered_df.to_csv(raw_csv, index=False)
    logging.info(f"Exported clean 2014-2024 dataset to {clean_csv} ({len(ordered_df)} rows, {len(ordered_df.columns)} columns)")

    # Update metadata
    meta_path = os.path.join(BASE_DIR, "dataset_metadata.json")
    meta = {
        "title": "National Crime Records Bureau (NCRB) District-wise Crime in India (2014-2024 Official Series)",
        "source_authority": "National Crime Records Bureau (NCRB), Ministry of Home Affairs, Government of India",
        "portal": "Open Government Data (OGD) Platform India (data.gov.in) & NCRB Reports Portal",
        "license": "Open Government Data License - India (OGDL)",
        "years_covered": [2014, 2024],
        "total_records": int(len(ordered_df)),
        "total_states": int(ordered_df['STATE'].nunique()),
        "total_districts": int(ordered_df[~ordered_df['IS_AGGREGATE_ROW']]['DISTRICT'].nunique()),
        "census_benchmark": "Census of India 2011 (Registrar General & Census Commissioner)",
        "forecast_horizon": [2025, 2026, 2027, 2028],
        "crime_categories_count": int(len(present_cols) - 4)
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=4)
    logging.info(f"Updated metadata in {meta_path}")

if __name__ == "__main__":
    df = ingest_all_years()
    save_and_backup(df)
    print("INGESTION_COMPLETE")
