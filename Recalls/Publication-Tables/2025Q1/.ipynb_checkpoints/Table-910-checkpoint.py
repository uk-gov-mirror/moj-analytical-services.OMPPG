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


reas1 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2024q1.parquet')
reas2 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2024q2.parquet')
reas3 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2024q3.parquet')
reas4 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2024q4.parquet')
reas5 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2025q1.parquet')

# uppercase the headers
for df in [reas1,reas2,reas3,reas4,reas5]:
    df.columns = df.columns.str.upper()

# Concatenate all DataFrames into one------------------------------------------------------------------

reasons = pd.concat([reas1,reas2,reas3,reas4,reas5], ignore_index=True)
len(reasons) # 80,236,74661,68905
reasons.head()
reasons.info()

del reas1,reas2,reas3,reas4,reas5

# Some corrections
reasons['SENTENCETYPE'].value_counts()

reasons.loc[reasons['CUSTODYTYPE'] == 'IPP','SENTENCETYPE'] = 'IPP'
reasons.loc[reasons['CUSTODYTYPE'] == 'Life','SENTENCETYPE'] = 'Life sentence'
reasons.loc[reasons['SENTENCETYPE'] == 'Other','SENTENCETYPE'] = 'Determinate 12 months or more'
reasons.loc[reasons['SENTENCETYPE'] == 'Under 12 months','SENTENCETYPE'] = 'Determinate less than 12 months'

reasons['SENTENCE'] = reasons['SENTENCETYPE']

reasons['SENTENCE'].unique()

""" Sort out ORA status of a couple of hdc recall types

trbHdcMask = ['HDC recall - 255 1 (a) breach of curfew conditions','HDC recall - 255 1 (b) inability to monitor']
    
reasons['RECALL_TYPE_DESCRIPTION'].unique()

addSentenceMask = (
    (reasons['LICENCE_REVOKE_DATE'].dt.year >= 2025) & 
    (reasons['RECALL_TYPE_DESCRIPTION'].isin(trbHdcMask))
)

sum(addSentenceMask) # 358

oraMask2 = addSentenceMask & (reasons['PART_TOTAL_IN_DAYS'] < 365)
sum(oraMask2) # 91

reasons[addSentenceMask]['PART_TOTAL_IN_DAYS'].value_counts(dropna=False).sort_index()

"""

reasons.loc[oraMask2,'SENTENCE'] = 'Determinate less than 12 months'

# Add a recall 'QUARTER' column in the form 'Month to Month year'-------------------------------------------
# this uses a function in Shared.py

reasons['QUARTER'] = reasons['LICENCE_REVOKE_DATE'].dt.to_period('Q') # convert in the form 2022Q2
reasons['QUARTER'] = reasons['QUARTER'].apply(format_quarter) # then apply the function to it to change to 'Month to Month year'
reasons['QUARTER'].unique()
reasons.head() # have a look

# Change gender values - uses a mapping from Shared.py-----------------------------------------------------------
reasons['GENDER'].unique()
reasons['GENDER'] = reasons['GENDER'].replace(gender_mapping) # change 'F' to 'Female', 'M' to 'Male'

# reasons[reasons['REASON_DESC'] == 'Other']['RECALL_REASON_DESCRIPTIONS'].value_counts(dropna=False)

# create a list of the unique recall['QUARTER'] values ---------------

quarters = list(reasons['QUARTER'].unique()) # values like 'Month to Month Year'
quarters

# Calculate summaries for table 2 - function table_2_func() is in Shared.py

table_10_summary = table_10_func(reasons,recalls, sex_values, sentence_values, reason_desc_vals)

len(table_10_summary) # 420
# table_10_summary.head(20) # each row came from a dictionary in a list

# Order the values of the columns of the summary table
table_10_summary['Sex'] = table_10_summary['Sex'].astype(CategoricalDtype(categories=sex_values, ordered=True))
table_10_summary['Sentence type'] = table_10_summary['Sentence type'].astype(CategoricalDtype(categories=sentence_values, ordered=True))
table_10_summary['Recall reason'] = table_10_summary['Recall reason'].astype(CategoricalDtype(categories=reason_desc_vals, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_10_df = table_10_summary.pivot_table(
    index=['Sex', 'Sentence type', 'Recall reason'],
    columns='quarter',
    values='values',observed=False
).reset_index()

len(table_10_df) # 84

# Order the columns for publication

table_10_df = table_10_df[['Sex', 'Sentence type', 'Recall reason'] + quarters]

table_10_df.to_excel("table_10.xlsx",index=False)


# Write pivot table to excel document

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:
    table_10_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_5_Q_10',index=False,header=False)