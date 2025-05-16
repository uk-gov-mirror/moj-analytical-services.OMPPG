""" 
GOAL: PRODUCE TABLE 10 - CONTINUATION FROM TABLE 9 CODE.
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Get last final recall data for the last 5 quarters----------------------------------------------------------------------

years = list(range(2015,2025))
quarters =[f"q{i}" for i in range(1,5)]

#---------------------------------- Import data

# some of the files are SAS and others are Parquet, so try to import each

def conCatReasonDatasets(years,quarters):
    
    reasons = pd.DataFrame() # start with an empty dataframe

    for year in years:
        
        for quarter in quarters:

            quart_reas = pd.DataFrame() # Reset appending file

            try: # Try to import SAS file first
                quart_reas = pd.read_sas(f"s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_{year}{quarter}.sas7bdat", encoding='latin1')
                quart_reas.columns = quart_reas.columns.str.upper()
                quart_reas = quart_reas.drop(columns =['DOS','RTC_DATE','DOB','REPORT_RECD_BY_UNIT_TARGET','PB_DECISION_AFTER_BREACH_ACTUAL'])
                                             
                print(f"Loaded SAS file for {year}{quarter}")

            except Exception as e:# If no SAS file, import parquet version

                print(f"Failed to load SAS file for {year}{quarter}, error: {e}")

                try:
                    quart_reas = pd.read_parquet(f"s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_{year}{quarter}.parquet")
                    quart_reas.columns = quart_reas.columns.str.upper()
                    quart_reas = quart_reas.drop(columns =['DOS','RTC_DATE','DOB','REPORT_RECD_BY_UNIT_TARGET','PB_DECISION_AFTER_BREACH_ACTUAL'])
                    print(f"Loaded Parquet file for {year}{quarter}")

                except Exception as e:
                    print(f"Failed to load parquet file for {year}{quarter}, error: {e}")

            reasons = pd.concat([reasons,quart_reas],axis=0)

    return reasons

reasons_0 = conCatReasonDatasets(years,quarters)
reasons = reasons_0.copy()

"""
len(reasons) # 473321
reasons['LICENCE_REVOKE_DATE'].dt.year.value_counts(dropna=False).sort_index()
"""

# placeholder for summaries
reasons['COMMON'] = 1

# Add a recall 'YEAR' column in the form 'Month to Month year'-------------------------------------------

reasons['YEAR'] = reasons['LICENCE_REVOKE_DATE'].dt.year

"""
reasons['LICENCE_REVOKE_DATE'].dt.year.value_counts()
reasons.head()
reasons.tail()

"""
# Some corrections
"""
reasons.pivot_table(index=['SENTENCETYPE','CUSTODYTYPE'],columns='COMMON',aggfunc='size',fill_value=0)
"""

reasons.loc[reasons['CUSTODYTYPE'] == 'IPP','SENTENCETYPE'] = 'IPP'
reasons.loc[reasons['CUSTODYTYPE'] == 'Life','SENTENCETYPE'] = 'Life sentence'
reasons.loc[reasons['SENTENCETYPE'] == 'Other','SENTENCETYPE'] = 'Determinate 12 months or more'
reasons.loc[reasons['SENTENCETYPE'] == 'Under 12 months','SENTENCETYPE'] = 'Determinate less than 12 months'

reasons['SENTENCE'] = reasons['SENTENCETYPE']
reasons['SENTENCE'].unique()
# Change gender values - uses a mapping from Shared.py-----------------------------------------------------------
reasons['GENDER'].unique()
reasons['GENDER'] = reasons['GENDER'].replace(gender_mapping) # change 'F' to 'Female', 'M' to 'Male'

# fix reason descriptions for some legacy recall reasons

reasons[reasons['LICENCE_REVOKE_DATE'] > pd.Timestamp(2018,6,30)]['REASON_DESC'].value_counts(dropna=False)

legacyRecallReason_format = {
    'b. Poor Behaviour - non-compliance[*]': 'Non-compliance',
    'a. Further Charge[*]': 'Facing further charge',
    'c. Failed to keep in touch[*]': 'Failed to keep in touch',
    'd. Failed to reside[*]': 'Failed to reside',
    'e. Poor Behaviour - Drugs/alcohol[*]': 'Drugs/alcohol',
    'a. HDC - Time violation': 'HDC - Time violation',
    'f. Poor Behaviour - Relationships': 'Poor Behaviour - Relationships',
    'b. HDC - Inability to monitor': 'HDC - Inability to monitor',
    'c. HDC - Failed installation': 'HDC - Failed installation',
    'd. HDC - Equipment Tamper': 'HDC - Equipment Tamper',
    'f. Other[*]': 'Other',
    'g. Other[*]': 'Other',
    'g. Unknown[*]':'Unknown',
    'h. Unknown[*]':'Unknown',
    'Unknown': 'Unknown'
}

reasons['REASON_DESC_2'] = reasons['REASON_DESC'].replace(legacyRecallReason_format)

"""
reasons['REASON_DESC_2'].value_counts(dropna=False)

reasons[reasons['REASON_DESC_2'] == 'Other']['RECALL_REASON_DESCRIPTIONS'].value_counts(dropna=False)

reasons[reasons['REASON_DESC_2'] == 'Unknown']['RECALL_REASON_DESCRIPTIONS'].value_counts(dropna=False) # NaNs
"""

# Calculate summaries for table 2 - function table_2_func() is in Shared.py

reasons['REASON_DESC'] = reasons['REASON_DESC_2'].copy()

table_10_summary = table_10_func(reasons,recalls, sex_values, sentence_values, reason_desc_vals)

"""
len(table_10_summary) # 910
# table_10_summary.head(20) # each row came from a dictionary in a list
"""

# Order the values of the columns of the summary table
table_10_summary['Sex'] = table_10_summary['Sex'].astype(CategoricalDtype(categories=sex_values, ordered=True))
table_10_summary['Sentence type'] = table_10_summary['Sentence type'].astype(CategoricalDtype(categories=sentence_values, ordered=True))
table_10_summary['Recall reason'] = table_10_summary['Recall reason'].astype(CategoricalDtype(categories=reason_desc_vals, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_10_df = table_10_summary.pivot_table(
    index=['Sex', 'Sentence type', 'Recall reason'],
    columns='year',
    values='values',observed=False
).reset_index()

len(table_10_df) # 91

# Order the columns for publication

table_10_df = table_10_df[['Sex', 'Sentence type', 'Recall reason'] + years]

table_10_df

# Write pivot table to excel document

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:
    table_10_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_5_Q_10',index=False,header=False)