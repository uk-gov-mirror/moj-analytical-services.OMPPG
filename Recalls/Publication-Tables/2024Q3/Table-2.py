""" 
GOAL: PRODUCE RECALL TABLES FOR OMSQ.
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
                      
rec2 = pd.read_sas('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2023q3.sas7bdat',encoding='latin1')
rec3 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2023q4.parquet')
rec4 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2024q1.parquet')
rec5 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2024q2.parquet')
rec1 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2024q3.parquet')

# uppercase the headers
for df in [rec1,rec2,rec3,rec4,rec5]:
    df.columns = df.columns.str.upper()

# Concatenate all DataFrames into one------------------------------------------------------------------

recalls = pd.concat([rec2,rec3,rec4,rec5,rec1], ignore_index=True)
len(recalls) # 41354, 38193,35235
recalls.head()

del rec1,rec2,rec3,rec4,rec5

# Add a recall 'QUARTER' column in the form 'Month to Month year'-------------------------------------------
# this uses a function in Shared.py

recalls['QUARTER'] = recalls['LICENCE_REVOKE_DATE'].dt.to_period('Q') # convert in the form 2022Q2
recalls['QUARTER'] = recalls['QUARTER'].apply(format_quarter) # then apply the function to it to change to 'Month to Month year'

# recalls['QUARTER'].unique()
# recalls.head() # have a look

# Change gender values - uses a mapping from Shared.py-----------------------------------------------------------
recalls['GENDER'].unique()
recalls['GENDER'] = recalls['GENDER'].replace(gender_mapping) # change 'F' to 'Female', 'M' to 'Male'

# Create a SENTENCE column (under 12, over 12, IPP, life)--------------------------------------------------------

sentence(recalls)

recalls['SENTENCE'].unique()

# Create a HDC indentification ------------------------------------------------------------------

recalls['HDC'] = 'Non-HDC'
recalls.loc[recalls['RECALL_TYPE_DESCRIPTION'].str.contains('HDC', case=False),'HDC'] = 'HDC'

# recalls.pivot_table(index=['RECALL_TYPE_DESCRIPTION','HDC'],aggfunc='size').reset_index(name='count').sort_values('HDC')

# create a list of the unique recall['QUARTER'] values ---------------

quarters = list(recalls['QUARTER'].unique()) # values like 'Month to Month Year'
quarters

# Fair idea of unique individuals involved
def check_unique_people(df):
    for quarter in quarters:
        uniques_1 = df[df['QUARTER'] == quarter]
        uniques_2 = uniques_1.drop_duplicates('NOMS_ID',keep='first')
        print(f"{quarter}: missing NOMS ID ={uniques_1['NOMS_ID'].isna().sum()}, recalls = {len(uniques_1)}, unique people = {len(uniques_2)}")

check_unique_people(recalls)  

# Calculate summaries for table 2 - function table_2_func() is in Shared.py

table_2_summary = table_2_func(recalls, sex_values, sentence_values, hdc_values)

len(table_2_summary) # 225
table_2_summary.head(20) # each row came from a dictionary in a list

# Order the values of the columns of the summary table
table_2_summary['Sex'] = table_2_summary['Sex'].astype(CategoricalDtype(categories=sex_values, ordered=True))
table_2_summary['Sentence type'] = table_2_summary['Sentence type'].astype(CategoricalDtype(categories=sentence_values, ordered=True))
table_2_summary['Recall category'] = table_2_summary['Recall category'].astype(CategoricalDtype(categories=hdc_values, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_2_df = table_2_summary.pivot_table(
    index=['Sex', 'Sentence type', 'Recall category'],
    columns='quarter',
    values='values',observed=False
).reset_index()

len(table_2_df) # 45

# Order the columns for publication

table_2_df = table_2_df[['Sex', 'Sentence type', 'Recall category'] + quarters]

table_2_df


# don't use: percentage change ---------------------------------------------------------------- 
#percent_change_words = f'Percentage change between {quarters[0]} and {quarters[-1]}'
#table_2_df[percent_change_words] = (table_2_df[quarters[-1]] - table_2_df[quarters[0]])/ table_2_df[quarters[0]]
#table_2_df[percent_change_words] = np.round(table_2_df[percent_change_words],4)

# don't use: Format the values to have thousand separators ------------------------
#for quarter in quarters:
    #table_2_df[quarter] = table_2_df[quarter].apply(lambda x: f"{int(x):,}" if not pd.isna(x) else x)

# Write pivot table to excel document
output_work_book = "../Prison_Recall_Template.xlsx"

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:
    table_2_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_5_Q_2',index=False, header = False)

