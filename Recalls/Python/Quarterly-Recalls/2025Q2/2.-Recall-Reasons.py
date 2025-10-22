""" 
GOAL: PRODUCE QUARTERLY RECALL DATA FOR OMSQ.
By Eric Nyame, 15/04/2024
"""

# Expand dataset to include one row for every reason
reasons = recalls_final.copy()

reasons['REASON_DESC'] = reasons['RECALL_REASON_DESCRIPTIONS'].str.split(',')

reasons = reasons.explode('REASON_DESC')

reasons['REASON_DESC'] = reasons['REASON_DESC'].str.strip()

# Bring cases with no reason recorded
missing_reasons = recalls_final[recalls_final['NUMBER_OF_RECALL_REASONS'].isna()] # 0

# Concatenate the 'expanded_reasons' and 'missing_reasons' datasets
reasons = pd.concat([reasons, missing_reasons], ignore_index=True)
reasons.shape # # 20717, 18980, 18840, 19051, 14626

# Define the mapping dictionary

reasons['REASON_DESC'].value_counts(dropna=False) # check unique values before mapping

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

reasons_final.shape # 20644, 18897, 18781, 18977, 14579

# final table of reasons by quarter

# Extract year and quarter from 'LICENCE_REVOKE_DATE'
reasons_final['YYQ'] = reasons_final['LICENCE_REVOKE_DATE'].dt.to_period('Q').astype(str)

reasons_final.head()
reasons_final.info()

# Create a pivot table
pd.pivot_table(reasons_final, 
               index=['GENDER', 'REASON_DESC'], 
               columns=['YYQ'], aggfunc='size', fill_value=0)

pd.crosstab([reasons_final['GENDER'], reasons_final['REASON_DESC']],reasons_final['YYQ'])
# Print the pivot table

# Save on Amazon to continue

reasons_final = reasons_final.drop(columns=['YYQ'])

reasons_final.to_parquet(f"s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_{year}q{quarter}.parquet", index=False)
