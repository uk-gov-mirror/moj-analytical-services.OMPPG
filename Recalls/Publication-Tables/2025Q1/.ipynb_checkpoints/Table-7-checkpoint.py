""" 
GOAL: PRODUCE TABLE 7 - CONTINUATION FROM TABLE 6 CODE
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Get final UAL data for the last 5 quarters ----------------------------------------------------

ual1 = pd.read_parquet('s3://alpha-omppg/UAL/final_data/ual_final_2024q1.parquet')
ual2 = pd.read_parquet('s3://alpha-omppg/UAL/final_data/ual_final_2024q2.parquet')
ual3 = pd.read_parquet('s3://alpha-omppg/UAL/final_data/ual_final_2024q3.parquet')
ual4 = pd.read_parquet('s3://alpha-omppg/UAL/final_data/ual_final_2024q4.parquet')
ual5 = pd.read_parquet('s3://alpha-omppg/UAL/final_data/ual_final_2025q1.parquet')

# uppercase the headers
for df in [ual1,ual2,ual3,ual4,ual5]:
    df.columns = df.columns.str.upper()

# Create recall end date for each file

max(ual5['LICENCE_REVOKE_DATE'])

for df in [ual1,ual2,ual3,ual4,ual5]:
    df['RECALL_END_DATE'] = max(df['LICENCE_REVOKE_DATE'])
    df['RECALL_END_DATE'] = df['RECALL_END_DATE'].dt.to_period("Q").dt.end_time
    df['RECALL_END_DATE_STR'] = df['RECALL_END_DATE'].dt.strftime('%d %b %Y')
    df['RECALL_END_DATE_STR'] = df['RECALL_END_DATE_STR'].replace({'Jun':'June','Jul':'July','Sep':'Sept'},regex=True)

for df in [ual1,ual2,ual3,ual4,ual5]:
    print(df['RECALL_END_DATE_STR'].unique())
    
# Concatenate all DataFrames in order into one------------------------------------------------------------------

ual = pd.concat( [ual1,ual2,ual3,ual4,ual5], ignore_index=True)
len(ual) # 13393, 13002, 12634,12236, 11900
ual.head()
ual.info()

del ual1,ual2,ual3,ual4,ual5

# Add a recall 'QUARTER' column to each DataFrame-----------------------------------------------------------------
ual['RECALL_END_DATE_STR'].unique()

ual['QUARTER'] = ual['RECALL_END_DATE'].dt.quarter
ual['QUARTER'].unique()

# Create a recalled in and returned by headings

ual['RETURN_BY'] = ual.apply(lambda x: np.where(
    x['QUARTER'] == 4, pd.Timestamp(x['RECALL_END_DATE'].year+1,3,31), 
    np.where(x['QUARTER'] == 3, pd.Timestamp(x['RECALL_END_DATE'].year,12,31),
    np.where(x['QUARTER'] == 2, pd.Timestamp(x['RECALL_END_DATE'].year,9,30), 
             pd.Timestamp(x['RECALL_END_DATE'].year,6,30)))).item(),axis = 1)

ual['RETURN_BY_STR'] = ual['RETURN_BY'].dt.strftime('%d %b %Y')
ual['RETURN_BY_STR'] = ual['RETURN_BY_STR'].replace({'Jun':'June','Jul':'July','Sep':'Sept'},regex=True)

ual['RETURN_BY_STR'].unique()

# ual[['LICENCE_REVOKE_DATE','RECALL_END_DATE','QUARTER',"RETURN_BY_STR"]].head()

ual['RECALLED_IN_NOT_RETURNED_BY'] = ual.apply(lambda x: 'Recalled between 1984 and ' + str(x['RECALL_END_DATE_STR']) + ' not returned by ' + str(x['RETURN_BY_STR']), axis=1)

ual['RECALLED_IN_NOT_RETURNED_BY'].unique()
ual.head()

# Change gender values ----------------------------------------------------------------------

ual['GENDER'].unique()
ual['GENDER'] = ual['GENDER'].replace(gender_mapping)

# Create a SENTENCE column (under 12, over 12, IPP, life----------------------------------------------------------

sentence(ual) # sentece() function is from Shared.py

ual['SENTENCE'].unique()
ual.head()

# Couple of corrections
ual['SUP_BODY'].value_counts(dropna=False)

((ual['SUP_BODY'] == 'a. Probation Trust') & (ual['SENTENCE'] == 'Determinate less than 12 months')).sum() # 0 as expected

ual.loc[(ual['SUP_BODY'] == 'a. Probation Trust') & (ual['SENTENCE'] == 'Determinate less than 12 months'),'SUP_BODY'] = 'c. CRC'

ual.loc[ual['SUP_BODY'] == 'b. PS','SUP_BODY']= 'b. NPS'

ual.loc[ual['SUP_BODY'] == 'b. NPS','SUP_BODY'] = 'National probation'
ual.loc[ual['SUP_BODY'] == 'a. Probation Trust','SUP_BODY'] = 'Probation trust'
# ual.loc[ual['SUP_BODY'] == 'c. CRC','SUP_BODY']= 'Community rehabilitation companies'

ual['SUP_BODY'].unique()

# Define unique values Table 7
rec_1984_not_returned_by = list(ual['RECALLED_IN_NOT_RETURNED_BY'].unique())
rec_1984_not_returned_by

# Calculate summaries for the combined DataFrame
table_7_summary = table_7_func(ual, sex_values, sentence_values)

len(table_7_summary) # 300
table_7_summary.head(20) # each row came from a dictionary in a list

# categorise to order values for publication
table_7_summary['Sex'] = table_7_summary['Sex'].astype(CategoricalDtype(categories=sex_values, ordered=True))
table_7_summary['Sentence type'] = table_7_summary['Sentence type'].astype(CategoricalDtype(categories=sentence_values, ordered=True))
table_7_summary['Supervising body'] = table_7_summary['Supervising body'].astype(CategoricalDtype(categories=supervising_body, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_7_df = table_7_summary.pivot_table(
    index=['Sex', 'Sentence type', 'Supervising body'],
    columns='text',
    values='values',observed=False
).reset_index()

len(table_7_df) # 60

# Order the columns for publication
table_7_df = table_7_df[['Sex', 'Sentence type', 'Supervising body'] + rec_1984_not_returned_by]

table_7_df

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:
    table_7_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_5_Q_7',index=False,header=False)
