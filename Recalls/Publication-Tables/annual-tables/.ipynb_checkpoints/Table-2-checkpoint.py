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
#----------------------------------Set Global Parameters
years = list(range(2015,2025))
quarters =[f"q{i}" for i in range(1,5)]

#---------------------------------- Import data

# some of the files are SAS and others are Parquet, so try to import each

def conCatRecallDatasets(years,quarters):
    
    recalls = pd.DataFrame() # start with an empty dataframe

    for year in years:
        
        for quarter in quarters:

            quart_recs = pd.DataFrame() # Reset appending file

            try: # Try to import SAS file first
                quart_recs = pd.read_sas(f"s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_{year}{quarter}.sas7bdat", encoding='latin1')
                quart_recs.columns = quart_recs.columns.str.upper()
                print(f"Loaded SAS file for {year}{quarter}")

            except Exception as e:# If no SAS file, import parquet version

                print(f"Failed to load SAS file for {year}{quarter}, error: {e}")

                try:
                    quart_recs = pd.read_parquet(f"s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_{year}{quarter}.parquet")
                    quart_recs.columns = quart_recs.columns.str.upper()
                    print(f"Loaded Parquet file for {year}{quarter}")

                except Exception as e:
                    print(f"Failed to load parquet file for {year}{quarter}, error: {e}")

            recalls = pd.concat([recalls,quart_recs],axis=0)

    return recalls

recalls_0 = conCatRecallDatasets(years,quarters)
recalls = recalls_0.copy()
len(recalls) # 229751

recalls = recalls.replace("–","-",regex=True) # replace long dashes with normal dashes

"""
recalls['LICENCE_REVOKE_DATE'].dt.year.value_counts(dropna=False).sort_index()
"""

# placeholder for summaries
recalls['COMMON'] = 1

# Add a recall 'YEAR' column in the form 'Month to Month year'-------------------------------------------

recalls['YEAR'] = recalls['LICENCE_REVOKE_DATE'].dt.year

"""
recalls.head()
recalls.tail()

"""

# Change gender values - uses a mapping from Shared.py-----------------------------------------------------------
recalls['GENDER'].unique()
recalls['GENDER'] = recalls['GENDER'].replace(gender_mapping) # change 'F' to 'Female', 'M' to 'Male'

# Create a SENTENCE column (under 12, over 12, IPP, life)--------------------------------------------------------

sentence(recalls)

"""
recalls['SENTENCE'].unique()

recalls.pivot_table(index=['CUSTODYTYPE','SENTENCETYPE','SENTENCE'],
                    columns='COMMON',
                    aggfunc='size',observed=False,fill_value=0)
"""

# Create a HDC indentification ------------------------------------------------------------------

"""
recalls['RECALL_TYPE_DESCRIPTION'].value_counts(dropna=False)
"""
recalls['HDC'] = 'Non-HDC'
recalls.loc[recalls['RECALL_TYPE_DESCRIPTION'].str.contains('HDC', case=False),'HDC'] = 'HDC'

""" 
recalls.pivot_table(index=['RECALL_TYPE_DESCRIPTION','HDC'],
                    aggfunc='size').reset_index(name='count').sort_values('HDC')
"""

# create a list of year values ---------------

years = list(recalls['YEAR'].unique()) 
years

"""
# Fair idea of unique individuals involved
def check_unique_people(df):
    for year in years:
        uniques_1 = df[df['YEAR'] == year]
        uniques_2 = uniques_1.drop_duplicates('NOMS_ID',keep='first')
        print(f"{year}: missing NOMS ID ={uniques_1['NOMS_ID'].isna().sum()}, recalls = {len(uniques_1)}, unique people = {len(uniques_2)}")

check_unique_people(recalls)  
"""

# Calculate summaries for table 2 - function table_2_func() is in Shared.py

table_2_summary = table_2_func(recalls, sex_values, sentence_values, hdc_values)

len(table_2_summary) # 405
table_2_summary.head(20) # each row came from a dictionary in a list

# Order the values of the columns of the summary table
table_2_summary['Sex'] = table_2_summary['Sex'].astype(CategoricalDtype(categories=sex_values, ordered=True))
table_2_summary['Sentence type'] = table_2_summary['Sentence type'].astype(CategoricalDtype(categories=sentence_values, ordered=True))
table_2_summary['Recall category'] = table_2_summary['Recall category'].astype(CategoricalDtype(categories=hdc_values, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_2_df = table_2_summary.pivot_table(
    index=['Sex', 'Sentence type', 'Recall category'],
    columns='year',
    values='values',observed=False
).reset_index()

"""
len(table_2_df) # 45
"""
# Order the columns for publication

table_2_df = table_2_df[['Sex', 'Sentence type', 'Recall category'] + years]

"""
table_2_df
"""

# Write pivot table to excel document
output_work_book = "z-annualRecallTemplate.xlsx"

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:
    table_2_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_5_Q_2',index=False, header = False)

