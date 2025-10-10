""" 
GOAL: PRODUCE QUARTERLY RECALL DATA FOR OMSQ.
By Eric Nyame, 15/04/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb

# Expand dataset to include one row for every reason
reasons = recalls_final.copy()

reasons['REASON_DESC'] = reasons['RECALL_REASON_DESCRIPTIONS'].str.split(',')

reasons = reasons.explode('REASON_DESC')

reasons['REASON_DESC'] = reasons['REASON_DESC'].str.strip()

# Bring cases with no reason recorded
missing_reasons = recalls_final[recalls_final['NUMBER_OF_RECALL_REASONS'].isna()] # 0

# Concatenate the 'expanded_reasons' and 'missing_reasons' datasets
reasons = pd.concat([reasons, missing_reasons], ignore_index=True)
reasons.shape # # 18980, 18840, 19051, 14626

# Define the mapping dictionary

recallReason_format = {
    'Poor Behaviour - non-compliance': 'Non-compliance',
    'Poor Behaviour - Further offence/charge': 'Facing further charge',
    'Further Charge': 'Facing further charge',
    'EM - Further offence/charge - detected by ELM': 'Facing further charge',
    'HDC Further Charge': 'Facing further charge',
    'Failed to keep in touch': 'Failed to keep in touch',
    'Out Of Touch': 'Failed to keep in touch',
    'Failed to reside': 'Failed to reside',
    'Fail To Reside': 'Failed to reside',
    'Poor Behaviour - Drugs': 'Drugs/alcohol',
    'Poor Behaviour - alcohol': 'Drugs/alcohol',
    'HDC - Time violation': 'HDC - Time violation',
    'Poor Behaviour - Relationships': 'Poor Behaviour - Relationships',
    'HDC - Inability to monitor': 'HDC - Inability to monitor',
    'Failed home visit': 'Failed home visit',
    'HDC - Failed installation': 'HDC - Failed installation',
    'HDC - Equipment Tamper': 'HDC - Equipment Tamper',
    'Missing': 'Unknown'
}

# Apply the mapping to 'REASON_DESC'
reasons['REASON_DESC'] = reasons['REASON_DESC'].map(recallReason_format).fillna('Other')

#/Compress into one row for each recall/reason combination

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query ="""SELECT DISTINCT * FROM reasons"""

reasons_final = duckdb.sql(query).df()

reasons_final.shape # 18897, 18781, 18977, 14579
